"""
Real hardware control for Raspberry Pi 5.
Controls RGB LEDs and Buzzer via GPIO.
"""
import time
import threading
from typing import Optional

# Attempt to import gpiozero (recommended for RPi)
try:
    from gpiozero import RGBLED, Buzzer, AngularServo
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

class PiHardwareController:
    """
    Controls physical hardware on Raspberry Pi 5.
    RGB LED pins: Red=17, Green=27, Blue=22
    Buzzer pin: 23
    """
    
    def __init__(self, red_pin=17, green_pin=27, blue_pin=22, buzzer_pin=23, servo_pin=18):
        self.enabled = GPIO_AVAILABLE
        self.led = None
        self.buzzer = None
        self.servo = None
        self.current_pan = 0  # Center
        
        if self.enabled:
            try:
                self.led = RGBLED(red=red_pin, green=green_pin, blue=blue_pin)
                self.buzzer = Buzzer(buzzer_pin)
                # AngularServo: initial_angle=0, min_angle=-90, max_angle=90
                # min_pulse_width and max_pulse_width might need adjustment depending on the servo
                self.servo = AngularServo(servo_pin, initial_angle=0, min_angle=-90, max_angle=90)
                print(f"[PI-HW] Hardware initialized: LED({red_pin},{green_pin},{blue_pin}), Buzzer({buzzer_pin}), Servo({servo_pin})")
            except Exception as e:
                print(f"[PI-HW] Failed to initialize GPIO: {e}")
                self.enabled = False
        else:
            print("[PI-HW] GPIO libraries not found. Running in simulation mode.")

    def set_led(self, color: str, action: str = "on"):
        """
        Set RGB LED color and action.
        Colors: red, green, blue, yellow, orange, white, off
        Actions: on, off, blink
        """
        if not self.enabled or not self.led:
            return

        # Define colors (R, G, B) normalized 0-1
        colors = {
            "red": (1, 0, 0),
            "green": (0, 1, 0),
            "blue": (0, 0, 1),
            "yellow": (1, 1, 0),
            "orange": (1, 0.5, 0),
            "white": (1, 1, 1),
            "off": (0, 0, 0)
        }
        
        rgb = colors.get(color.lower(), (0, 0, 0))
        
        if action == "off" or color == "off":
            self.led.off()
        elif action == "blink":
            self.led.blink(on_color=rgb, n=3)
        else:
            self.led.color = rgb

    def play_buzzer(self, pattern: str = "beep", duration_ms: int = 100):
        """
        Play a pattern on the buzzer.
        """
        if not self.enabled or not self.buzzer:
            return

        if pattern == "beep":
            self.buzzer.beep(on_time=duration_ms/1000, n=1)
        elif pattern == "double":
            self.buzzer.beep(on_time=0.1, off_time=0.1, n=2)
        elif pattern == "long":
            self.buzzer.beep(on_time=0.5, n=1)
        elif pattern == "success":
            # Simple success sequence
            def sequence():
                self.buzzer.on()
                time.sleep(0.1)
                self.buzzer.off()
                time.sleep(0.05)
                self.buzzer.on()
                time.sleep(0.2)
                self.buzzer.off()
            threading.Thread(target=sequence, daemon=True).start()
        elif pattern == "error":
            self.buzzer.beep(on_time=0.5, n=1)

    def set_pan(self, angle: float):
        """
        Set camera pan angle (-90 to 90).
        """
        if not self.enabled or not self.servo:
            return
            
        # Clamp angle
        angle = max(-90, min(90, angle))
        self.servo.angle = angle
        self.current_pan = angle

# Global instance
_pi_controller: Optional[PiHardwareController] = None

def get_pi_controller() -> PiHardwareController:
    global _pi_controller
    if _pi_controller is None:
        _pi_controller = PiHardwareController()
    return _pi_controller
