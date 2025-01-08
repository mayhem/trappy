from abc import abstractmethod
import itertools
from time import sleep, monotonic

from particle_system import Particle, ParticleSystem
from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent


class EffectChasingDots(ParticleSystem):

    FADER_COUNT = 2
    FADER_SPRITE = 3
    MAX_PARTICLE_COUNT = 8
    SLUG = "chasing-dots"
    VARIANTS = 3

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

    def detect_collisions(self, t, color = (255, 255, 255)):

        # Organize particles by strips 
        strips = [ [] for i in range(self.driver.strips) ]
        for p in self.particles:
            for s in p.strips:
                strips[s].append(p)

        for strip in strips:
            for a, b in itertools.combinations(strip, 2):
                a_pos = int(a.velocity * (t - a.t) + a.position)
                b_pos = int(b.velocity * (t - b.t) + b.position)

                if (a.velocity > 0 and b.velocity < 0 and a_pos >= b_pos) or \
                   (a.velocity < 0 and b.velocity > 0 and a_pos <= b_pos):
                    is_alive = False
                    a.color = b.color = color
                    a.remove_after_next = True
                    b.remove_after_next = True


    def run(self):

        t = 0
        row = 0
        skip_count = 0
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

            elif self.variant == 1:

                strips = [ x for x in range(self.driver.strips)]
                shuffle(strips)
                for s in strips[:count]:
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, s, self.get_next_color(ignore_odd_colors=True), 0, velocity, sprite))
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, s, self.get_next_color(ignore_odd_colors=True), self.driver.leds - 1, -velocity, sprite))

                self.detect_collisions(t)

            else:
                if skip_count == 0:
                    skip_count = count
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, Particle.STRIP_ALL, self.get_next_color(), 0, velocity, sprite))

                skip_count -= 1

            self.driver.set(self.render_leds(t))
            t += self.direction 
            row += 1

            self.sleep()
