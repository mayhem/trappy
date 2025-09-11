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
                 sprite:int=1,
                 fade:float=None,
                 ttl=None):
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
        self.fade = fade
        self.ttl = ttl

        # If this is set, this particle will be removed after the next render pass
        self.remove_after_next = False

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
        # Using an alpha channel allows for much cooler transitions to gradients effects

        particle_positions = [[] for _ in range(NUM_STRIPS)]
        for i in range(len(self.bg_particles) - 1, -1, -1):
            p = self.bg_particles[i]
            if p.init_r_position is None:
                for i in range(NUM_STRIPS):
                    insort_right(particle_positions[i], p, key=lambda x: x.position)
            else:
                insort_right(particle_positions[int(p.r_position)], p, key=lambda x: x.position)

            # check for ttl expiry
            if p.ttl is not None:
                p.ttl -= 1
                if p.ttl == 0:
                    del self.bg_particles[i]

        for i in range(NUM_STRIPS):
            palette = []
            for pp in particle_positions[i]:
                palette.append((pp.position / NUM_LEDS, pp.color))

            if len(palette) > 1:
                print_palette(palette)
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

            # Fade the particle and remove is black
            if p.fade is not None and p.color is not None:
                p.color[0] = int(p.color[0] * p.fade)
                p.color[1] = int(p.color[1] * p.fade)
                p.color[2] = int(p.color[2] * p.fade)
                if (p.color[0] == 0 and p.color[1] == 0 and p.color[2] == 0):
                    is_alive = False

            # check for out of bounds
            if p.position >= self.driver.leds or p.position < 0:
                is_alive = False

            # check for ttl expiry
            if p.ttl is not None:
                p.ttl -= 1
                if p.ttl == 0:
                    is_alive = False
                
            if is_alive:
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

    def __init__(self, particle_system: ParticleSystemRenderer):
        self.particle_system = particle_system
        
    @property
    def direction(self):
        return self.particle_system.direction
        
    def get_next_color(self, ignore_odd_colors: bool=False):
        return self.particle_system.get_next_color(ignore_odd_colors)

    def get_random_color(self):
        return self.particle_system.get_random_color()

    def add_bg_particle(self, particle):
        self.particle_system.add_bg_particle(particle)

    def add_particle(self, particle):
        self.particle_system.add_particle(particle)

    @abstractmethod
    def next(self, t: float) -> Particle:
        pass
