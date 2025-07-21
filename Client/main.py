import pygame
import math
import sys
import time
from CarGameClient import CarGameClient
import random
from Speedometer import Speedometer
import math
from MainMenu import MainMenu


# Initialize Pygame
pygame.init()

# Constants
INITIAL_SCREEN_WIDTH = 800
INITIAL_SCREEN_HEIGHT = 600
FPS = 60

# CAR TUNING - Easy to modify these values
MAX_SPEED = 65          # Maximum speed of the car in m/s
ACCELERATION = 0.3     # How fast the car accelerates
TURN_SPEED = 5         # How responsive steering is (normal driving)
DRIFT_TURN_SPEED = 3   # How responsive steering is (while drifting)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

class GameWindow:
    def __init__(self):
        self.width = INITIAL_SCREEN_WIDTH
        self.height = INITIAL_SCREEN_HEIGHT
        
    def update_size(self, new_width, new_height):
        self.width = new_width
        self.height = new_height

class Camera:
    def __init__(self, window):
        self.x = 0
        self.y = 0
        self.window = window

    def update(self, car):
        self.x = car.x - self.window.width // 2
        self.y = car.y - self.window.height // 2

    def apply(self, x, y):
        return int(x - self.x), int(y - self.y)


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

    def update_state(self, x, y, angle, car_color, drifting=False, visible=True):
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
        name_surface = self.font.render(self.name, True, BLACK)
        name_rect = name_surface.get_rect(midbottom=(screen_x, screen_y - self.height // 2 - 5))
        screen.blit(name_surface, name_rect)


class Car:
    def __init__(self, x, y, car_color):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.max_speed = MAX_SPEED
        self.acceleration = ACCELERATION
        self.friction = 0.1
        self.turn_speed = TURN_SPEED
        self.drift_turn_speed = DRIFT_TURN_SPEED
        self.is_drifting = False
        self.width = 30
        self.height = 15
        self.last_skid_time = 0
        self.skid_interval = 0.05
        self.car_color = car_color

    def get_speed(self):
        """Returns the Car's current speed in m/s"""
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)
    
    def get_speed_kmh(self):
        """Returns the Car's current speed in km/h"""
        return self.get_speed() * 3.6

    def draw(self, screen, camera):
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        car_color = RED if self.is_drifting else self.car_color
        pygame.draw.rect(car_surface, car_color, (0, 0, self.width, self.height))
        pygame.draw.rect(car_surface, RED, (self.width - 5, 0, 5, self.height))
        rotated_car = pygame.transform.rotate(car_surface, -self.angle)
        screen_x, screen_y = camera.apply(self.x, self.y)
        car_rect = rotated_car.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_car, car_rect)

    def update(self, keys, skid_marks):
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        self.is_drifting = keys[pygame.K_SPACE] and current_speed > 1

        if keys[pygame.K_w]:
            self.velocity_x += self.acceleration * math.cos(math.radians(self.angle))
            self.velocity_y += self.acceleration * math.sin(math.radians(self.angle))
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


def draw_road_markings(screen, camera, window):
    """Draw infinite road markings that adapt to window size"""
    # Calculate visible area based on camera position and current window size
    start_x = int(camera.x // 100) * 100
    end_x = start_x + window.width + 200
    
    for i in range(start_x, end_x, 100):
        # Horizontal road marking
        line_start_x, line_start_y = camera.apply(i, 0)
        line_end_x, line_end_y = camera.apply(i + 50, 0)
        
        # Only draw if visible on screen
        if -50 <= line_start_x <= window.width + 50:
            pygame.draw.line(screen, GRAY, (line_start_x, line_start_y), (line_end_x, line_end_y), 5)
    
    # Draw vertical road markings too for better orientation
    start_y = int(camera.y // 100) * 100
    end_y = start_y + window.height + 200
    
    for i in range(start_y, end_y, 100):
        # Vertical road marking
        line_start_x, line_start_y = camera.apply(0, i)
        line_end_x, line_end_y = camera.apply(0, i + 50)
        
        # Only draw if visible on screen
        if -50 <= line_start_y <= window.height + 50:
            pygame.draw.line(screen, GRAY, (line_start_x, line_start_y), (line_end_x, line_end_y), 5)


def draw_ui(screen, car, window):
    """Draw UI elements that adapt to window size"""
    # Create fonts
    font = pygame.font.Font(None, 36)
    controls_font = pygame.font.Font(None, 24)
    
    # Display speed (UI elements stay on screen)
    speed_text = font.render(f"Speed: {car.get_speed():.1f} m/s ({car.get_speed_kmh():.0f} km/h)", True, BLACK)
    screen.blit(speed_text, (10, 10))
    
    # Display drift status
    if car.is_drifting:
        drift_text = font.render("DRIFTING!", True, RED)
        screen.blit(drift_text, (10, 50))
    
    # Display car position for reference
    pos_text = font.render(f"Position: ({car.x:.0f}, {car.y:.0f})", True, BLACK)
    screen.blit(pos_text, (10, 90))
    
    # Display window size in top right
    size_text = controls_font.render(f"Window: {window.width}x{window.height}", True, BLACK)
    size_rect = size_text.get_rect(topright=(window.width - 10, 10))
    screen.blit(size_text, size_rect)
    
    # Display controls
    controls = [
        "Controls:",
        "W - Accelerate",
        "S - Brake/Reverse",
        "A - Turn Left",
        "D - Turn Right",
        "SPACE - Handbrake/Drift",
        "C - Change Car Color",
        "ESC - Exit"
    ]
    
    for i, text in enumerate(controls):
        control_text = controls_font.render(text, True, BLACK)
        screen.blit(control_text, (10, 130 + i * 25))


def main():
    # Create the game window manager
    game_window = GameWindow()
    
    # Create the screen
    screen = pygame.display.set_mode((game_window.width, game_window.height), pygame.RESIZABLE)
    pygame.display.set_caption("Top-Down Car Game - Resizable")
    clock = pygame.time.Clock()

    menu = MainMenu(screen)
    config = menu.run()
    
    # Create car at world position (0, 0)
    car = Car(0, 0, config["car_color"])

    # Create a Speedometer
    speedometer = Speedometer(x=game_window.width - 100, y=game_window.height - 100, radius=80, max_speed=car.max_speed, unit="km/h", show_digital_speedometer=False)
    
    # Create camera with window reference
    camera = Camera(game_window)
    
    # List to store skid marks
    skid_marks = []
    
    # NETWORK SETUP
    client = CarGameClient(config["server"], config["port"], config["player_name"], config["car_color"])
    client.connect()

    remote_players = {}

    def on_player_update(name, data):
        if name not in remote_players:
            remote_players[name] = MultiplayerCar(data["x"], data["y"], name, data["car_color"])

        remote_players[name].update_state(
            x=data["x"],
            y=data["y"],
            angle=data["angle"],
            drifting=data.get("is_drifting", False),
            visible=True,
            car_color=data["car_color"]
        )

    def on_player_disconnect(name):
        remote_players[name].update_state(
            x=0,
            y=0,
            angle=0,
            drifting=False,
            visible=False,
            car_color=None
        )
        print(f'[INFO] {name} disconnected, making invisible')

    client.on_player_update = on_player_update
    client.on_player_disconnect = on_player_disconnect

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                game_window.update_size(event.w, event.h)
                screen = pygame.display.set_mode((game_window.width, game_window.height), pygame.RESIZABLE)
                speedometer.x = game_window.width - 100
                speedometer.y = game_window.height - 100
                print(f"Window resized to: {game_window.width}x{game_window.height}")

        # Get pressed keys
        keys = pygame.key.get_pressed()
        
        # Update car
        car.update(keys, skid_marks)
        speedometer.update_speed(car.get_speed_kmh())
        speedometer.update()

        # Send local car state to server
        client.send_player_state(car.x, car.y, car.angle, car.is_drifting, car.car_color)
        
        # Update camera to follow car
        camera.update(car)
        
        # Remove expired skid marks
        skid_marks = [skid for skid in skid_marks if not skid.is_expired()]
        
        # Clear screen
        screen.fill(WHITE)
        
        # Draw infinite road markings
        draw_road_markings(screen, camera, game_window)
        
        # Draw skid marks (behind the car)
        for skid in skid_marks:
            skid.draw(screen, camera)
        
        # Draw car
        car.draw(screen, camera)
        speedometer.draw(screen)

        # Draw all remote multiplayer cars
        for mp_car in remote_players.values():
            if mp_car.visible == True:
                mp_car.draw(screen, camera)
        
        # Draw UI elements
        draw_ui(screen, car, game_window)
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    # Quit
    client.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()