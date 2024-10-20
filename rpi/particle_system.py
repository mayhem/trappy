from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color

class Particle:

    STRIP_ALL = -1
    def __init__(self, t, strip, color, position, velocity, sprite_pattern):
        """ strip can be a strip number, STRIP_ALL or a list of strips """
        self.t = t
        self.strip = strip
        self.color = color
        self.position = position  # Initial position -- we're not tracking current position
        self.velocity = velocity
        self.sprite_pattern = sprite_pattern


class EffectParticleSystem(Effect):

    FADER_COUNT = 4
    FADER_SPRITE = 5
    MAX_PARTICLE_COUNT = 8
    VARIANTS = 2

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []

    def get_active_faders(self):
        return [ self.FADER_COUNT, self.FADER_SPRITE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            # scale to MAX_PARTICLE_COUNT
            return value * (self.MAX_PARTICLE_COUNT-1) + 1

        if fader == self.FADER_SPRITE:
            return value * 254 + 1

        return None

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

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
                    color = self.get_next_color() if p.color is None else p.color
                    if p.sprite_pattern == 1:
                        led_data[(s * self.driver.leds) + pos] = color
                    else:
                        for i in range(8):
                            if p.sprite_pattern & (1 << i) != 0 and pos + i < self.driver.leds:
                                led_data[(s * self.driver.leds) + pos + i] = color

            if is_alive:
                still_alive.append(p)

        self.particles = still_alive

        return led_data

    def run(self):

        t = 0
        row = 0
        strip = 0
        strip_step = 1
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            count = int(self.fader_value(self.FADER_COUNT))
            sprite = int(self.fader_value(self.FADER_SPRITE))

            if self.variant == 0:
                if count == self.driver.strips:
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, Particle.STRIP_ALL, None, 0, velocity, sprite))
                else:
                    strips = [ x for x in range(self.driver.strips)]
                    shuffle(strips)
                    for s in strips[:count]:
                        velocity = 1 + randint(2, 6)
                        self.particles.append(Particle(t, s, self.get_next_color(), 0, velocity, sprite))
            else:
                # Use fader count in this!
                velocity = 2
                self.particles.append(Particle(t, strip, self.get_next_color(), 0, velocity, sprite))
                if strip == 7:
                    strip_step = -1
                if strip == 0:
                    strip_step = 1
                strip += strip_step

            self.driver.set(self.render_leds(t))
            t += self.direction 
            row += 1

            self.sleep()
