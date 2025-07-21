import pygame
from pygame.locals import *

pygame.init()

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 120, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

FONT = pygame.font.Font(None, 32)


class InputBox:
    """Text-Eingabefeld für Benutzerinput"""
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == KEYDOWN and self.active:
            if event.key == K_RETURN:
                self.active = False
            elif event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = FONT.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_value(self):
        return self.text


class Button:
    """Ein einfacher Button"""
    def __init__(self, x, y, w, h, text, color, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.callback = callback
        self.txt_surface = FONT.render(text, True, BLACK)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(
            self.txt_surface,
            (self.rect.centerx - self.txt_surface.get_width() // 2,
             self.rect.centery - self.txt_surface.get_height() // 2)
        )

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_color = [120, 0, 240]  # default

        # Input-Felder
        self.name_input = InputBox(300, 100, 200, 32, "Player")
        self.server_input = InputBox(300, 150, 200, 32, "127.0.0.1")
        self.port_input = InputBox(300, 200, 200, 32, "5000")

        # Buttons
        self.color_buttons = [
            Button(300, 260, 60, 32, "Rot", RED, lambda: self.set_color([255, 0, 0])),
            Button(370, 260, 60, 32, "Grün", GREEN, lambda: self.set_color([0, 255, 0])),
            Button(440, 260, 60, 32, "Blau", BLUE, lambda: self.set_color([0, 0, 255]))
        ]
        self.start_button = Button(300, 320, 200, 40, "Spiel starten", GRAY, self.start_game)

        self.result = None

    def set_color(self, color):
        self.selected_color = color

    def start_game(self):
        self.result = {
            "player_name": self.name_input.get_value(),
            "server": self.server_input.get_value(),
            "port": int(self.port_input.get_value()),
            "car_color": self.selected_color
        }
        self.running = False

    def draw_labels(self):
        def render_label(text, x, y):
            label = FONT.render(text, True, BLACK)
            self.screen.blit(label, (x, y))

        render_label("Name:", 200, 105)
        render_label("Server:", 200, 155)
        render_label("Port:", 200, 205)
        render_label("Farbe:", 200, 265)

    def run(self):
        while self.running:
            self.screen.fill(WHITE)

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                self.name_input.handle_event(event)
                self.server_input.handle_event(event)
                self.port_input.handle_event(event)
                for btn in self.color_buttons:
                    btn.handle_event(event)
                self.start_button.handle_event(event)

            self.draw_labels()
            self.name_input.draw(self.screen)
            self.server_input.draw(self.screen)
            self.port_input.draw(self.screen)

            for btn in self.color_buttons:
                btn.draw(self.screen)

            # Zeige gewählte Farbe
            pygame.draw.rect(self.screen, self.selected_color, (520, 260, 32, 32))

            self.start_button.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(30)

        return self.result
