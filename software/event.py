class EffectEvent:

    def __init__(self, effect, variant = 0, float_values=None, color_values=None, fader_values=None):
        # Which control is sending this message?
        self.effect = effect
        self.variant = variant
        self.float_values = float_values
        self.color_values = color_values
        self.fader_values = fader_values

    @property
    def floats(self):
        return self.float_values

    @property
    def colors(self):
        return self.color_values

class SpeedEvent:
    def __init__(self, speed):
        self.speed = speed

class BrightnessEvent:
    def __init__(self, brightness):
        self.brightness = brightness

class DirectionEvent:
    INWARD = -1
    OUTWARD = 1
    def __init__(self, direction):
        self.direction = direction

class GammaEvent:
    def __init__(self, gamma):
        self.gamma = gamma

class FaderEvent:
    def __init__(self, fader, value):
        self.fader = fader
        self.value = value

class InstantColorEvent:
    def __init__(self, color):
        self.color = color

class EffectVariantEvent:
    def __init__(self, variant):
        self.variant = variant
