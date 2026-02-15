"""
Hardware Manager that switches between real Raspberry Pi hardware 
and a simulator based on availability and platform.
"""
import platform
import os
import time
from typing import Any, Dict, Optional

# Import controllers
from hardware_sim import get_hardware_simulator, HardwareSimulator
from hardware_pi import get_pi_controller, PiHardwareController

class HardwareManager:
    """
    Unified manager for hardware interactions.
    Handles sensors (HR, IMU) and actuators (LED, Buzzer).
    """
    
    def __init__(self):
        self.is_pi = False
        try:
            # Check if running on Raspberry Pi
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().lower()
                    if 'raspberry pi' in model:
                        self.is_pi = True
        except:
            self.is_pi = False
            
        self.sim = get_hardware_simulator()
        self.pi = get_pi_controller()
        
        # Use Pi if available, otherwise simulation
        self.use_real_hw = self.is_pi and self.pi.enabled
        
        if self.use_real_hw:
            print("[HW-MGR] Using REAL hardware (Raspberry Pi)")
        else:
            print("[HW-MGR] Using Hardware SIMULATOR")

    def start_session(self):
        """Start a workout session."""
        self.sim.start_session()
        if self.use_real_hw:
            self.pi.set_led("green", "blink")
            self.pi.play_buzzer("success")

    def stop_session(self):
        """Stop the workout session."""
        self.sim.stop_session()
        if self.use_real_hw:
            self.pi.set_led("off")
            self.pi.play_buzzer("long")

    def set_exercise_intensity(self, intensity: float):
        """Set exercise intensity for simulation/sensors."""
        self.sim.set_exercise_intensity(intensity)

    def update(self) -> Dict[str, Any]:
        """Update sensor values."""
        # Note: In a full "real" implementation, this would read from I2C
        # For now, we use the simulator values but controlled by the manager
        return self.sim.update()

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        status = self.sim.get_status()
        status["real_hardware"] = self.use_real_hw
        return status

    def should_pause_exercise(self) -> tuple[bool, Optional[str]]:
        """Safety checks."""
        return self.sim.should_pause_exercise()

    def set_led(self, color: str, action: str = "on"):
        """Control LED."""
        if self.use_real_hw:
            self.pi.set_led(color, action)
        else:
            # Log for simulation
            emoji = {"green": "🟢", "red": "🔴", "yellow": "🟡", "blue": "🔵"}.get(color.lower(), "⚪")
            print(f"[HW-MGR] SIM LED: {emoji} {color.upper()} -> {action}")

    def play_buzzer(self, pattern: str = "beep", duration_ms: int = 100):
        """Control Buzzer."""
        if self.use_real_hw:
            self.pi.play_buzzer(pattern, duration_ms)
        else:
            print(f"[HW-MGR] SIM BUZZER: {pattern} ({duration_ms}ms)")

    def set_camera_pan(self, angle: float):
        """Set camera pan angle."""
        self.sim.set_pan(angle)
        if self.use_real_hw:
            self.pi.set_pan(angle)
        else:
            # Throttle simulation logs to avoid clutter (reduced to 0.5s for better feedback)
            if hasattr(self, '_last_sim_pan_log') and time.time() - self._last_sim_pan_log < 0.5:
                return
            self._last_sim_pan_log = time.time()
            print(f"[HW-MGR] SIM CAMERA PAN: {angle:.1f}°")

# Global instance
_manager: Optional[HardwareManager] = None

def get_hardware_manager() -> HardwareManager:
    global _manager
    if _manager is None:
        _manager = HardwareManager()
    return _manager
