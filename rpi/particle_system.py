from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color

class Particle:

    STRIP_ALL = -1
    def __init__(self, t, strip, position, velocity, sprite_pattern):
        """ strip can be a strip number, STRIP_ALL or a list of strips """
        self.t = t
        self.strip = strip
        self.position = position  # Initial position -- we're not tracking current position
        self.velocity = velocity
        self.sprite_pattern = sprite_pattern


class EffectParticleSystem(Effect):

    FADER_SPEED = 2
    FADER_COUNT = 3
    MAX_PARTICLE_COUNT = 4

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self._particle_count = self._map_count_value(event.fader_values[self.FADER_COUNT])
        self.particles = []

    @property
    def particle_count(self):
        self.lock.acquire()
        count = self._particle_count
        self.lock.release()
        return int(count)

    def _map_count_value(self, value):
        # scale to MAX_PARTICLE_COUNT
        return value * self.MAX_PARTICLE_COUNT

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def accept_event(self, event):
        super().accept_event(event)
        if isinstance(event, FaderEvent):
            if event.fader == self.FADER_COUNT:
                self.lock.acquire()
                self._particle_count = self._map_count_value(event.value)
                self.lock.release()
            return

    def render_leds(self, t, background_color=(0,0,0)):

        led_data = [ list(background_color) for x in range(self.driver.strips * self.driver.leds) ]

        still_alive = []
        for p in self.particles:
            strips = [ p.strip ] if isinstance(p.strip, int) else p.strip
            assert isinstance(strips, list)

            if strips == [ Particle.STRIP_ALL ]:
                strips = list(range(self.driver.strips))

            is_alive = True
            for s in strips:
                pos = p.velocity * (t - p.t) + p.position
                if pos >= self.driver.leds:
                    is_alive = False
                else:
                    led_data[(s * self.driver.leds) + pos] = self.get_next_color()

            if is_alive:
                still_alive.append(p)

        self.particles = still_alive

        return led_data

    def run(self):

        t = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            speed = self.speed
            if speed == 0:
                sleep(.01)
                continue

            max_count = self.particle_count
            for i in range(max_count):
                velocity = 1 + randint(2, 6)
                self.particles.append(Particle(t, Particle.STRIP_ALL, 0, velocity, 0))

            self.driver.set(self.render_leds(t))
            t += self.direction 

            max_delay = .1
            delay = (1.0 - speed) * max_delay
            sleep(delay)
