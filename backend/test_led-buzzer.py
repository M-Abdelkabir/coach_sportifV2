from hardware_manager import get_hardware_manager
hw = get_hardware_manager()
hw.set_led("green", "blink")
hw.play_buzzer("success")