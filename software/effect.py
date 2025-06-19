from abc import abstractmethod
from time import sleep
from threading import Thread, Lock
from queue import Queue

from event import *
from config import PROFILE


class Effect(Thread):

    FADER_BRIGHTNESS = 2
    FADER_SPEED = 3
    VARIANTS = 1
    SLUG = "__base"

    def __init__(self, driver, event, apc=None, timeout=None):
        Thread.__init__(self)
        self.lock = Lock()
        self.stop = False
        self.driver = driver
        self.apc = apc
        self.timeout = timeout
        self.event = event
        self.variant = event.variant

        self.colors = event.color_values
        self.color_index = 0
        self._speed = event.fader_values[self.FADER_SPEED]
        self._direction = DirectionEvent.OUTWARD
        self.faders = []
        for fader, value in enumerate(event.fader_values):
            self.faders.append(self.map_fader_value(fader, value))

        self.instant_color_queue = Queue()
        self.max_delay = .1
        self.min_delay = 0.0

    def exit(self):
        self.stop = True
        self.join()

    def set_sleep_params(self, min_delay, max_delay):
        if min_delay < 0 or min_delay > max_delay or max_delay < 0:
            return

        self.min_delay = min_delay
        self.max_delay = max_delay

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

        if isinstance(event, EffectVariantEvent):
            self.lock.acquire()
            self.variant = event.variant
            self.lock.release()
            return

    def get_active_faders(self):
        """ return a list of integer values that indicate which faders are active for this effect """
        return []

    def fader_value(self, fader):
        self.lock.acquire()
        value = self.faders[fader]
        self.lock.release()
        return value    

    def map_fader_value(self, fader, value):
        """ Can be overridden in derived class to provide a mapping function for a fader """
        return None

    def get_instant_color(self):
        if self.instant_color_queue.qsize() > 0:
            return self.instant_color_queue.get()
        return None

    def get_next_color(self, ignore_odd_colors=False):
        if self.instant_color_queue.qsize() > 0:
            self.colors[self.color_index] = self.instant_color_queue.get()

        new_color  = self.colors[self.color_index][:3]

        if ignore_odd_colors:
            num_colors = len(self.colors)
            if num_colors % 2 == 1:
                num_colors -= 1 
            self.color_index = (self.color_index + 1) % num_colors
        else:
            self.color_index = (self.color_index + 1) % len(self.colors)

        return list(new_color)

    def get_num_variants(self):
        return self.VARIANTS

    def set_current_variant(self, variant):
        self.lock.acquire()
        self.variant = variant
        self.lock.release()

    def get_current_variant(self):
        self.lock.acquire()
        v = self.variant
        self.lock.release()
        return v

    def sleep(self, partial=None):
        """ Partial is used to break a sleep cycle into a partial number of cycles """
        if PROFILE:
            return

        while True:
            speed = self.speed
            if speed == 0:
                if not PROFILE:
                    sleep(.01)
                continue

            break

        delay = (self.min_delay + ((self.max_delay - self.min_delay) * (1.0 - speed)))
        if partial is not None:
            delay /= partial
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
