from abc import abstractmethod
from time import sleep
from threading import Thread, Lock

from event import *


class Effect(Thread):

    FADER_SPEED = 2

    def __init__(self, driver, event, apc=None, timeout=None):
        Thread.__init__(self)
        self.lock = Lock()
        self.stop = False
        self.driver = driver
        self.apc = apc
        self.timeout = timeout
        self.event = event

        self.colors = event.color_values
        self.color_index = 0
        self._speed = event.fader_values[self.FADER_SPEED]
        self._direction = DirectionEvent.OUTWARD

    def exit(self):
        self.stop = True

    def accept_event(self, event):
        if isinstance(event, SpeedEvent):
            self.lock.acquire()
            self._speed = event.speed
            self.lock.release()
            return

        if isinstance(event, DirectionEvent):
            self.lock.acquire()
            self._direction = event.direction
            self.lock.release()
            return

    def get_next_color(self):
        new_color  = self.colors[self.color_index][:3]
        self.color_index = (self.color_index + 1) % len(self.colors)
        return new_color

    @property
    def speed(self):
        self.lock.acquire()
        speed = self._speed
        self.lock.release()
        return speed

    @property
    def direction(self):
        self.lock.acquire()
        direction = self._direction
        self.lock.release()
        return direction

    @abstractmethod
    def run(self):
        pass
