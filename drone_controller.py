import time
import threading
import pygame
from enum import Enum
from djitellopy import Tello
from collections import deque

from global_variables import *

class ConnectionStatus(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"

class DroneController:
    def __init__(self):
        self.tello = None
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.battery_level = 0
        self.height = 0
        self.flight_time = 0
        self.is_flying = False
        self.imu_ready = False
        self.takeoff_time = 0
        self.imu_stabilization_delay = 3.0  # Wait 3 seconds after takeoff for IMU
        self.last_command_time = 0
        self.command_cooldown = 0.5  # Prevent command spam
        
        # Enhanced features
        self.command_queue = deque()
        self.speed_multiplier = 1.0
        self.last_ready_beep = 0
        self.ready_beep_interval = 5.0  # Beep every 5 seconds when ready
        
        # RC control mode
        self.rc_mode_active = False
        self.rc_thread = None
        self.rc_stop_event = threading.Event()
        self.current_rc_values = {'left_right': 0, 'forward_back': 0, 'up_down': 0, 'yaw': 0}
        
        # Initialize pygame mixer for audio
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_enabled = True
        except:
            self.audio_enabled = False
            print("⚠️ Audio not available - beep notifications disabled")
        
    def connect(self):
        """Connect to the drone"""
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            self.tello = Tello()
            self.tello.connect(wait_for_state=False)
            self.connection_status = ConnectionStatus.CONNECTED
            self.update_telemetry()
            print("✓ Connected to drone successfully!")
            print("📋 Instructions:")
            print("  1. Place drone on flat surface for IMU calibration")
            print("  2. Press 'T' or click TAKEOFF to enable movement controls")
            print("  3. Use WASD for movement, QE for rotation, IK for up/down")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("💡 Troubleshooting:")
            print("  - Ensure drone is powered on")
            print("  - Check WiFi connection to drone")
            print("  - Try moving closer to drone")
            self.connection_status = ConnectionStatus.ERROR
            return False
    
    def disconnect(self):
        """Disconnect from the drone"""
        # Stop RC mode if active
        if self.rc_mode_active:
            self.stop_rc_mode()
        
        if self.tello:
            try:
                if self.is_flying:
                    self.tello.land()
                self.tello.end()
            except:
                pass
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.tello = None
    
    def update_telemetry(self):
        """Update drone telemetry data"""
        if self.tello and self.connection_status == ConnectionStatus.CONNECTED:
            try:
                self.battery_level = self.tello.get_battery()
                print(self.battery_level)
                self.height = self.tello.get_height()
                self.flight_time = self.tello.get_flight_time()
                
                # Check if ready for beep notification
                self.check_ready_beep()
            except:
                pass
    
    def set_speed_multiplier(self, multiplier):
        """Set speed multiplier for enhanced movement"""
        self.speed_multiplier = multiplier
        if multiplier > 1.0:
            print(f"🚀 Speed boost activated! {multiplier}x movement speed")
        else:
            print("🐌 Normal speed restored")
    
    def clear_command_queue(self):
        """Clear all queued commands"""
        if len(self.command_queue) > 0:
            self.command_queue.clear()
            print(f"🗑️ Cleared {len(self.command_queue)} queued commands")
            self.play_beep(frequency=800, duration=0.1)  # Clear sound
        else:
            print("📭 No commands to clear")
    
    def play_beep(self, frequency=1000, duration=0.2):
        """Play a beep sound for notifications"""
        if not self.audio_enabled:
            return
        
        try:
            # Generate a simple beep tone
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = 4096 * (i % (sample_rate // frequency) < (sample_rate // frequency) // 2)
                arr.append([wave, wave])
            
            sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
            sound.play()
        except Exception as e:
            # Fallback to system beep if pygame audio fails
            print("\a")  # ASCII bell character
    
    def check_ready_beep(self):
        """Check if drone is ready and play beep if appropriate"""
        current_time = time.time()
        
        # Only beep if:
        # 1. Drone is flying and IMU ready
        # 2. No commands in queue
        # 3. Enough time has passed since last beep
        if (self.is_flying and self.imu_ready and
            len(self.command_queue) == 0 and
            current_time - self.last_ready_beep >= self.ready_beep_interval):
            
            self.play_beep(frequency=1200, duration=0.1)
            self.last_ready_beep = current_time
            print("🔔 Drone ready for commands")
    
    def can_execute_command(self):
        """Check if enough time has passed since last command"""
        current_time = time.time()
        if current_time - self.last_command_time >= self.command_cooldown:
            self.last_command_time = current_time
            return True
        return False
    
    def execute_command(self, command_func, *args):
        """Execute a drone command with cooldown protection"""
        if self.tello and self.connection_status == ConnectionStatus.CONNECTED and self.can_execute_command():
            try:
                command_func(*args)
                return True
            except Exception as e:
                error_msg = str(e)
                if "No valid imu" in error_msg:
                    print(f"IMU Error: Drone must be taken off first before movement commands work")
                else:
                    print(f"Command failed: {e}")
                return False
        elif self.connection_status != ConnectionStatus.CONNECTED:
            print(f"Cannot execute command: {self.connection_status.value}")
        return False
    
    def check_imu_ready(self):
        """Check if IMU is ready for movement commands"""
        if not self.is_flying:
            return False
        
        current_time = time.time()
        if current_time - self.takeoff_time >= self.imu_stabilization_delay:
            self.imu_ready = True
        
        return self.imu_ready
    
    def execute_movement_command(self, command_func, *args):
        """Execute a movement command with takeoff and IMU checks"""
        if not self.is_flying:
            print("Movement commands require takeoff first. Press 'T' or click TAKEOFF button.")
            return False
        
        if not self.check_imu_ready():
            remaining_time = self.imu_stabilization_delay - (time.time() - self.takeoff_time)
            print(f"⏳ IMU stabilizing... {remaining_time:.1f}s remaining. Using RC controls for immediate movement.")
            return self.execute_rc_movement(command_func, *args)
        
        # Apply speed multiplier to movement distance
        modified_args = []
        for arg in args:
            if isinstance(arg, (int, float)):
                modified_args.append(int(arg * self.speed_multiplier))
            else:
                modified_args.append(arg)
        
        speed_indicator = "🚀" if self.speed_multiplier > 1.0 else "✈️"
        if modified_args:
            print(f"{speed_indicator} Command: {command_func.__name__} with distance/angle: {modified_args[0]}")
        
        return self.execute_command(command_func, *modified_args)
    
    def execute_rc_movement(self, command_func, *args):
        """Execute movement using RC controls as fallback"""
        if not self.tello or self.connection_status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            # RC controls use speed values from -100 to 100
            # Apply speed multiplier to RC speed (capped at 100)
            base_rc_speed = 50
            rc_speed = min(int(base_rc_speed * self.speed_multiplier), 100)
            
            speed_indicator = "🚀" if self.speed_multiplier > 1.0 else "🎮"
            
            # Map movement commands to RC controls
            if command_func == self.tello.move_forward:
                self.tello.send_rc_control(0, rc_speed, 0, 0)
                print(f"{speed_indicator} RC forward (speed: {rc_speed})")
            elif command_func == self.tello.move_back:
                self.tello.send_rc_control(0, -rc_speed, 0, 0)
                print(f"{speed_indicator} RC backward (speed: {rc_speed})")
            elif command_func == self.tello.move_left:
                self.tello.send_rc_control(-rc_speed, 0, 0, 0)
                print(f"{speed_indicator} RC left (speed: {rc_speed})")
            elif command_func == self.tello.move_right:
                self.tello.send_rc_control(rc_speed, 0, 0, 0)
                print(f"{speed_indicator} RC right (speed: {rc_speed})")
            elif command_func == self.tello.move_up:
                self.tello.send_rc_control(0, 0, rc_speed, 0)
                print(f"{speed_indicator} RC up (speed: {rc_speed})")
            elif command_func == self.tello.move_down:
                self.tello.send_rc_control(0, 0, -rc_speed, 0)
                print(f"{speed_indicator} RC down (speed: {rc_speed})")
            elif command_func == self.tello.rotate_clockwise:
                self.tello.send_rc_control(0, 0, 0, rc_speed)
                print(f"{speed_indicator} RC rotate right (speed: {rc_speed})")
            elif command_func == self.tello.rotate_counter_clockwise:
                self.tello.send_rc_control(0, 0, 0, -rc_speed)
                print(f"{speed_indicator} RC rotate left (speed: {rc_speed})")
            
            # Stop movement after short duration (longer for speed boost)
            duration = 0.4 if self.speed_multiplier > 1.0 else 0.3
            threading.Timer(duration, lambda: self.tello.send_rc_control(0, 0, 0, 0)).start()
            return True
        except Exception as e:
            print(f"RC movement failed: {e}")
            return False
    
    def takeoff(self):
        """Take off"""
        if self.is_flying:
            print("⚠️  Drone is already flying!")
            return
        
        print("🚁 Attempting takeoff...")
        if self.execute_command(self.tello.takeoff):
            self.is_flying = True
            self.imu_ready = False
            self.takeoff_time = time.time()
            print("✅ Takeoff successful!")
            print(f"⏳ IMU stabilizing for {self.imu_stabilization_delay}s... RC controls available immediately.")
            
            # Start a timer to notify when IMU is ready
            def notify_imu_ready():
                time.sleep(self.imu_stabilization_delay)
                if self.is_flying:  # Only notify if still flying
                    self.imu_ready = True
                    print("✅ IMU stabilized! Full movement commands now available.")
            
            threading.Thread(target=notify_imu_ready, daemon=True).start()
        else:
            print("❌ Takeoff failed. Check drone status and try again.")
    
    def land(self):
        """Land"""
        if not self.is_flying:
            print("⚠️  Drone is already on the ground!")
            return
            
        print("🛬 Landing drone...")
        if self.execute_command(self.tello.land):
            self.is_flying = False
            self.imu_ready = False
            print("✅ Landing successful. Movement controls disabled.")
        else:
            print("❌ Landing failed. Try emergency stop if needed.")
    
    def move_forward(self):
        """Move forward"""
        self.execute_movement_command(self.tello.move_forward, REAL_MOVEMENT_SPEED)
    
    def move_back(self):
        """Move backward"""
        self.execute_movement_command(self.tello.move_back, REAL_MOVEMENT_SPEED)
    
    def move_left(self):
        """Move left"""
        self.execute_movement_command(self.tello.move_left, REAL_MOVEMENT_SPEED)
    
    def move_right(self):
        """Move right"""
        self.execute_movement_command(self.tello.move_right, REAL_MOVEMENT_SPEED)
    
    def move_up(self):
        """Move up"""
        self.execute_movement_command(self.tello.move_up, REAL_VERTICAL_SPEED)
    
    def move_down(self):
        """Move down"""
        self.execute_movement_command(self.tello.move_down, REAL_VERTICAL_SPEED)
    
    def rotate_clockwise(self):
        """Rotate clockwise"""
        self.execute_movement_command(self.tello.rotate_clockwise, REAL_ROTATION_SPEED)
    
    def rotate_counter_clockwise(self):
        """Rotate counter-clockwise"""
        self.execute_movement_command(self.tello.rotate_counter_clockwise, REAL_ROTATION_SPEED)
    
    def flip_forward(self):
        """Perform a forward flip"""
        if not self.is_flying:
            print("Flip commands require takeoff first. Press 'T' or click TAKEOFF button.")
            return False
        
        if not self.imu_ready:
            print("⏳ IMU must be stabilized before performing flips. Please wait...")
            return False
        
        print("🤸 Performing forward flip!")
        return self.execute_command(self.tello.flip_forward)
    
    def emergency_stop(self):
        """Emergency stop - hover in place"""
        if self.tello and self.connection_status == ConnectionStatus.CONNECTED:
            try:
                # Send stop command (hover)
                self.tello.send_rc_control(0, 0, 0, 0)
            except:
                pass
    
    def start_rc_mode(self):
        """Start continuous RC control mode"""
        print(f"🎮 start_rc_mode called - tello: {self.tello is not None}, status: {self.connection_status}, active: {self.rc_mode_active}")
        if not self.rc_mode_active and self.tello and self.connection_status == ConnectionStatus.CONNECTED:
            self.rc_mode_active = True
            self.rc_stop_event.clear()
            print("🎮 RC Mode activated - continuous control enabled")
        elif self.rc_mode_active:
            print("🎮 RC Mode already active")
        else:
            print("🎮 RC Mode not started - drone not connected or not available")
    
    def stop_rc_mode(self):
        """Stop continuous RC control mode"""
        if self.rc_mode_active:
            self.rc_mode_active = False
            self.rc_stop_event.set()
            
            # Send stop command to ensure drone stops moving
            if self.tello and self.connection_status == ConnectionStatus.CONNECTED:
                try:
                    self.tello.send_rc_control(0, 0, 0, 0)
                except:
                    pass
            
            # Reset RC values
            self.current_rc_values = {'left_right': 0, 'forward_back': 0, 'up_down': 0, 'yaw': 0}
            print("🎮 RC Mode deactivated - discrete control restored")
    
    def calculate_rc_values(self, active_keys):
        """Calculate RC control values based on active keys"""
        import pygame
        
        # Base RC speed with speed multiplier
        base_speed = 50
        rc_speed = min(int(base_speed * self.speed_multiplier), 100)
        
        # Initialize values
        left_right = 0
        forward_back = 0
        up_down = 0
        yaw = 0
        
        # Calculate movement values based on active keys
        if pygame.K_a in active_keys:  # Left
            left_right -= rc_speed
        if pygame.K_d in active_keys:  # Right
            left_right += rc_speed
        if pygame.K_w in active_keys:  # Forward
            forward_back += rc_speed
        if pygame.K_s in active_keys:  # Back
            forward_back -= rc_speed
        if pygame.K_i in active_keys:  # Up
            up_down += rc_speed
        if pygame.K_k in active_keys:  # Down
            up_down -= rc_speed
        if pygame.K_q in active_keys:  # Rotate left
            yaw -= rc_speed
        if pygame.K_e in active_keys:  # Rotate right
            yaw += rc_speed
        
        return {
            'left_right': left_right,
            'forward_back': forward_back,
            'up_down': up_down,
            'yaw': yaw
        }
    
    def update_rc_control(self, active_keys):
        """Update RC control based on currently active keys"""
        print(f"🎮 update_rc_control called - rc_mode_active: {self.rc_mode_active}, active_keys: {len(active_keys)}")
        if not self.rc_mode_active or not self.tello or self.connection_status != ConnectionStatus.CONNECTED:
            print(f"🎮 RC control skipped - mode: {self.rc_mode_active}, tello: {self.tello is not None}, status: {self.connection_status}")
            return
        
        # Calculate new RC values
        new_values = self.calculate_rc_values(active_keys)
        
        # Only send command if values have changed or if we need to maintain movement
        if new_values != self.current_rc_values:
            self.current_rc_values = new_values
            
            try:
                self.tello.send_rc_control(
                    new_values['left_right'],
                    new_values['forward_back'],
                    new_values['up_down'],
                    new_values['yaw']
                )
                
                # Debug output for active movements
                active_movements = []
                if new_values['left_right'] != 0:
                    active_movements.append(f"LR:{new_values['left_right']}")
                if new_values['forward_back'] != 0:
                    active_movements.append(f"FB:{new_values['forward_back']}")
                if new_values['up_down'] != 0:
                    active_movements.append(f"UD:{new_values['up_down']}")
                if new_values['yaw'] != 0:
                    active_movements.append(f"YAW:{new_values['yaw']}")
                
                if active_movements:
                    speed_indicator = "🚀" if self.speed_multiplier > 1.0 else "🎮"
                    print(f"{speed_indicator} RC: {' '.join(active_movements)}")
                
            except Exception as e:
                print(f"RC control failed: {e}")
