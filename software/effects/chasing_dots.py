import itertools
from time import sleep, monotonic

from particle_system import Particle, ParticleSystemRenderer, ParticleGenerator
from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS

class EyeOfSauron(ParticleGenerator):
    
    def __init__(self, particle_system: ParticleSystemRenderer, max_particles):
        ParticleGenerator.__init__(self, particle_system)
        self.skip_count = 0
        self.max_particles = max_particles

    def next(self, t: float, fader_count, fader_sprite):
        if self.skip_count == 0:
            self.skip_count = self.max_particles - fader_count + 1
            velocity = 1 + randint(2, 6)
            if self.direction == 1:
                self.add_particle(Particle(t, self.get_next_color(), 0, vel=velocity, sprite=fader_sprite))
            else:
                self.add_particle(Particle(t, self.get_next_color(), NUM_LEDS - 1, vel=velocity, sprite=fader_sprite))

        self.skip_count -= 1
        

class Starfield(ParticleGenerator):
    
    def next(self, t: float, fader_count, fader_sprite):
        strips = [ x for x in range(NUM_STRIPS)]
        shuffle(strips)
        for s in strips[:fader_count]:
            velocity = 1 + randint(2, 6)
            if self.direction == 1:
                self.add_particle(Particle(t, self.get_random_color(), 0, s, vel=velocity, sprite=fader_sprite))
            else:
                self.add_particle(Particle(t, self.get_random_color(), NUM_LEDS - 1, s, vel=velocity, sprite=fader_sprite))

class Collisions(ParticleGenerator):
    
    def next(self, t: float, fader_count, fader_sprite):
        strips = [ x for x in range(NUM_STRIPS)]
        shuffle(strips)
        for s in strips[:fader_count]:
            velocity = 1 + randint(2, 6)
            self.add_particle(Particle(t, self.get_next_color(ignore_odd_colors=True), 0, s, vel=velocity, sprite=fader_sprite))
            velocity = 1 + randint(2, 6)
            self.add_particle(Particle(t, self.get_next_color(ignore_odd_colors=True), NUM_LEDS - 1, s, vel=-velocity, sprite=fader_sprite))
        self.particle_system.detect_collisions(t)

class Spiral(ParticleGenerator):
    
    def __init__(self, particle_system: ParticleSystemRenderer, max_particles):
        ParticleGenerator.__init__(self, particle_system)
        self.skip_count = 0
        self.max_particles = max_particles
        self.spin_offset = 0

    def next(self, t: float, fader_count, fader_sprite):
        if self.skip_count == 0:
            self.skip_count = self.max_particles - fader_count + 1
            velocity = 1 + randint(1, 3)
            if self.direction == 1:
                self.add_particle(Particle(t, self.get_next_color(), 0, self.spin_offset, velocity, 0.0625, fader_sprite))
            else:
                self.add_particle(Particle(t, self.get_next_color(), NUM_LEDS - 1, 0, 0.0, random() * 2, fader_sprite))
            self.spin_offset = (self.spin_offset + 2) % NUM_LEDS
        self.skip_count -= 1

class EffectChasingDots(ParticleSystemRenderer):

    FADER_COUNT = 2
    FADER_SPRITE = 3
    SLUG = "background"
    MAX_PARTICLE_COUNT = 8
    VARIANTS = 4

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.generators = [EyeOfSauron(self, self.MAX_PARTICLE_COUNT), 
                           Starfield(self), 
                           Collisions(self), 
                           Spiral(self, self.MAX_PARTICLE_COUNT)]
        
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
            if p.r_position is None:
                for s in range(NUM_STRIPS):
                    strips[s].append(p)
            else:
                strip = int(p.r_position * NUM_STRIPS)
                strips[strip].append(p)

        for strip in strips:
            for a, b in itertools.combinations(strip, 2):
                if (a.velocity > 0 and b.velocity < 0 and a.position >= b.position) or \
                   (a.velocity < 0 and b.velocity > 0 and a.position <= b.position):
                    is_alive = False
                    a.color = b.color = color
                    a.remove_after_next = True 
                    b.remove_after_next = True

    
    def run(self):
        t = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            count = int(self.fader_value(self.FADER_COUNT))
            sprite = int(self.fader_value(self.FADER_SPRITE))

            self.generators[self.variant].next(t, count, sprite)
            self.driver.set_np(self.render_leds())
            t += self.direction 
            self.move(t)

            self.sleep()
