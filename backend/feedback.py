"""
Text-to-Speech and multimodal feedback system.
Uses pyttsx3 for offline TTS on laptop.
"""
import pyttsx3
import threading
from typing import Optional
from queue import Queue
import os
import platform
from hardware_manager import get_hardware_manager
import time


class FeedbackEngine:
    """
    Multimodal feedback system for the virtual coach.
    Handles text, voice, LED simulation, and buzzer simulation.
    """
    
    def __init__(self):
        """Initialize the feedback engine with TTS."""
        self._tts_queue: Queue = Queue()
        self._tts_thread: Optional[threading.Thread] = None
        self._tts_running = False
        self._engine: Optional[pyttsx3.Engine] = None
        self._ws_voice_queue: Queue = Queue() # For WebSocket broadcasting
        self._init_tts()
        
    def _init_tts(self):
        """Start the TTS worker thread."""
        self._tts_running = True
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()
        print("[TTS] Worker thread started")
    
    def _tts_worker(self):
        """Background worker thread for TTS to avoid blocking."""
        # Initialize the engine inside the thread (Required for SAPI5 on Windows)
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 150)
            self._engine.setProperty('volume', 0.9)
            
            voices = self._engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                    self._engine.setProperty('voice', voice.id)
                    break
            print("[TTS] Engine initialized in background thread")
        except Exception as e:
            print(f"[TTS] Threaded initialization failed: {e}")
            self._engine = None

        while self._tts_running:
            try:
                text = self._tts_queue.get(timeout=0.5)
                if text and self._engine:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception:
                pass 
    
    def speak(self, text: str, priority: bool = False):
        """
        Add text to speech queue.
        
        Args:
            text: Text to speak
            priority: If True, clear queue and speak immediately
        """
        if not self._engine:
            print(f"[TTS-FALLBACK] {text}")
            return
            
        if priority:
            # Clear the queue for priority messages
            while not self._tts_queue.empty():
                try:
                    self._tts_queue.get_nowait()
                except:
                    break
        
        self._tts_queue.put(text)
        self._ws_voice_queue.put(text)
        print(f"[TTS] Queued: {text}")

    def get_ws_messages(self) -> list:
        """Get and clear the queue of messages to send via WebSocket."""
        messages = []
        while not self._ws_voice_queue.empty():
            try:
                messages.append(self._ws_voice_queue.get_nowait())
            except:
                break
        return messages
    
    def led(self, color: str, action: str = "on"):
        """
        Simulate LED feedback (print on laptop).
        
        Args:
            color: LED color (green, red, blue, yellow, orange)
            action: "on", "off", or "blink"
        """
        emoji = {
            "green": "🟢",
            "red": "🔴",
            "blue": "🔵",
            "yellow": "🟡",
            "orange": "🟠",
        }.get(color.lower(), "⚪")
        
        print(f"[LED] {emoji} {color.upper()} → {action}")
        
        # Real Pi hardware control
        get_hardware_manager().set_led(color, action)
        
        return {"color": color, "action": action}
    
    def buzzer(self, pattern: str = "beep", duration_ms: int = 100):
        """
        Simulate buzzer feedback (print on laptop).
        
        Args:
            pattern: "beep", "double", "long", "alarm"
            duration_ms: Duration in milliseconds
        """
        patterns = {
            "beep": "🔔 BEEP",
            "double": "🔔🔔 BEEP-BEEP",
            "long": "🔔━━━ BEEEEP",
            "alarm": "🚨 ALARM!",
            "success": "🎵 ding-ding!",
            "error": "🔊 BUZZ!"
        }
        
        sound = patterns.get(pattern, f"🔔 {pattern}")
        print(f"[BUZZER] {sound} ({duration_ms}ms)")
        
        # Real Pi hardware control
        get_hardware_manager().play_buzzer(pattern, duration_ms)
        
        return {"pattern": pattern, "duration_ms": duration_ms}
    
    def posture_feedback(self, status: str, message: str):
        """
        Send posture feedback with appropriate modality.
        
        Args:
            status: "perfect", "warning", "error"
            message: Feedback message text
        """
        result = {
            "status": status,
            "message": message,
            "led": None,
            "buzzer": None,
            "voice": False
        }
        
        if status == "perfect":
            result["led"] = self.led("green")
            # Only speak occasionally for perfect posture
        elif status == "warning":
            result["led"] = self.led("yellow", "blink")
            result["buzzer"] = self.buzzer("beep")
            self.speak(message)
            result["voice"] = True
        elif status == "error":
            result["led"] = self.led("red", "blink")
            result["buzzer"] = self.buzzer("double")
            self.speak(message, priority=True)
            result["voice"] = True
        
        return result
    
    def rep_feedback(self, rep_count: int, target_reps: int, exercise: str):
        """
        Provide encouragement based on rep progress.
        
        Args:
            rep_count: Current rep count
            target_reps: Target number of reps
            exercise: Exercise name
        """
        remaining = target_reps - rep_count
        
        # Milestone feedback
        if rep_count == 1:
            self.speak(f"Let's go for {exercise}!")
            self.led("green")
        elif remaining == 5:
            self.speak("Come on, 5 more!")
            self.buzzer("beep")
        elif remaining == 3:
            self.speak("Only 3 left!")
        elif remaining == 1:
            self.speak("Last one!")
            self.led("blue", "blink")
        elif remaining == 0:
            self.speak("Perfect! Set complete!")
            self.buzzer("success")
            self.led("green", "blink")
    
    def fatigue_warning(self, slowdown_percent: float):
        """
        Warn user about fatigue detection.
        
        Args:
            slowdown_percent: Percentage of speed reduction detected
        """
        if slowdown_percent > 30:
            self.speak("Watch out! You're slowing down a lot. Take a break if needed.", priority=True)
            self.led("orange", "blink")
            self.buzzer("alarm")
        elif slowdown_percent > 20:
            self.speak("Slow down, breathe!")
            self.led("yellow")
            self.buzzer("double")
    
    def exercise_transition(self, next_exercise: str, rest_seconds: int):
        """
        Announce transition to next exercise.
        
        Args:
            next_exercise: Name of the next exercise
            rest_seconds: Rest duration in seconds
        """
        self.speak(f"Rest for {rest_seconds} seconds. Next exercise: {next_exercise}. Ready?")
        self.led("blue")
    
    def session_complete(self, total_reps: int, calories: float, duration_minutes: int):
        """
        Announce session completion.
        
        Args:
            total_reps: Total reps completed
            calories: Estimated calories burned
            duration_minutes: Session duration in minutes
        """
        self.speak(
            f"Excellent work! You did {total_reps} repetitions "
            f"and burned about {int(calories)} calories in {duration_minutes} minutes!"
        )
        self.led("green", "blink")
        self.buzzer("success")
    
    def heart_rate_warning(self, bpm: int):
        """Warn about high heart rate."""
        if bpm > 180:
            self.speak("Warning! Your heart rate is very high. Stop and breathe!", priority=True)
            self.led("red", "blink")
            self.buzzer("alarm")
        elif bpm > 170:
            self.speak("High heart rate! Slow down a bit.")
            self.led("orange")
    
    def eco_mode_notification(self, battery_level: int):
        """Notify about eco mode activation."""
        self.speak(f"Battery at {battery_level} percent. Eco mode activated.")
        self.led("yellow")
    
    def shutdown(self):
        """Shutdown the TTS engine."""
        self._tts_running = False
        if self._tts_thread:
            self._tts_thread.join(timeout=1.0)
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
        print("[TTS] Engine shutdown")


# Global feedback engine instance
_feedback_engine: Optional[FeedbackEngine] = None


def get_feedback_engine() -> FeedbackEngine:
    """Get or create the global feedback engine."""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackEngine()
    return _feedback_engine


# ==================== Message Templates ====================

POSTURE_MESSAGES = {
    # Squat
    "squat_knee_wide": "Gardez les genoux alignés avec vos pieds !",
    "squat_back_round": "Dos droit ! Regardez devant vous.",
    "squat_depth": "Descendez plus bas, cuisses parallèles au sol.",
    "squat_perfect": "Parfait ! Continuez.",
    
    # Push-up
    "pushup_hips_high": "Baissez les hanches ! Gardez le corps aligné.",
    "pushup_hips_low": "Montez les hanches ! Vous cambrez trop.",
    "pushup_elbows_wide": "Gardez les coudes proches du corps.",
    "pushup_depth": "Descendez plus bas, poitrine vers le sol.",
    "pushup_perfect": "Excellente forme ! Continuez.",
    
    # Plank
    "plank_hips_high": "Baissez les hanches ! Corps bien droit.",
    "plank_hips_low": "Engagez les abdos ! Ne cambrez pas le dos.",
    "plank_head_down": "Regardez le sol, tête alignée.",
    "plank_perfect": "Position parfaite ! Tenez bon.",
    
    # Bicep curl
    "curl_elbow_move": "Gardez le coude fixe ! Seul l'avant-bras bouge.",
    "curl_swing": "Pas d'élan ! Contrôlez le mouvement.",
    "curl_perfect": "Bien ! Mouvement contrôlé.",
    
    # Lunge
    "lunge_depth": "Descendez plus bas sur vos fentes !",
    "lunge_torso_lean": "Gardez le buste droit !",
    
    # Tricep Dip
    "dip_uneven": "Gardez vos coudes symétriques !",
    
    # Row
    "row_back_round": "Dos droit ! Tirez les coudes en arrière.",
    
    # Crunch
    "crunch_neck_strain": "Ne tirez pas sur votre nuque !",
    "crunch_legs_moving": "Gardez les jambes stables !",
    
    # General
    "great_form": "Excellente forme !",
    "keep_going": "Allez, on continue !",
    "almost_there": "Presque fini !",
    "well_done": "Bien joué !",

    # Missing mappings
    "squat_knee_uneven": "Gardez vos genoux symétriques !",
    "press_arch_back": "Engagez les abdos, ne cambrez pas le dos !",
    "deadlift_back_round": "Dos plat ! Poitrine sortie et hanches en arrière.",
    "body_not_visible": "Reculez pour que votre corps soit entièrement visible !",
    
    # LSTM model labels (pushup/squat form quality)
    "pushup_correct": "Pompe parfaite ! Continuez.",
    "pushup_incorrect": "Corrigez votre forme de pompe !",
    "squat_correct": "Squat parfait !",
    "squat_shallow": "Descendez plus bas !",
    "squat_forward_lean": "Ne vous penchez pas en avant !",
    "squat_knee_caving": "Poussez les genoux vers l'extérieur !",
    "squat_heels_off": "Gardez les talons au sol !",
    "squat_asymmetric": "Gardez un mouvement symétrique !",
}
