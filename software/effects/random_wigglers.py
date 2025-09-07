import itertools
from math import sin, cos, pi, sqrt
from time import sleep, monotonic

from particle_system import Particle, ParticleSystemRenderer, ParticleGenerator
from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS
from color import hue_to_rgb

class WiggleGenerator(ParticleGenerator):
    
    def __init__(self, particle_system: ParticleSystemRenderer, make_bg_particles=False):
        ParticleGenerator.__init__(self, particle_system, make_bg_particles)
        self.particles_per_strip = {}  # Track particles per strip
        
    def next(self, t: float, particle_count, spread, sprite):
        target_count = int(particle_count)
        
        # For each strip, ensure we have the right number of particles
        for strip_idx in range(NUM_STRIPS):
            if strip_idx not in self.particles_per_strip:
                self.particles_per_strip[strip_idx] = []
            
            current_particles = self.particles_per_strip[strip_idx]
            
            # Remove out-of-bounds particles from our tracking
            current_particles[:] = [p for p in current_particles if not p.remove_after_next 
                                  and 0 <= p.position < NUM_LEDS]
            
            # Add new particles if we're below target count
            while len(current_particles) < target_count:
                # Create new wiggling particle at random position
                random_pos = randint(0, NUM_LEDS - 1)
                wiggle_color = self.get_next_color()
                
                # Create particle with small random velocity for wiggling
                wiggle_velocity = randint(-2, 2)
                if wiggle_velocity == 0:
                    wiggle_velocity = 1  # Ensure some movement
                
                new_particle = Particle(t, wiggle_color, random_pos, strip_idx, 
                                      vel=wiggle_velocity, sprite=int(sprite))
                
                # Add wiggle behavior by giving it a random direction change
                new_particle.wiggle_phase = random() * 2 * pi
                new_particle.wiggle_amplitude = spread * 0.1
                new_particle.last_direction_change = t
                
                self.add_particle(new_particle)
                current_particles.append(new_particle)
    
    def update_wiggles(self, t):
        """Update wiggle behavior for existing particles"""
        for strip_particles in self.particles_per_strip.values():
            for particle in strip_particles:
                # Change direction randomly every few frames
                if t - particle.last_direction_change > randint(10, 30):
                    particle.velocity = randint(-2, 2)
                    if particle.velocity == 0:
                        particle.velocity = 1
                    particle.last_direction_change = t
                
                # Check if particle is out of bounds and mark for removal
                if particle.position < 0 or particle.position >= NUM_LEDS:
                    particle.remove_after_next = True

class EffectRandomWigglers(ParticleSystemRenderer):

    SLUG = "random-wigglers"
    FADER_COUNT = 2
    FADER_SPREAD = 3  
    FADER_SPRITE = 4
    COUNT_RANGE_MIN = 3
    COUNT_RANGE_MAX = 15
    SPREAD_RANGE_MIN = 1
    SPREAD_RANGE_MAX = 10
    SPRITE_RANGE_MIN = 1
    SPRITE_RANGE_MAX = 255
    VARIANTS = 1

    def __init__(self, driver, event, apc=None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.generators = [WiggleGenerator(self)]

    def get_active_faders(self):
        return [self.FADER_COUNT, self.FADER_SPREAD, self.FADER_SPRITE]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            return value * (self.COUNT_RANGE_MAX - self.COUNT_RANGE_MIN) + self.COUNT_RANGE_MIN
        elif fader == self.FADER_SPREAD:
            return value * (self.SPREAD_RANGE_MAX - self.SPREAD_RANGE_MIN) + self.SPREAD_RANGE_MIN
        elif fader == self.FADER_SPRITE:
            return value * (self.SPRITE_RANGE_MAX - self.SPRITE_RANGE_MIN) + self.SPRITE_RANGE_MIN
        return value

    def run(self):
        t = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            # Read all fader values at top of loop
            particle_count = self.fader_value(self.FADER_COUNT)
            spread = self.fader_value(self.FADER_SPREAD)
            sprite = self.fader_value(self.FADER_SPRITE)

            # Update wiggle behavior and create new particles as needed
            self.generators[0].update_wiggles(t)
            self.generators[0].next(t, particle_count, spread, sprite)
            
            self.driver.set_np(self.render_leds())
            t += self.direction 
            self.move(t)
            self.sleep()
