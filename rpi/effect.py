from abc import abstractmethod
from time import sleep
from threading import Thread, Lock
from queue import Queue

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

        self.instant_color_queue = Queue()

    def exit(self):
        self.stop = True
        self.join()

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

        if isinstance(event, InstantColorEvent):
            self.lock.acquire()
            self.instant_color_queue.put(event.color)
            self.lock.release()
            return

    def get_next_color(self):
        if self.instant_color_queue.qsize() > 0:
            self.colors[self.color_index] = self.instant_color_queue.get()

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
