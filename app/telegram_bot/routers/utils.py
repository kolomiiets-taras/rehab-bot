def validate_pulse(pulse: str) -> bool:
    """Validate if the pulse is an integer between 30 and 220."""
    try:
        pulse_value = int(pulse)
        return 30 <= pulse_value <= 220
    except ValueError:
        return False
