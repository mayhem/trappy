import itertools
from time import sleep, monotonic

from particle_system import Particle, ParticleSystemRenderer, ParticleGenerator
from gradient import Gradient
from random import random, randrange, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS

class Radar(ParticleGenerator):
    
    def __init__(self, particle_system: ParticleSystemRenderer, max_particles):
        ParticleGenerator.__init__(self, particle_system)
        self.max_particles = max_particles

    def next(self, t: float, fader_count, fader_fade):
        strip = t % NUM_STRIPS 
        color = (0, 150, 15)
        self.add_bg_particle(Particle(t, color, 0, strip=strip, ttl=1))
        self.add_bg_particle(Particle(t, color, NUM_LEDS, strip=strip, ttl=1))

        if t: 
            dots_strip = (strip - 1) % NUM_STRIPS
            for i in range(fader_count):
                self.add_particle(Particle(t, color, randrange(NUM_LEDS), strip=dots_strip,
                                           fade=fader_fade, sprite=randrange(1, 16), ttl=NUM_STRIPS))


class EffectRadar(ParticleSystemRenderer):

    SLUG = "radar"
    FADER_COUNT = 2
    FADER_FADE = 3
    VARIANTS = 1
    MAX_PARTICLE_COUNT = 25

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.generators = [Radar(self, self.MAX_PARTICLE_COUNT)]
        
    def get_active_faders(self):
        return [ self.FADER_COUNT, self.FADER_FADE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            # scale to MAX_PARTICLE_COUNT
            return value * (self.MAX_PARTICLE_COUNT-1) + 1

        if fader == self.FADER_FADE:
            return value

        return None

    def run(self):
        t = 0
        
        self.set_sleep_params(.1, .4)
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            count = int(self.fader_value(self.FADER_COUNT))
            fade = self.fader_value(self.FADER_FADE)

            self.generators[self.variant].next(t, count, fade)
            self.driver.set_np(self.render_leds())
            t += self.direction 
            self.move(t)

            self.sleep()
