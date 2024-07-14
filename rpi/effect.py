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


class Effect(Thread):

    def __init__(self, driver, timeout=None):
        Thread.__init__(self)
        self.stop = False
        self.driver = driver
        self.timeout = timeout

        # list controls and colors required for this effect to work. In order to start an effect, each of the
        # controls must send an INIT message, so the Control object can be set.
        self.speed_control = None

    def exit(self):
        self.stop = True

    @abstractmethod
    def run(self):
        pass
