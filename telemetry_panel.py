import pygame

from drone_controller import ConnectionStatus

from global_variables import *

class TelemetryPanel:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
    
    def draw(self, screen, drone_controller):
        # Draw panel background
        pygame.draw.rect(screen, LIGHT_GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        # Title
        title = self.title_font.render("TELEMETRY", True, BLACK)
        screen.blit(title, (self.rect.x + 10, self.rect.y + 10))
        
        y_offset = 50
        
        # Connection Status
        status_color = {
            ConnectionStatus.DISCONNECTED: RED,
            ConnectionStatus.CONNECTING: YELLOW,
            ConnectionStatus.CONNECTED: GREEN,
            ConnectionStatus.ERROR: RED
        }[drone_controller.connection_status]
        
        status_text = self.font.render(f"Status: {drone_controller.connection_status.value}", True, status_color)
        screen.blit(status_text, (self.rect.x + 10, self.rect.y + y_offset))
        y_offset += 30
        
        # Battery Level
        battery_text = self.font.render(f"Battery: {drone_controller.battery_level}%", True, BLACK)
        screen.blit(battery_text, (self.rect.x + 10, self.rect.y + y_offset))
        
        # Battery bar
        bar_rect = pygame.Rect(self.rect.x + 10, self.rect.y + y_offset + 25, 200, 20)
        pygame.draw.rect(screen, WHITE, bar_rect)
        pygame.draw.rect(screen, BLACK, bar_rect, 2)
        
        # Battery fill
        fill_width = int((drone_controller.battery_level / 100) * 198)
        if fill_width > 0:
            fill_color = GREEN if drone_controller.battery_level > 30 else (ORANGE if drone_controller.battery_level > 15 else RED)
            fill_rect = pygame.Rect(bar_rect.x + 1, bar_rect.y + 1, fill_width, 18)
            pygame.draw.rect(screen, fill_color, fill_rect)
        
        y_offset += 60
        
        # Height
        height_text = self.font.render(f"Height: {drone_controller.height} cm", True, BLACK)
        screen.blit(height_text, (self.rect.x + 10, self.rect.y + y_offset))
        y_offset += 30
        
        # Flight Time
        flight_text = self.font.render(f"Flight Time: {drone_controller.flight_time} s", True, BLACK)
        screen.blit(flight_text, (self.rect.x + 10, self.rect.y + y_offset))
        y_offset += 30
        
        # Flying Status
        flying_status = "FLYING" if drone_controller.is_flying else "GROUNDED"
        flying_color = GREEN if drone_controller.is_flying else GRAY
        flying_text = self.font.render(f"Status: {flying_status}", True, flying_color)
        screen.blit(flying_text, (self.rect.x + 10, self.rect.y + y_offset))
