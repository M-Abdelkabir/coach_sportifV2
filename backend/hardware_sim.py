"""
Hardware simulation for laptop testing.
Simulates HR sensor (MAX30102), IMU, battery, and calorie counter.
"""
import random
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class HardwareState:
    """Current state of simulated hardware sensors."""
    # Heart rate (MAX30102 simulation)
    heart_rate: int = 75
    hr_trend: float = 0  # Trend direction for realistic simulation
    hr_warning: bool = False
    
    # IMU simulation
    imu_acceleration: tuple = (0.0, 0.0, 9.8)  # x, y, z in m/s²
    imu_gyroscope: tuple = (0.0, 0.0, 0.0)  # x, y, z in deg/s
    tremor_detected: bool = False
    tremor_intensity: float = 0.0
    
    # Battery simulation
    battery_level: int = 100
    battery_drain_rate: float = 0.1  # % per minute during workout
    eco_mode: bool = False
    
    # Calories & hydration
    calories_burned: float = 0.0
    water_glasses_equivalent: float = 0.0  # ~8 calories = 1 glass of water saved
    
    # Actuators simulation
    camera_pan: float = 0.0  # -90 to 90 degrees
    
    # Session timing
    session_start: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)


class HardwareSimulator:
    """
    Simulates hardware sensors for laptop testing.
    On Raspberry Pi, this would interface with real GPIO/I2C sensors.
    """
    
    def __init__(self):
        """Initialize the hardware simulator."""
        self.state = HardwareState()
        self._exercise_intensity = 0.5  # 0.0 to 1.0
        self._is_exercising = False
        print("[HW-SIM] Hardware simulator initialized")
    
    def start_session(self):
        """Start a workout session."""
        self.state.session_start = time.time()
        self.state.last_update = time.time()
        self.state.calories_burned = 0.0
        self._is_exercising = True
        print("[HW-SIM] Session started")
    
    def stop_session(self):
        """Stop the workout session."""
        self._is_exercising = False
        print(f"[HW-SIM] Session stopped. Calories: {self.state.calories_burned:.1f}")
    
    def set_exercise_intensity(self, intensity: float):
        """
        Set current exercise intensity (affects HR and calorie burn).
        
        Args:
            intensity: 0.0 (rest) to 1.0 (max effort)
        """
        self._exercise_intensity = max(0.0, min(1.0, intensity))
    
    def update(self) -> Dict[str, Any]:
        """
        Update all simulated sensor values.
        Call this periodically (e.g., every 500ms).
        
        Returns:
            Dictionary with current sensor values and warnings
        """
        current_time = time.time()
        dt = current_time - self.state.last_update
        self.state.last_update = current_time
        
        # Update heart rate
        self._update_heart_rate(dt)
        
        # Update IMU
        self._update_imu()
        
        # Update battery
        self._update_battery(dt)
        
        # Update calories
        if self._is_exercising:
            self._update_calories(dt)
        
        return self.get_status()
    
    def _update_heart_rate(self, dt: float):
        """Simulate realistic heart rate changes."""
        # Target HR based on exercise intensity
        # Resting: 60-80, Light: 100-120, Moderate: 120-150, Intense: 150-180
        base_hr = 70
        max_hr = 180
        target_hr = base_hr + (max_hr - base_hr) * self._exercise_intensity
        
        # Smooth transition with some noise
        hr_diff = target_hr - self.state.heart_rate
        self.state.hr_trend = hr_diff * 0.1  # Gradual change
        
        # Add realistic variability
        noise = random.gauss(0, 2)
        new_hr = self.state.heart_rate + self.state.hr_trend * dt + noise
        
        # Clamp to realistic range
        self.state.heart_rate = int(max(50, min(200, new_hr)))
        
        # Check for warning
        self.state.hr_warning = self.state.heart_rate > 170
        
        if self.state.heart_rate > 180:
            print(f"[HW-SIM] ⚠️ HR WARNING: {self.state.heart_rate} BPM - Exercise should pause!")
    
    def _update_imu(self):
        """Simulate IMU readings for tremor detection."""
        # Base acceleration (gravity)
        base_accel = (0.0, 0.0, 9.8)
        
        # Add movement noise based on exercise intensity
        noise_scale = 0.5 + self._exercise_intensity * 2.0
        accel_noise = (
            random.gauss(0, noise_scale),
            random.gauss(0, noise_scale),
            random.gauss(0, noise_scale * 0.5)
        )
        
        self.state.imu_acceleration = (
            base_accel[0] + accel_noise[0],
            base_accel[1] + accel_noise[1],
            base_accel[2] + accel_noise[2]
        )
        
        # Gyroscope (rotation rates)
        gyro_noise_scale = 5 + self._exercise_intensity * 20
        self.state.imu_gyroscope = (
            random.gauss(0, gyro_noise_scale),
            random.gauss(0, gyro_noise_scale),
            random.gauss(0, gyro_noise_scale * 0.5)
        )
        
        # Detect tremor (high frequency small movements indicate fatigue)
        accel_magnitude = sum(a**2 for a in accel_noise) ** 0.5
        gyro_magnitude = sum(g**2 for g in self.state.imu_gyroscope) ** 0.5
        
        # Tremor threshold increases with intensity (more movement expected)
        tremor_threshold = 2.0 + self._exercise_intensity * 3.0
        
        # Random fatigue-induced tremor chance (reduced for better UX during testing)
        fatigue_factor = self._exercise_intensity * 0.02
        is_tremoring = (
            accel_magnitude > tremor_threshold * 2.0 and 
            random.random() < fatigue_factor
        )
        
        self.state.tremor_detected = is_tremoring
        self.state.tremor_intensity = accel_magnitude if is_tremoring else 0.0
        
        if is_tremoring:
            print(f"[HW-SIM] 🫨 Tremor detected! Intensity: {accel_magnitude:.2f}")
    
    def _update_battery(self, dt: float):
        """Simulate battery drain."""
        if self._is_exercising:
            # Higher drain during exercise
            drain = self.state.battery_drain_rate * (1 + self._exercise_intensity) * (dt / 60)
            self.state.battery_level = max(0, self.state.battery_level - drain)
        
        # Eco mode activation
        old_eco = self.state.eco_mode
        self.state.eco_mode = self.state.battery_level < 20
        
        if self.state.eco_mode and not old_eco:
            print(f"[HW-SIM] 🔋 ECO MODE ACTIVATED - Battery: {self.state.battery_level:.0f}%")
    
    def _update_calories(self, dt: float):
        """Calculate calories burned based on exercise intensity and duration."""
        # MET (Metabolic Equivalent of Task) estimation
        # Resting: 1, Light: 3, Moderate: 5, Vigorous: 8
        met = 1 + self._exercise_intensity * 7
        
        # Calories per minute (assuming 70kg person)
        # Formula: Calories/min = MET × 3.5 × weight(kg) / 200
        weight_kg = 70
        calories_per_min = met * 3.5 * weight_kg / 200
        
        # Add HR-based adjustment
        hr_factor = 1 + (self.state.heart_rate - 70) / 200
        calories_per_min *= hr_factor
        
        # Calculate for this time interval
        calories_delta = calories_per_min * (dt / 60)
        self.state.calories_burned += calories_delta
        
        # Water glass equivalent (1 glass ≈ 8 oz of water, saves ~8 calories worth of sugary drink)
        self.state.water_glasses_equivalent = self.state.calories_burned / 100  # Simplified
    
    def get_status(self) -> Dict[str, Any]:
        """Get current hardware status as dictionary."""
        session_duration = time.time() - self.state.session_start if self._is_exercising else 0
        
        return {
            "heart_rate": self.state.heart_rate,
            "heart_rate_warning": self.state.hr_warning,
            "imu_tremor_detected": self.state.tremor_detected,
            "imu_tremor_intensity": round(self.state.tremor_intensity, 2),
            "battery_level": round(self.state.battery_level),
            "eco_mode": self.state.eco_mode,
            "calories_burned": round(self.state.calories_burned, 1),
            "water_glasses_saved": round(self.state.water_glasses_equivalent, 1),
            "session_duration_seconds": int(session_duration),
            "is_exercising": self._is_exercising,
            "camera_pan": round(self.state.camera_pan, 1)
        }
    
    def should_pause_exercise(self) -> tuple[bool, Optional[str]]:
        """
        Check if exercise should be paused for safety.
        
        Returns:
            Tuple of (should_pause, reason_message)
        """
        if self.state.heart_rate > 180:
            return True, "Pouls trop élevé! Fais une pause et respire profondément."
        
        if self.state.tremor_detected and self.state.tremor_intensity > 3.0:
            return True, "Tremblements détectés. Repose-toi un moment."
        
        if self.state.battery_level < 5:
            return True, "Batterie critique! Branche l'appareil."
        
        return False, None
    
    def get_eco_recommendations(self) -> Dict[str, Any]:
        """
        Get eco mode recommendations to save battery.
        
        Returns:
            Dictionary with recommended settings
        """
        if not self.state.eco_mode:
            return {"active": False}
        
        return {
            "active": True,
            "fps_target": 15,  # Reduce from 30 to 15 FPS
            "feedback_mode": "minimal",  # Reduce TTS frequency
            "led_brightness": 50,  # Reduce LED brightness
            "message": f"Mode économie activé. Batterie: {self.state.battery_level:.0f}%"
        }
    
    def get_calorie_message(self) -> str:
        """Generate motivational calorie message."""
        calories = self.state.calories_burned
        glasses = self.state.water_glasses_equivalent
        
        if calories < 50:
            return f"Tu as brûlé {calories:.0f} calories. Continue!"
        elif calories < 150:
            return f"Super! {calories:.0f} calories brûlées, c'est équivalent à {glasses:.1f} verres de soda évités!"
        elif calories < 300:
            return f"Excellent! {calories:.0f} calories! Tu as économisé l'équivalent de {glasses:.1f} boissons sucrées!"
        else:
            return f"Incroyable! {calories:.0f} calories brûlées! C'est comme {glasses:.1f} verres de soda évités!"

    def set_pan(self, angle: float):
        """Simulate setting camera pan angle."""
        self.state.camera_pan = max(-90, min(90, angle))
        # print(f"[HW-SIM] Camera pan adjusted to: {self.state.camera_pan:.1f}°")


# Global hardware simulator instance
_hw_simulator: Optional[HardwareSimulator] = None


def get_hardware_simulator() -> HardwareSimulator:
    """Get or create the global hardware simulator."""
    global _hw_simulator
    if _hw_simulator is None:
        _hw_simulator = HardwareSimulator()
    return _hw_simulator
