import pygame
import sys
from CarGameClient import CarGameClient
from ctkMainMenu import MainMenu
import signal
import os
from tkinter import messagebox

# Game Objects
from Speedometers import Speedometer, NitroGauge
from GameObjects import Car, MultiplayerCar

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
DRIFT_TURN_SPEED = 2.5   # How responsive steering is (while drifting)
MAX_NITRO = 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

points = 0
received_highspeed_bonus = False

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

    # Display Points
    points_text = font.render(f"Points: {points:.0f}", True, BLACK)
    screen.blit(points_text, (10, 0))
    
    # Display speed (UI elements stay on screen)
    speed_text = font.render(f"Speed: {car.get_speed():.1f} m/s ({car.get_speed_kmh():.0f} km/h)", True, BLACK)
    screen.blit(speed_text, (10, 30))
    
    # Display drift status
    if car.is_drifting:
        drift_text = font.render("DRIFTING!", True, RED)
        screen.blit(drift_text, (10, 60))
    
    # Display car position for reference
    pos_text = font.render(f"Position: ({car.x:.0f}, {car.y:.0f})", True, BLACK)
    screen.blit(pos_text, (10, 100))
    
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
        "SHIFT - Hold for Nitro",
        "C - Change Car Color",
        "ESC - Exit"
    ]
    
    for i, text in enumerate(controls):
        control_text = controls_font.render(text, True, BLACK)
        screen.blit(control_text, (10, 130 + i * 25))

def calculate_points(car: Car):
    global received_highspeed_bonus
    global points
    if car.get_speed_kmh() > 50: # This is a Bonus for high speed
        if received_highspeed_bonus == False:
            received_highspeed_bonus = True
            points = points + 500
    else:
        if received_highspeed_bonus == True: received_highspeed_bonus = False # Reset

    if car.nitro_active == True:
        points = points + 2
    
    if car.is_drifting == True:
        points = points + car.get_speed_kmh() / 10

def close():
    os.kill(os.getpid(), signal.SIGTERM) # This is the last line that gets executed.

def network_error_close(error_description: str):
    messagebox.showerror(
        'Connection Lost!',
        f'The connection to the server has been lost. Please try reconnecting.\n\n({error_description})'
    )
    close()


def main():
    menu = MainMenu()
    config = menu.run()
    # Create the game window manager
    game_window = GameWindow()
    
    # Create the screen
    screen = pygame.display.set_mode((game_window.width, game_window.height), pygame.RESIZABLE)
    pygame.display.set_caption("Top-Down Car Game - Resizable")
    clock = pygame.time.Clock()
    
    if config["fullscreen"] == 1: # Fullscreen Support
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        game_window.update_size(info.current_w, info.current_h)

    # Create car at world position (0, 0)
    car = Car(0, 0, config["car_color"], MAX_SPEED, ACCELERATION, TURN_SPEED, DRIFT_TURN_SPEED, MAX_NITRO)

    # Create a Speedometer
    speedometer = Speedometer(x=game_window.width - 100, y=game_window.height - 100, radius=80, max_speed=100, unit="km/h", show_digital_speedometer=False)
    
    # Create a Nitro Gauge
    nitro_gauge = NitroGauge(x=game_window.width - 260, y=game_window.height - 160, max_nitro_ml=MAX_NITRO, height=150, width=80, text_color=(0, 255, 0))

    # Create camera with window reference
    camera = Camera(game_window)
    
    # List to store skid marks
    skid_marks = []
    
    # NETWORK SETUP
    client = CarGameClient(config["server"], config["port"], config["player_name"], config["car_color"], network_error_close)
    try:
        client.connect()
    except Exception as e:
        messagebox.showerror(f'No Connection to Server', f'Unable to Connect to {config["server"]} on Port {config["port"]}! ({e})')
        close()
        

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
            car_color=data["car_color"],
            points = data.get("points", 0),
            boosting=data.get("is_boosting", False),
            speed_kmh=data.get("speed_kmh", 0)
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
                nitro_gauge.x = game_window.width - 260
                nitro_gauge.y = game_window.height - 160
                print(f"Window resized to: {game_window.width}x{game_window.height}")

        # Get pressed keys
        keys = pygame.key.get_pressed()
        
        # Update car
        car.update(keys, skid_marks, 1 / FPS)
        speedometer.update_speed(car.get_speed_kmh())
        speedometer.update()
        if car.nitro_active == False:
            if car.current_nitro < MAX_NITRO:
                car.current_nitro += 1
        nitro_gauge.update_nitro(car.current_nitro)
        nitro_gauge.update()

        # Send local car state to server
        client.send_player_state(car.x, car.y, car.angle, car.is_drifting, car.car_color, points, car.nitro_active, car.get_speed_kmh())
        
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
        nitro_gauge.draw(screen)

        # Draw all remote multiplayer cars
        for mp_car in remote_players.values():
            if mp_car.visible == True:
                mp_car.draw(screen, camera)
        
        calculate_points(car)

        # Draw UI elements
        draw_ui(screen, car, game_window)
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    # Quit
    client.close()
    pygame.quit()
    close()

if __name__ == "__main__":
    main()