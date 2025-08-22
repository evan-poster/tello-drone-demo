import pygame
import math

from drone_controller import ConnectionStatus

from global_variables import *

class GamepadInterface:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        
        # Control states
        self.active_controls = set()
        
        # Button definitions
        self.buttons = {
            'takeoff': pygame.Rect(x + 50, y + 400, 100, 40),
            'land': pygame.Rect(x + 170, y + 400, 100, 40),
            'emergency': pygame.Rect(x + 290, y + 400, 100, 40)
        }
        
        # Movement indicators
        self.center_x = x + width // 2
        self.center_y = y + 200
        self.joystick_radius = 80
        
    def draw(self, screen, active_keys, drone_controller=None):
        # Draw panel background
        pygame.draw.rect(screen, LIGHT_GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        # Title with speed boost and RC mode indicators
        title_text = "GAMEPAD CONTROLS"
        title_color = BLACK
        
        if drone_controller:
            if drone_controller.rc_mode_active:
                title_text += " 🎮 RC MODE"
                title_color = BLUE
            if drone_controller.speed_multiplier > 1.0:
                title_text += " 🚀 SPEED BOOST"
                title_color = RED if not drone_controller.rc_mode_active else ORANGE
        
        title = self.title_font.render(title_text, True, title_color)
        screen.blit(title, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw virtual joystick
        self.draw_joystick(screen, active_keys)
        
        # Draw rotation controls
        self.draw_rotation_controls(screen, active_keys)
        
        # Draw vertical controls
        self.draw_vertical_controls(screen, active_keys)
        
        # Draw action buttons
        self.draw_action_buttons(screen)
        
        # Draw control legend
        self.draw_control_legend(screen)
    
    def draw_joystick(self, screen, active_keys):
        # Main joystick circle
        pygame.draw.circle(screen, WHITE, (self.center_x, self.center_y), self.joystick_radius)
        pygame.draw.circle(screen, BLACK, (self.center_x, self.center_y), self.joystick_radius, 3)
        
        # Center dot
        center_color = GREEN if any(k in active_keys for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]) else DARK_GRAY
        pygame.draw.circle(screen, center_color, (self.center_x, self.center_y), 8)
        
        # Directional indicators
        directions = {
            pygame.K_w: (0, -1, "W"),  # Forward
            pygame.K_s: (0, 1, "S"),   # Back
            pygame.K_a: (-1, 0, "A"),  # Left
            pygame.K_d: (1, 0, "D")    # Right
        }
        
        for key, (dx, dy, label) in directions.items():
            active = key in active_keys
            
            # Calculate position
            x = self.center_x + dx * (self.joystick_radius - 20)
            y = self.center_y + dy * (self.joystick_radius - 20)
            
            # Enhanced visual feedback
            if active:
                # Larger, brighter circle when active
                pygame.draw.circle(screen, GREEN, (int(x), int(y)), 18)
                pygame.draw.circle(screen, WHITE, (int(x), int(y)), 15)
                pygame.draw.circle(screen, BLACK, (int(x), int(y)), 18, 3)
                
                # Draw directional arrow
                arrow_length = 25
                arrow_x = self.center_x + dx * arrow_length
                arrow_y = self.center_y + dy * arrow_length
                pygame.draw.line(screen, GREEN, (self.center_x, self.center_y), (int(arrow_x), int(arrow_y)), 4)
                
                # Arrow head
                if dx != 0:  # Horizontal arrows
                    pygame.draw.polygon(screen, GREEN, [
                        (int(arrow_x), int(arrow_y)),
                        (int(arrow_x - dx * 8), int(arrow_y - 5)),
                        (int(arrow_x - dx * 8), int(arrow_y + 5))
                    ])
                else:  # Vertical arrows
                    pygame.draw.polygon(screen, GREEN, [
                        (int(arrow_x), int(arrow_y)),
                        (int(arrow_x - 5), int(arrow_y - dy * 8)),
                        (int(arrow_x + 5), int(arrow_y - dy * 8))
                    ])
            else:
                # Normal state
                pygame.draw.circle(screen, LIGHT_GRAY, (int(x), int(y)), 15)
                pygame.draw.circle(screen, BLACK, (int(x), int(y)), 15, 2)
            
            # Draw label
            text_color = BLACK if active else DARK_GRAY
            text = self.font.render(label, True, text_color)
            text_rect = text.get_rect(center=(int(x), int(y)))
            screen.blit(text, text_rect)
    
    def draw_rotation_controls(self, screen, active_keys):
        # Rotation controls (Q/E)
        q_active = pygame.K_q in active_keys
        e_active = pygame.K_e in active_keys
        
        # Q (Counter-clockwise)
        q_rect = pygame.Rect(self.center_x - 150, self.center_y - 20, 40, 40)
        if q_active:
            pygame.draw.rect(screen, GREEN, q_rect)
            pygame.draw.rect(screen, WHITE, pygame.Rect(q_rect.x + 3, q_rect.y + 3, 34, 34))
            pygame.draw.rect(screen, BLACK, q_rect, 3)
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, q_rect)
            pygame.draw.rect(screen, BLACK, q_rect, 2)
        
        q_text_color = BLACK if q_active else DARK_GRAY
        q_text = self.font.render("Q", True, q_text_color)
        q_text_rect = q_text.get_rect(center=q_rect.center)
        screen.blit(q_text, q_text_rect)
        
        # Rotation arrow (CCW)
        self.draw_rotation_arrow(screen, self.center_x - 130, self.center_y, False, q_active)
        
        # E (Clockwise)
        e_rect = pygame.Rect(self.center_x + 110, self.center_y - 20, 40, 40)
        if e_active:
            pygame.draw.rect(screen, GREEN, e_rect)
            pygame.draw.rect(screen, WHITE, pygame.Rect(e_rect.x + 3, e_rect.y + 3, 34, 34))
            pygame.draw.rect(screen, BLACK, e_rect, 3)
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, e_rect)
            pygame.draw.rect(screen, BLACK, e_rect, 2)
        
        e_text_color = BLACK if e_active else DARK_GRAY
        e_text = self.font.render("E", True, e_text_color)
        e_text_rect = e_text.get_rect(center=e_rect.center)
        screen.blit(e_text, e_text_rect)
        
        # Rotation arrow (CW)
        self.draw_rotation_arrow(screen, self.center_x + 130, self.center_y, True, e_active)
    
    def draw_vertical_controls(self, screen, active_keys):
        # Vertical controls (I/K)
        i_active = pygame.K_i in active_keys
        k_active = pygame.K_k in active_keys
        
        # I (Up)
        i_rect = pygame.Rect(self.center_x - 20, self.center_y - 150, 40, 40)
        if i_active:
            pygame.draw.rect(screen, GREEN, i_rect)
            pygame.draw.rect(screen, WHITE, pygame.Rect(i_rect.x + 3, i_rect.y + 3, 34, 34))
            pygame.draw.rect(screen, BLACK, i_rect, 3)
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, i_rect)
            pygame.draw.rect(screen, BLACK, i_rect, 2)
        
        i_text_color = BLACK if i_active else DARK_GRAY
        i_text = self.font.render("I", True, i_text_color)
        i_text_rect = i_text.get_rect(center=i_rect.center)
        screen.blit(i_text, i_text_rect)
        
        # Up arrow
        arrow_color = GREEN if i_active else GRAY
        arrow_width = 4 if i_active else 2
        pygame.draw.polygon(screen, arrow_color, [
            (self.center_x, self.center_y - 100),
            (self.center_x - 12, self.center_y - 85),
            (self.center_x + 12, self.center_y - 85)
        ])
        if i_active:
            pygame.draw.line(screen, GREEN, (self.center_x, self.center_y - 85), (self.center_x, self.center_y - 70), 4)
        
        # K (Down)
        k_rect = pygame.Rect(self.center_x - 20, self.center_y + 110, 40, 40)
        if k_active:
            pygame.draw.rect(screen, GREEN, k_rect)
            pygame.draw.rect(screen, WHITE, pygame.Rect(k_rect.x + 3, k_rect.y + 3, 34, 34))
            pygame.draw.rect(screen, BLACK, k_rect, 3)
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, k_rect)
            pygame.draw.rect(screen, BLACK, k_rect, 2)
        
        k_text_color = BLACK if k_active else DARK_GRAY
        k_text = self.font.render("K", True, k_text_color)
        k_text_rect = k_text.get_rect(center=k_rect.center)
        screen.blit(k_text, k_text_rect)
        
        # Down arrow
        arrow_color = GREEN if k_active else GRAY
        pygame.draw.polygon(screen, arrow_color, [
            (self.center_x, self.center_y + 100),
            (self.center_x - 12, self.center_y + 85),
            (self.center_x + 12, self.center_y + 85)
        ])
        if k_active:
            pygame.draw.line(screen, GREEN, (self.center_x, self.center_y + 85), (self.center_x, self.center_y + 70), 4)
    
    def draw_rotation_arrow(self, screen, x, y, clockwise, active=False):
        # Draw curved arrow for rotation
        color = GREEN if active else GRAY
        width = 4 if active else 2
        
        # Simple arrow representation
        if clockwise:
            pygame.draw.arc(screen, color, (x-15, y-15, 30, 30), 0, math.pi*1.5, width)
            if active:
                # Add arrow head for clockwise
                pygame.draw.polygon(screen, color, [
                    (x + 12, y + 8),
                    (x + 8, y + 12),
                    (x + 15, y + 15)
                ])
        else:
            pygame.draw.arc(screen, color, (x-15, y-15, 30, 30), math.pi*0.5, math.pi*2, width)
            if active:
                # Add arrow head for counter-clockwise
                pygame.draw.polygon(screen, color, [
                    (x - 12, y + 8),
                    (x - 8, y + 12),
                    (x - 15, y + 15)
                ])
    
    def draw_action_buttons(self, screen):
        # Takeoff button
        takeoff_color = LIGHT_GRAY
        pygame.draw.rect(screen, takeoff_color, self.buttons['takeoff'])
        pygame.draw.rect(screen, BLACK, self.buttons['takeoff'], 2)
        takeoff_text = self.font.render("TAKEOFF", True, BLACK)
        takeoff_rect = takeoff_text.get_rect(center=self.buttons['takeoff'].center)
        screen.blit(takeoff_text, takeoff_rect)
        
        # Land button
        land_color = LIGHT_GRAY
        pygame.draw.rect(screen, land_color, self.buttons['land'])
        pygame.draw.rect(screen, BLACK, self.buttons['land'], 2)
        land_text = self.font.render("LAND", True, BLACK)
        land_rect = land_text.get_rect(center=self.buttons['land'].center)
        screen.blit(land_text, land_rect)
        
        # Emergency button
        emergency_color = RED
        pygame.draw.rect(screen, emergency_color, self.buttons['emergency'])
        pygame.draw.rect(screen, BLACK, self.buttons['emergency'], 2)
        emergency_text = self.font.render("STOP", True, WHITE)
        emergency_rect = emergency_text.get_rect(center=self.buttons['emergency'].center)
        screen.blit(emergency_text, emergency_rect)
    
    def draw_control_legend(self, screen):
        legend_y = self.rect.y + 460
        legend_text = [
            "WASD: Move Forward/Back/Left/Right",
            "QE: Rotate Counter-Clockwise/Clockwise",
            "IK: Move Up/Down",
            "T: Takeoff | L: Land | H: Emergency Stop",
            "F: Forward Flip",
            "SHIFT: Hold for 2x Speed | SPACE: Clear Queue",
            "CTRL: Hold for Real-time RC Control"
        ]
        
        for i, text in enumerate(legend_text):
            rendered = self.font.render(text, True, BLACK)
            screen.blit(rendered, (self.rect.x + 10, legend_y + i * 22))
    
    def handle_click(self, pos, drone_controller):
        """Handle mouse clicks on buttons"""
        # Only allow button clicks if connected (except emergency stop)
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(pos):
                if button_name == 'emergency':
                    # Emergency stop always works if drone exists
                    drone_controller.emergency_stop()
                elif drone_controller.connection_status == ConnectionStatus.CONNECTED:
                    if button_name == 'takeoff':
                        drone_controller.takeoff()
                    elif button_name == 'land':
                        drone_controller.land()
