import pygame
import sys
import time
import threading

from drone_controller import DroneController, ConnectionStatus
from telemetry_panel import TelemetryPanel
from gamepad_interface import GamepadInterface

from global_variables import *

class DroneInterface:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Drone Control Interface")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize components
        self.drone_controller = DroneController()
        self.telemetry_panel = TelemetryPanel(50, 50, 300, 400)
        self.gamepad_interface = GamepadInterface(400, 50, 450, 650)
        
        # Input tracking
        self.active_keys = set()
        self.last_telemetry_update = 0
        self.telemetry_update_interval = 1.0  # Update every second
        self.shift_pressed = False
        self.ctrl_pressed = False
        
        # Connect button
        self.connect_button = pygame.Rect(900, 50, 150, 40)
        self.font = pygame.font.Font(None, 24)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self.active_keys.add(event.key)
                
                # Handle shift key for speed multiplier
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.shift_pressed = True
                    self.drone_controller.set_speed_multiplier(3.0)
                
                # Handle ctrl key for RC mode
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    self.ctrl_pressed = True
                    print("🎮 Ctrl key pressed - activating RC mode")
                    self.drone_controller.start_rc_mode()
                
                self.handle_key_press(event.key)
            
            elif event.type == pygame.KEYUP:
                self.active_keys.discard(event.key)
                
                # Handle shift key release
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.shift_pressed = False
                    self.drone_controller.set_speed_multiplier(1.0)
                
                # Handle ctrl key release
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    self.ctrl_pressed = False
                    print("🎮 Ctrl key released - deactivating RC mode")
                    self.drone_controller.stop_rc_mode()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
    
    def handle_key_press(self, key):
        """Handle individual key presses for drone commands"""
        # Handle special keys that don't require connection
        if key == pygame.K_SPACE:
            self.drone_controller.clear_command_queue()
            return
        
        # Only execute movement commands if connected
        if self.drone_controller.connection_status != ConnectionStatus.CONNECTED:
            return
        
        # If Ctrl is pressed, movement keys are handled by RC mode
        # Only handle non-movement keys when Ctrl is pressed
        if self.ctrl_pressed:
            non_movement_commands = {
                pygame.K_t: self.drone_controller.takeoff,
                pygame.K_l: self.drone_controller.land,
                pygame.K_h: self.drone_controller.emergency_stop,
                pygame.K_f: self.drone_controller.flip_forward,
            }
            if key in non_movement_commands:
                non_movement_commands[key]()
            return
            
        # Normal discrete movement commands when Ctrl is not pressed
        key_commands = {
            pygame.K_w: self.drone_controller.move_forward,
            pygame.K_s: self.drone_controller.move_back,
            pygame.K_a: self.drone_controller.move_left,
            pygame.K_d: self.drone_controller.move_right,
            pygame.K_q: self.drone_controller.rotate_counter_clockwise,
            pygame.K_e: self.drone_controller.rotate_clockwise,
            pygame.K_i: self.drone_controller.move_up,
            pygame.K_k: self.drone_controller.move_down,
            pygame.K_t: self.drone_controller.takeoff,
            pygame.K_l: self.drone_controller.land,
            pygame.K_h: self.drone_controller.emergency_stop,
            pygame.K_f: self.drone_controller.flip_forward,
        }
        
        if key in key_commands:
            key_commands[key]()
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks"""
        # Connect button
        if self.connect_button.collidepoint(pos):
            if self.drone_controller.connection_status == ConnectionStatus.DISCONNECTED:
                threading.Thread(target=self.drone_controller.connect, daemon=True).start()
            else:
                self.drone_controller.disconnect()
        
        # Gamepad buttons
        self.gamepad_interface.handle_click(pos, self.drone_controller)
    
    def update(self):
        """Update game state"""
        current_time = time.time()
        
        # Update telemetry periodically
        if current_time - self.last_telemetry_update >= self.telemetry_update_interval:
            if self.drone_controller.connection_status == ConnectionStatus.CONNECTED:
                threading.Thread(target=self.drone_controller.update_telemetry, daemon=True).start()
            self.last_telemetry_update = current_time
        
        # Update RC control if Ctrl is pressed
        if self.ctrl_pressed and self.drone_controller.connection_status == ConnectionStatus.CONNECTED:
            # Debug: Show active keys when in RC mode
            if self.active_keys:
                movement_keys = {pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_q, pygame.K_e, pygame.K_i, pygame.K_k}
                active_movement = [str(key) for key in self.active_keys if key in movement_keys]
                if active_movement:
                    print(f"🎮 RC Update - Active keys: {active_movement}")
            self.drone_controller.update_rc_control(self.active_keys)
    
    def draw(self):
        """Draw the interface"""
        self.screen.fill(WHITE)
        
        # Draw components
        self.telemetry_panel.draw(self.screen, self.drone_controller)
        self.gamepad_interface.draw(self.screen, self.active_keys, self.drone_controller)
        
        # Draw connect button
        button_color = RED if self.drone_controller.connection_status == ConnectionStatus.DISCONNECTED else GREEN
        button_text = "CONNECT" if self.drone_controller.connection_status == ConnectionStatus.DISCONNECTED else "DISCONNECT"
        
        pygame.draw.rect(self.screen, button_color, self.connect_button)
        pygame.draw.rect(self.screen, BLACK, self.connect_button, 2)
        
        text = self.font.render(button_text, True, WHITE)
        text_rect = text.get_rect(center=self.connect_button.center)
        self.screen.blit(text, text_rect)
        
        # Draw title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("DRONE CONTROL INTERFACE", True, BLACK)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 25))
        self.screen.blit(title, title_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("Starting Drone Control Interface...")
        print("Controls:")
        print("  WASD: Move Forward/Back/Left/Right")
        print("  QE: Rotate Counter-Clockwise/Clockwise")
        print("  IK: Move Up/Down")
        print("  T: Takeoff | L: Land | H: Emergency Stop")
        print("  F: Forward Flip")
        print("  SHIFT: Hold for 2x speed boost")
        print("  CTRL: Hold for real-time RC control")
        print("  SPACE: Clear queued commands")
        print("  Click CONNECT to connect to drone")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        # Cleanup
        self.drone_controller.disconnect()
        pygame.quit()
        sys.exit()
