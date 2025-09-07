from abc import abstractmethod
from enum import Enum
from colorsys import hsv_to_rgb
from color import hue_to_rgb
import itertools
from time import sleep, monotonic
from math import fmod
from bisect import insort_right
import numpy as np

from gradient import create_gradient, print_palette
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color
from config import NUM_LEDS, NUM_STRIPS

STRIP_ALL = -1

class Particle:

    def __init__(self,
                 t: float,
                 color: tuple,
                 init_pos: float=0.0,
                 strip: int=STRIP_ALL,
                 vel:float=0.0,
                 r_vel:float=0.0,
                 sprite:int=1):
        self.init_t = t
        self.color = color                  # The color of the particle
        self.init_position = init_pos       # Initial position
        self.position = init_pos            # Current position
        if strip == STRIP_ALL:
            self.r_position = self.init_r_position = None
        else:
            self.r_position = self.init_r_position = strip / NUM_STRIPS
        self.velocity = vel
        self.r_velocity = r_vel
        self.sprite_pattern = sprite

        # If this is set, this particle will be removed after the next render pass
        self.remove_after_next = False

    def drop_out_of_bounds(self):
        """This funciton is called on a point that just became out of bounds.
           If any cleanup, like gradient adjustment, is needed before the point
           is dropped, it can be done here.
           Return False to keep the point, True to drop it """

        return True

    def __str__(self):
        return "t %.3f p: %.3f v: %.3f" % (self.init_t, self.position, self.velocity)
        
class LinkType(Enum):
    GRADIENT = 1
    RAINBOW = 2
    BLACK_WHITE = 3

#TODO: Make pattern where particles wiggle back and forth, and only if they accidentally slide off, generate a new one

# Override move to get more funky movements.
# Make v and f into functions

class ParticleSystemRenderer(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []
        self.bg_particles = []
        self.debug = 5
        self.allow_margin_particles = False

    def set_allow_margin_particles(self, state):
        # TODO: not implemented yet
        self.allow_margin_particles = state
        
    def add_particle(self, particle):
        self.particles.append(particle)

    def add_bg_particle(self, particle):
        self.bg_particles.append(particle)

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def move(self, t):
        for p in itertools.chain(self.bg_particles, self.particles):
            p.position = (p.velocity * (t - p.init_t)) + p.init_position
            if p.init_r_position is None:
                p.r_position = None
            else:
                p.r_position = (p.r_velocity * (t - p.init_t)) + p.init_r_position

    def render_background(self, led_data):
        # TODO:
        # Add support for gradient types, so we that we can do pre-set gradient. 
        # Add render types: gradient, alpha, solid, rainbow, de/colorize

        particle_positions = [[] for _ in range(NUM_STRIPS)]
        for p in self.bg_particles:
            if p.init_r_position is None:
                for i in range(NUM_STRIPS):
                    insort_right(particle_positions[i], p, key=lambda x: x.position)
            else:
                insort_right(particle_positions[int(p.r_position)], p, key=lambda x: x.position)

        for i in range(NUM_STRIPS):
            palette = []
            for pp in particle_positions[i]:
                palette.append((pp.position / NUM_LEDS, pp.color))

            if len(palette) > 1:
                led_data[i] = create_gradient(palette)

    def render_leds(self):

        led_data = np.zeros((self.driver.strips, self.driver.leds, 3), dtype=np.uint8)
        self.render_background(led_data)
        for particle_index, p in enumerate(self.particles):
            is_alive = True
            if p.r_position is None:
                strips = list(range(NUM_STRIPS))
            else:
                strips = [int(p.r_position * NUM_STRIPS)]

            if p.position >= self.driver.leds or p.position < 0:
                is_alive = False
            else:
                for s, strip in enumerate(strips):
                        if p.r_position is None:
                            r_pos = s / NUM_STRIPS
                        else:
                            r_pos = fmod(p.r_position, 1.0)
                        target_strip = int(r_pos * NUM_STRIPS)
                        color = self.get_next_color() if p.color is None else p.color
                        if p.sprite_pattern == 1:
                            led_data[target_strip][p.position] = color
                        else:
                            for i in range(8):
                                if p.sprite_pattern & (1 << i) != 0 and p.position + i < self.driver.leds:
                                    led_data[target_strip][int(p.position + i)] = color

            if not is_alive or p.remove_after_next:
                if p.drop_out_of_bounds():
                    self.particles.pop(particle_index)

        return led_data

    def render_gradient(self):
        ''' Assumes that all particles are in order '''
        
        palette = []
        for p in self.particles:
            palette.insert(0, (p.position / NUM_LEDS, p.color))
            
#        if palette[0][0] > 0.0:
#            palette.insert(0, (0.0, (0,0,0)))

#        if palette[-1][0] < 1.0:
#            palette.append((1.0, (0,0,0)))

        if len(palette) < 2:
            return np.zeros((self.driver.strips, self.driver.leds, 3), dtype=np.uint8)
        
        return np.tile(create_gradient(palette, num_leds=NUM_LEDS), (1, NUM_STRIPS, 1))

        

class ParticleGenerator:

    def __init__(self, particle_system: ParticleSystemRenderer, make_bg_particles=False):
        self.particle_system = particle_system
        self.make_bg_particles = make_bg_particles
        
    @property
    def direction(self):
        return self.particle_system.direction
        
    def get_next_color(self, ignore_odd_colors: bool=False):
        return self.particle_system.get_next_color(ignore_odd_colors)

    def get_random_color(self):
        return self.particle_system.get_random_color()

    def add_particle(self, particle):
        if self.make_bg_particles:
            self.particle_system.add_bg_particle(particle)
        else:
            self.particle_system.add_particle(particle)

    @abstractmethod
    def next(self, t: float, last_particle: Particle) -> Particle:
        pass
