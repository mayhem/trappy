from abc import abstractmethod
from time import sleep
from threading import Thread

class EffectEvent:

    def __init__(self, effect, float_values=None, color_values=None):
        # Which control is sending this message?
        self.effect = effect
        self.float_values = float_values
        self.color_values = color_values

    @property
    def floats(self):
        return self.float_values

    @property
    def colors(self):
        return self.color_values

class SpeedEvent:

    def __init__(self, speed):
        self.speed = speed


class Effect(Thread):

    def __init__(self, driver, event, apc=None, timeout=None):
        Thread.__init__(self)
        self.stop = False
        self.driver = driver
        self.apc = apc
        self.timeout = timeout
        self.event = event

        # list controls and colors required for this effect to work. In order to start an effect, each of the
        # controls must send an INIT message, so the Control object can be set.
        self.speed_control = None

    def exit(self):
        self.stop = True

    def accept_event(self, event):
        pass

    @abstractmethod
    def run(self):
        pass
