#!/usr/bin/env python3
"""
Hardware Diagnostic Tool for Virtual Sports Coach
Tests the LEDs, Buzzer, and Servo Motor on Raspberry Pi.
"""
import time
import sys

try:
    from gpiozero import RGBLED, Buzzer, AngularServo
    from gpiozero.pins.lgpio import LPiFactory
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

# Configuration (Matches hardware_pi.py and HARDWARE_CONFIG.md)
RED_PIN = 17
GREEN_PIN = 27
BLUE_PIN = 22
BUZZER_PIN = 23
SERVO_PIN = 18

def test_leds():
    print("\n--- Testing RGB LED ---")
    try:
        led = RGBLED(red=RED_PIN, green=GREEN_PIN, blue=BLUE_PIN)
        
        print("Blinking RED...")
        led.color = (1, 0, 0)
        time.sleep(1)
        
        print("Blinking GREEN...")
        led.color = (0, 1, 0)
        time.sleep(1)
        
        print("Blinking BLUE...")
        led.color = (0, 0, 1)
        time.sleep(1)
        
        print("Blinking WHITE...")
        led.color = (1, 1, 1)
        time.sleep(1)
        
        led.off()
        print("LED Test Complete.")
    except Exception as e:
        print(f"LED Test Failed: {e}")

def test_buzzer():
    print("\n--- Testing Buzzer ---")
    try:
        bz = Buzzer(BUZZER_PIN)
        print("Beeping 3 times...")
        for _ in range(3):
            bz.on()
            time.sleep(0.1)
            bz.off()
            time.sleep(0.1)
        print("Buzzer Test Complete.")
    except Exception as e:
        print(f"Buzzer Test Failed: {e}")

def test_servo():
    print("\n--- Testing Servo Motor ---")
    try:
        # Note: Pulse width may need adjustment for specific servos
        servo = AngularServo(SERVO_PIN, initial_angle=0, min_angle=-90, max_angle=90)
        
        print("Moving to -90°...")
        servo.angle = -90
        time.sleep(1.5)
        
        print("Moving to +90°...")
        servo.angle = 90
        time.sleep(1.5)
        
        print("Returning to 0° (Center)...")
        servo.angle = 0
        time.sleep(1)
        
        print("Servo Test Complete.")
    except Exception as e:
        print(f"Servo Test Failed: {e}")

def main():
    print("========================================")
    print("  Hardware Diagnostic - Sports Coach    ")
    print("========================================")
    
    if not GPIO_AVAILABLE:
        print("\nERROR: gpiozero not found!")
        print("Please run: pip install gpiozero lgpio")
        sys.exit(1)
        
    print(f"Configuration:")
    print(f"- RGB LED Pins: R:{RED_PIN}, G:{GREEN_PIN}, B:{BLUE_PIN}")
    print(f"- Buzzer Pin: {BUZZER_PIN}")
    print(f"- Servo Pin: {SERVO_PIN}")
    
    input("\nPress Enter to start LED test...")
    test_leds()
    
    input("\nPress Enter to start Buzzer test...")
    test_buzzer()
    
    input("\nPress Enter to start Servo test...")
    test_servo()
    
    print("\n========================================")
    print("      Diagnostic Completed!             ")
    print("========================================")

if __name__ == "__main__":
    main()
