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
        self.faders = []
        for fader, value in enumerate(event.fader_values):
            self.faders.append(self.map_fader_value(fader, value))

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

        if isinstance(event, FaderEvent):
            self.lock.acquire()
            self.faders[event.fader] = self.map_fader_value(event.fader, event.value)
            self.lock.release()
            return

    def fader_value(self, fader):
        self.lock.acquire()
        value = self.faders[fader]
        self.lock.release()
        return value    

    def map_fader_value(self, fader, value):
        """ Can be overridden in derived class to provide a mapping function for a fader """
        return None

    def get_next_color(self):
        if self.instant_color_queue.qsize() > 0:
            self.colors[self.color_index] = self.instant_color_queue.get()

        new_color  = self.colors[self.color_index][:3]
        self.color_index = (self.color_index + 1) % len(self.colors)
        return list(new_color)

    def sleep(self):
        while True:
            speed = self.speed
            if speed == 0:
                sleep(.01)
                continue

            break

        max_delay = .1
        delay = (1.0 - speed) * max_delay
        sleep(delay)

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
