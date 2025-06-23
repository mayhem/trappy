from time import sleep, monotonic

from particle_system import Particle, ParticleSystemRenderer, GradientType
from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS


class EffectBackground(ParticleSystemRenderer):

    FADER_COUNT = 2
    FADER_SPRITE = 3
    SLUG = "background"
    VARIANTS = 1
    MAX_PARTICLE_COUNT = 8

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

    def get_active_faders(self):
        return [ self.FADER_COUNT, self.FADER_SPRITE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            # scale to MAX_PARTICLE_COUNT
            return value * (self.MAX_PARTICLE_COUNT-1) + 1

        if fader == self.FADER_SPRITE:
            return value * 254 + 1

        return None
    
    def run(self):
        t = 0
        p0 = Particle(t, (255, 0, 0), 0.0, Particle.STRIP_ALL, 0.0, 0.0, 0, -1) 
        p1 = Particle(t, (0, 0, 255), 1.0, Particle.STRIP_ALL, 0.0, 0.0, 0, -1) 
        self.set_background([p0, p1])

        row = 0
        skip_count = 0
        spin_offset = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            count = int(self.fader_value(self.FADER_COUNT))
            sprite = int(self.fader_value(self.FADER_SPRITE))

            # t, color, position, strip, velcity, r_velo, sprite
            if self.variant == 0:
                if skip_count == 0:
                    skip_count = self.MAX_PARTICLE_COUNT - count + 1
                    velocity = 1 + randint(2, 6)
                    if self.direction == 1:
                        self.particles.append(Particle(t, self.get_next_color(), 0, Particle.STRIP_ALL, velocity, 0.0, sprite))
                    else:
                        self.particles.append(Particle(t, self.get_next_color(), self.driver.leds - 1, Particle.STRIP_ALL, velocity, 0.0, sprite))
                skip_count -= 1

            self.driver.set(self.render_leds(t))
            t += self.direction 
            row += 1

            self.sleep()
