import itertools
from time import sleep, monotonic

from particle_system import Particle, ParticleSystemRenderer, ParticleGenerator
from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS

class SlidingGradient(ParticleGenerator):
    
    def __init__(self, particle_system: ParticleSystemRenderer, make_bg_particles=False):
        ParticleGenerator.__init__(self, particle_system, make_bg_particles)
        self.skip_count = 0

    def next(self, t: float, fader_spacing, use_bg=False):
        
        if self.skip_count == 0:
            self.skip_count = fader_spacing
            velocity = 2
            if self.direction == 1:
                self.add_particle(Particle(t, self.get_next_color(), -(fader_spacing * 2), vel=velocity))
            else:
                self.add_particle(Particle(t, self.get_next_color(), NUM_LEDS - 1, vel=velocity))

        self.skip_count -= 1

class EffectSlidingGradient(ParticleSystemRenderer):

    SLUG = "sliding-gradient"
    FADER_SPACING = 2
    SPACING_RANGE_MIN = 2
    SPACING_RANGE_MAX = 8
    VARIANTS = 1

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.generators = [SlidingGradient(self, True)]
        self.hue = 0.0

    def get_active_faders(self):
        return [ self.FADER_SPACING ]

    def map_fader_value(self, fader, value):
        # scale to SPACING_RANGE_MIN and SPACING_RANGE_MAX
        if fader == self.FADER_SPACING:
            return value * self.SPACING_RANGE_MAX + self.SPACING_RANGE_MIN

        return None

    def run(self):

        t = 0
        spacing = int(self.fader_value(self.FADER_SPACING))
        while(len(self.bg_particles) < 2 or self.bg_particles[0].position <= NUM_LEDS + spacing):
            self.generators[self.variant].next(t, spacing)
            self.move(t)
            t += 1

        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            spacing = int(self.fader_value(self.FADER_SPACING))
            self.generators[self.variant].next(t, spacing)
            self.driver.set_np(self.render_leds())
            t += self.direction 
            self.move(t)

            self.sleep()
