import time
import pygame
import math
import random

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

class SkidMark:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.creation_time = time.time()
        self.lifetime = 3.0
        self.width = 3
        self.length = 8

    def is_expired(self):
        return time.time() - self.creation_time > self.lifetime

    def get_alpha(self):
        elapsed = time.time() - self.creation_time
        fade_ratio = 1.0 - (elapsed / self.lifetime)
        return max(0, min(255, int(255 * fade_ratio)))

    def draw(self, screen, camera):
        alpha = self.get_alpha()
        if alpha > 0:
            screen_x, screen_y = camera.apply(self.x, self.y)

            skid_surface = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
            skid_color = (*BLACK, alpha)
            pygame.draw.rect(skid_surface, skid_color, (0, 0, self.length, self.width))

            rotated_skid = pygame.transform.rotate(skid_surface, -self.angle)
            skid_rect = rotated_skid.get_rect(center=(screen_x, screen_y))

            screen.blit(rotated_skid, skid_rect)

class MultiplayerCar:
    """A car controlled externally (e.g., via network) for multiplayer visualization."""

    def __init__(self, x, y, name, car_color):
        """
        Initialize a multiplayer car.

        :param x: Initial x-position in world coordinates.
        :param y: Initial y-position in world coordinates.
        :param name: String containing the player's name to render above the car.
        :param car_color: A List containing three integers between 0-255
        """
        self.x = x
        self.y = y
        self.angle = 0
        self.car_color = car_color
        self.name = name
        self.is_drifting = False
        self.width = 30
        self.height = 15
        self.font = pygame.font.Font(None, 24)
        self.visible = True
        self.points = 0

    def update_state(self, x, y, angle, car_color, drifting=False, visible=True, points=0):
        """
        Update the car's position and rotation from external state.

        :param x: New x-position.
        :param y: New y-position.
        :param angle: New angle (in degrees).
        :param drifting: Whether the car is drifting.
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.is_drifting = drifting
        self.visible = visible
        self.car_color = car_color
        self.points = points


    def draw(self, screen, camera):
        """
        Draw the car and the player's name above it.

        :param screen: Pygame screen surface.
        :param camera: Camera object for applying world-to-screen transformation.
        """
        # Draw car
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        body_color = RED if self.is_drifting else self.car_color
        pygame.draw.rect(car_surface, body_color, (0, 0, self.width, self.height))
        pygame.draw.rect(car_surface, RED, (self.width - 5, 0, 5, self.height))

        rotated_car = pygame.transform.rotate(car_surface, -self.angle)
        screen_x, screen_y = camera.apply(self.x, self.y)
        car_rect = rotated_car.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_car, car_rect)

        # Draw player name above car
        name_surface = self.font.render(f'{self.name} ({self.points:.0f} pts)', True, BLACK)
        name_rect = name_surface.get_rect(midbottom=(screen_x, screen_y - self.height // 2 - 5))
        screen.blit(name_surface, name_rect)

class Car:
    def __init__(self, x, y, car_color, max_speed: int, acceleration: float, turn_speed: float, drift_turn_speed: float, max_nitro: int):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.friction = 0.1
        self.turn_speed = turn_speed
        self.drift_turn_speed = drift_turn_speed
        self.is_drifting = False
        self.width = 30
        self.height = 15
        self.last_skid_time = 0
        self.skid_interval = 0.05
        self.car_color = car_color
        self.current_nitro = max_nitro
        self.nitro_active = False
        self.nitro_acceleration_boost = 0.3  # zusätzliche Beschleunigung bei Nitro
        self.nitro_usage_rate = 20.0  # ml pro Sekunde
        
        # Flammen-Parameter für Nitro-Effekt
        self.flame_particles = []
        self.flame_spawn_timer = 0

    def get_speed(self):
        """Returns the Car's current speed in m/s"""
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)
    
    def get_speed_kmh(self):
        """Returns the Car's current speed in km/h"""
        return self.get_speed() * 3.6

    def handle_nitro(self, keys, dt):
        """
        Handle nitro activation based on key input.

        :param keys: Pressed key states
        :param dt: Delta time in seconds (for frame-rate-independent consumption)
        """
        using_nitro = keys[pygame.K_LSHIFT] and self.current_nitro > 0
        self.nitro_active = using_nitro

        if using_nitro:
            self.current_nitro -= self.nitro_usage_rate * dt
            self.current_nitro = max(0, self.current_nitro)
            
            # Flammen-Partikel spawnen während Nitro aktiv ist
            self.spawn_flame_particles(dt)
        
        # Flammen-Partikel aktualisieren (auch wenn Nitro nicht aktiv, damit sie auslaufen)
        self.update_flame_particles(dt)

    def spawn_flame_particles(self, dt):
        """Spawnt Flammen-Partikel am Heck des Autos während Nitro aktiv ist"""
        self.flame_spawn_timer += dt
        
        # Flammen alle 0.02 Sekunden spawnen für flüssigen Effekt
        if self.flame_spawn_timer >= 0.02:
            # Position am Heck des Autos berechnen
            rear_offset = -self.width // 2 - 5  # Etwas hinter dem Auto
            rear_x = self.x + rear_offset * math.cos(math.radians(self.angle))
            rear_y = self.y + rear_offset * math.sin(math.radians(self.angle))
            
            # Mehrere Flammen-Partikel für besseren Effekt
            for i in range(2):
                # Leichte Variation in der Position
                offset_y = (i - 0.5) * 8
                flame_x = rear_x + offset_y * math.cos(math.radians(self.angle + 90))
                flame_y = rear_y + offset_y * math.sin(math.radians(self.angle + 90))
                
                # Flammen-Partikel erstellen
                particle = {
                    'x': flame_x,
                    'y': flame_y,
                    'size': random.uniform(3, 8),
                    'life': random.uniform(0.1, 0.3),  # Kurze Lebensdauer
                    'max_life': random.uniform(0.1, 0.3),
                    'velocity_x': random.uniform(-10, 10),
                    'velocity_y': random.uniform(-10, 10)
                }
                self.flame_particles.append(particle)
            
            self.flame_spawn_timer = 0

    def update_flame_particles(self, dt):
        """Aktualisiert alle Flammen-Partikel"""
        for particle in self.flame_particles[:]:  # Kopie der Liste für sicheres Entfernen
            particle['life'] -= dt
            particle['x'] += particle['velocity_x'] * dt
            particle['y'] += particle['velocity_y'] * dt
            
            # Partikel entfernen wenn Lebensdauer abgelaufen
            if particle['life'] <= 0:
                self.flame_particles.remove(particle)

    def draw_flame_particles(self, screen, camera):
        """Zeichnet die Flammen-Partikel"""
        for particle in self.flame_particles:
            screen_x, screen_y = camera.apply(particle['x'], particle['y'])
            
            # Farbe basierend auf Lebensdauer (von gelb/orange zu rot)
            life_ratio = particle['life'] / particle['max_life']
            if life_ratio > 0.7:
                color = (255, 255, 100)  # Gelb
            elif life_ratio > 0.4:
                color = (255, 150, 0)    # Orange
            else:
                color = (255, 50, 0)     # Rot
            
            # Größe basierend auf Lebensdauer
            current_size = int(particle['size'] * life_ratio)
            if current_size > 0:
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), current_size)

    def draw(self, screen, camera):
        # Zuerst Flammen zeichnen (damit sie hinter dem Auto erscheinen)
        self.draw_flame_particles(screen, camera)
        
        # Dann das Auto zeichnen
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, self.car_color, (0, 0, self.width, self.height))
        pygame.draw.rect(car_surface, RED, (self.width - 5, 0, 5, self.height))
        rotated_car = pygame.transform.rotate(car_surface, -self.angle)
        screen_x, screen_y = camera.apply(self.x, self.y)
        car_rect = rotated_car.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_car, car_rect)

    def update(self, keys, skid_marks, dt):
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        self.handle_nitro(keys, dt)
        self.is_drifting = keys[pygame.K_SPACE] and current_speed > 1

        if keys[pygame.K_w]:
            accel = self.acceleration + (self.nitro_acceleration_boost if self.nitro_active else 0)
            self.velocity_x += accel * math.cos(math.radians(self.angle))
            self.velocity_y += accel * math.sin(math.radians(self.angle))
        elif keys[pygame.K_s]:
            self.velocity_x -= self.acceleration * 0.5 * math.cos(math.radians(self.angle))
            self.velocity_y -= self.acceleration * 0.5 * math.sin(math.radians(self.angle))

        if current_speed > 0.1:
            turn_speed = self.drift_turn_speed if self.is_drifting else self.turn_speed
            if keys[pygame.K_a]:
                self.angle -= turn_speed
            elif keys[pygame.K_d]:
                self.angle += turn_speed

        if self.is_drifting:
            self.velocity_x *= 0.96
            self.velocity_y *= 0.96
        else:
            forward_x = math.cos(math.radians(self.angle))
            forward_y = math.sin(math.radians(self.angle))

            forward_velocity = self.velocity_x * forward_x + self.velocity_y * forward_y
            sideways_velocity_x = self.velocity_x - forward_velocity * forward_x
            sideways_velocity_y = self.velocity_y - forward_velocity * forward_y

            sideways_velocity_x *= 0.3
            sideways_velocity_y *= 0.3
            forward_velocity *= 0.98

            self.velocity_x = forward_velocity * forward_x + sideways_velocity_x
            self.velocity_y = forward_velocity * forward_y + sideways_velocity_y

            current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
            if current_speed > self.max_speed:
                self.velocity_x = (self.velocity_x / current_speed) * self.max_speed
                self.velocity_y = (self.velocity_y / current_speed) * self.max_speed

        if self.is_drifting:
            current_time = time.time()
            if current_time - self.last_skid_time > self.skid_interval:
                rear_offset = -self.width // 3
                rear_x = self.x + rear_offset * math.cos(math.radians(self.angle))
                rear_y = self.y + rear_offset * math.sin(math.radians(self.angle))

                tire_offset = self.height // 3
                left_x = rear_x + tire_offset * math.cos(math.radians(self.angle + 90))
                left_y = rear_y + tire_offset * math.sin(math.radians(self.angle + 90))
                right_x = rear_x + tire_offset * math.cos(math.radians(self.angle - 90))
                right_y = rear_y + tire_offset * math.sin(math.radians(self.angle - 90))

                skid_marks.append(SkidMark(left_x, left_y, self.angle))
                skid_marks.append(SkidMark(right_x, right_y, self.angle))
                self.last_skid_time = current_time

        if keys[pygame.K_c]:
            self.car_color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

        self.x += self.velocity_x
        self.y += self.velocity_y
