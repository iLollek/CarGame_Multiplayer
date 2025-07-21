import pygame
import math


class Speedometer:
    def __init__(self, x, y, radius=80, max_speed=200, unit="km/h", show_digital_speedometer=True,
                 bg_color=(30, 30, 30), needle_color=(255, 50, 50),
                 scale_color=(255, 255, 255), text_color=(255, 255, 255)):
        """
        Initialize the speedometer.
        
        Args:
            x, y: Position of the speedometer center
            radius: Radius of the speedometer
            max_speed: Maximum speed to display on the scale
            unit: Unit of measurement ("km/h", "m/s", "mph")
            bg_color: Background color of the speedometer
            needle_color: Color of the speed needle
            scale_color: Color of the scale markings
            text_color: Color of the text
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.max_speed = max_speed
        self.unit = unit
        self.bg_color = bg_color
        self.needle_color = needle_color
        self.scale_color = scale_color
        self.text_color = text_color
        self.show_digital_speedomter = show_digital_speedometer
        
        # Current speed
        self.current_speed = 0
        
        # Angle configuration (semicircle from -135° to +135°)
        self.start_angle = -135  # degrees
        self.end_angle = 135     # degrees
        self.total_angle = self.end_angle - self.start_angle  # 270°
        
        # Font for text
        self.font_large = pygame.font.Font(None, int(radius * 0.3))
        self.font_small = pygame.font.Font(None, int(radius * 0.2))
        
        # Smoothing for needle movement
        self.target_speed = 0
        self.smooth_factor = 0.1

    def update_speed(self, speed, smooth=True):
        """
        Update the speed value.
        
        Args:
            speed: New speed value
            smooth: Whether to smooth the needle movement
        """
        if smooth:
            self.target_speed = max(0, min(speed, self.max_speed))
        else:
            self.current_speed = max(0, min(speed, self.max_speed))
            self.target_speed = self.current_speed

    def update(self):
        """Update the speedometer (call this every frame for smooth animation)"""
        # Smooth needle movement
        speed_diff = self.target_speed - self.current_speed
        self.current_speed += speed_diff * self.smooth_factor

    def _speed_to_angle(self, speed):
        """Convert speed value to needle angle"""
        speed_ratio = min(speed / self.max_speed, 1.0)
        angle = self.start_angle + (speed_ratio * self.total_angle)
        return math.radians(angle)

    def _draw_background(self, surface):
        """Draw the speedometer background"""
        # Main circle
        pygame.draw.circle(surface, self.bg_color, (self.x, self.y), self.radius)
        pygame.draw.circle(surface, self.scale_color, (self.x, self.y), self.radius, 3)
        
        # Inner circle
        inner_radius = self.radius * 0.85
        pygame.draw.circle(surface, self.bg_color, (self.x, self.y), int(inner_radius))

    def _draw_scale(self, surface):
        """Draw the speed scale markings"""
        # Major tick marks (every 20 units)
        major_interval = max(20, self.max_speed // 10)
        minor_interval = major_interval // 4
        
        # Draw major ticks
        for speed in range(0, int(self.max_speed) + 1, major_interval):
            angle = self._speed_to_angle(speed)
            
            # Outer point
            outer_x = self.x + (self.radius * 0.85) * math.cos(angle)
            outer_y = self.y + (self.radius * 0.85) * math.sin(angle)
            
            # Inner point
            inner_x = self.x + (self.radius * 0.75) * math.cos(angle)
            inner_y = self.y + (self.radius * 0.75) * math.sin(angle)
            
            pygame.draw.line(surface, self.scale_color, (outer_x, outer_y), (inner_x, inner_y), 3)
            
            # Speed numbers
            text_x = self.x + (self.radius * 0.65) * math.cos(angle)
            text_y = self.y + (self.radius * 0.65) * math.sin(angle)
            
            text = self.font_small.render(str(speed), True, self.text_color)
            text_rect = text.get_rect(center=(text_x, text_y))
            surface.blit(text, text_rect)
        
        # Draw minor ticks
        for speed in range(0, int(self.max_speed) + 1, minor_interval):
            if speed % major_interval != 0:  # Skip major ticks
                angle = self._speed_to_angle(speed)
                
                outer_x = self.x + (self.radius * 0.85) * math.cos(angle)
                outer_y = self.y + (self.radius * 0.85) * math.sin(angle)
                
                inner_x = self.x + (self.radius * 0.8) * math.cos(angle)
                inner_y = self.y + (self.radius * 0.8) * math.sin(angle)
                
                pygame.draw.line(surface, self.scale_color, (outer_x, outer_y), (inner_x, inner_y), 1)

    def _draw_needle(self, surface):
        """Draw the speed needle"""
        angle = self._speed_to_angle(self.current_speed)
        
        # Needle tip
        tip_x = self.x + (self.radius * 0.7) * math.cos(angle)
        tip_y = self.y + (self.radius * 0.7) * math.sin(angle)
        
        # Needle base (opposite direction)
        base_length = self.radius * 0.15
        base_x = self.x - base_length * math.cos(angle)
        base_y = self.y - base_length * math.sin(angle)
        
        # Draw needle line
        pygame.draw.line(surface, self.needle_color, (base_x, base_y), (tip_x, tip_y), 4)
        
        # Center circle
        pygame.draw.circle(surface, self.needle_color, (self.x, self.y), 8)
        pygame.draw.circle(surface, self.bg_color, (self.x, self.y), 5)

    def _draw_digital_display(self, surface):
        """Draw digital speed display"""
        # Background for digital display
        display_width = self.radius * 0.8
        display_height = self.radius * 0.3
        display_x = self.x - display_width // 2
        display_y = self.y + self.radius * 0.3
        
        pygame.draw.rect(surface, (0, 0, 0), (display_x, display_y, display_width, display_height))
        pygame.draw.rect(surface, self.scale_color, (display_x, display_y, display_width, display_height), 2)
        
        # Digital speed text
        speed_text = f"{self.current_speed:.0f}"
        unit_text = self.unit
        
        speed_surface = self.font_large.render(speed_text, True, self.text_color)
        unit_surface = self.font_small.render(unit_text, True, self.text_color)
        
        # Center the text
        speed_rect = speed_surface.get_rect(center=(self.x, display_y + display_height * 0.4))
        unit_rect = unit_surface.get_rect(center=(self.x, display_y + display_height * 0.75))
        
        surface.blit(speed_surface, speed_rect)
        surface.blit(unit_surface, unit_rect)

    def _draw_redline(self, surface):
        """Draw red zone for high speeds (optional)"""
        if self.max_speed > 100:  # Only show redline for higher max speeds
            redline_start = self.max_speed * 0.8  # Red zone starts at 80% of max
            
            # Draw red arc
            redline_start_angle = self._speed_to_angle(redline_start)
            redline_end_angle = self._speed_to_angle(self.max_speed)
            
            # Create points for the red zone arc
            arc_points = []
            angle_step = 0.1
            current_angle = redline_start_angle
            
            while current_angle <= redline_end_angle:
                outer_x = self.x + (self.radius * 0.85) * math.cos(current_angle)
                outer_y = self.y + (self.radius * 0.85) * math.sin(current_angle)
                arc_points.append((outer_x, outer_y))
                current_angle += angle_step
            
            # Draw red arc as thick line segments
            if len(arc_points) > 1:
                for i in range(len(arc_points) - 1):
                    pygame.draw.line(surface, (255, 0, 0), arc_points[i], arc_points[i + 1], 5)

    def draw(self, surface):
        """
        Draw the complete speedometer on the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        self._draw_background(surface)
        self._draw_redline(surface)
        self._draw_scale(surface)
        self._draw_needle(surface)
        if self.show_digital_speedomter:
            self._draw_digital_display(surface)

    def set_position(self, x, y):
        """Change the speedometer position"""
        self.x = x
        self.y = y

    def set_max_speed(self, max_speed):
        """Change the maximum speed scale"""
        self.max_speed = max_speed
        # Reset current speed if it exceeds new max
        if self.current_speed > max_speed:
            self.current_speed = max_speed
        if self.target_speed > max_speed:
            self.target_speed = max_speed


# Example usage and demo
if __name__ == "__main__":
    pygame.init()
    
    # Create screen
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Speedometer Demo")
    clock = pygame.time.Clock()
    
    # Create speedometers with different configurations
    speedometer_kmh = Speedometer(200, 200, radius=120, max_speed=200, unit="km/h")
    speedometer_ms = Speedometer(600, 200, radius=100, max_speed=50, unit="m/s", 
                                needle_color=(0, 255, 0))
    speedometer_mph = Speedometer(400, 450, radius=90, max_speed=120, unit="mph", 
                                 bg_color=(20, 20, 50), needle_color=(255, 255, 0))
    
    # Demo variables
    demo_speed = 0
    speed_direction = 1
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Demo animation - speed goes up and down
        demo_speed += speed_direction * 1.5
        if demo_speed >= 180:
            speed_direction = -1
        elif demo_speed <= 0:
            speed_direction = 1
        
        # Update speedometers
        speedometer_kmh.update_speed(demo_speed)
        speedometer_ms.update_speed(demo_speed / 3.6)  # Convert km/h to m/s
        speedometer_mph.update_speed(demo_speed / 1.609)  # Convert km/h to mph
        
        speedometer_kmh.update()
        speedometer_ms.update()
        speedometer_mph.update()
        
        # Draw everything
        screen.fill((50, 50, 50))
        
        speedometer_kmh.draw(screen)
        speedometer_ms.draw(screen)
        speedometer_mph.draw(screen)
        
        # Instructions
        font = pygame.font.Font(None, 36)
        text = font.render("Speedometer Demo - Press ESC to exit", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()