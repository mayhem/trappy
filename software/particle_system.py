from abc import abstractmethod
from enum import Enum
from colorsys import hsv_to_rgb
from color import hue_to_rgb
import itertools
from time import sleep, monotonic
from math import fmod
from bisect import insort_left, insort_right
import numpy as np

from gradient import create_gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color
from config import NUM_LEDS, NUM_STRIPS

class Particle:

    STRIP_ALL = -1
    def __init__(self, t: float, color: tuple, position: float, strip: int, velocity:float=1.0, r_velocity:float=1.0, sprite_pattern:int=1, z_order:float=0):
        self.t = t                    # Time when particle was added
        self.color = color            # The color of the particle
        self.position = position      # Initial position -- we're not tracking current position
        if strip == Particle.STRIP_ALL:
            self.r_position = None
        else:
            self.r_position = strip / NUM_STRIPS
        self.velocity = velocity
        self.r_velocity = r_velocity
        self.sprite_pattern = sprite_pattern
        self.z_order = z_order

        # If this is set, this particle will be removed after the next render pass
        self.remove_after_next = False

    def __str__(self):
        return "t %.3f p: %.3f v: %.3f" % (self.t, self.position, self.velocity)
        
class GradientType(Enum):
    GRADIENT = 1
    RAINBOW = 2
    BLACK_WHITE = 3
    
class ParticleSystemRenderer(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []
        self.bg_particles = []

        self.debug = 5
        
    def add_particle(self, particle):
        insort_left(self.particles, particle, key=lambda x: x.z_order)

    def add_bg_particle(self, particle):
        self.bg_particles.append(particle)

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()
        
    def render_background(self, t, led_data):
        # Iterate over bg particles
        #   Calculate int pos for all, insertion sort
        # Iterate over pg particles pos
        #   add one point to the palette for each pos.
        #   invalidate out of bounds pos, but keep at least one out of bounds pos 
        particle_positions = []
        for p in self.bg_particles:
            pos = (p.velocity * (t - p.t) + p.position)
            insort_right(particle_positions, (p, pos), key=lambda x: x[1])

        print(t)
        palette = []            
        for p, pos in particle_positions:
            palette.append((pos, p.color))
            print(pos, p.color)
        print()

        self.debug -= 1
        if self.debug == 0:
            import sys
            sys.exit(-1)


    def render_leds(self, t, background_color=(0,0,0)):

        led_data = [ list(background_color) for x in range(self.driver.strips * self.driver.leds) ]
        self.render_background(t, led_data)

        still_alive = []
        for p in sorted(self.particles, key=lambda x: x.z_order, reverse=True):
            is_alive = True
            if p.r_position is None:
                strips = list(range(NUM_STRIPS))
            else:
                strips = [int(p.r_position * NUM_STRIPS)]

            # TODO: This function repeats unecessary steps! (calculating pos ($$) does not depend on s
            for s, strip in enumerate(strips):
                pos = int(p.velocity * (t - p.t) + p.position)
                if pos >= self.driver.leds or pos < 0:
                    is_alive = False
                else:
                    if p.r_position is None:
                        r_pos = s / NUM_STRIPS
                    else:
                        r_pos = fmod(p.r_velocity * (t - p.t) + p.r_position, 1.0)
                    target_strip = int(r_pos * NUM_STRIPS)
                    if is_alive:
                        color = self.get_next_color() if p.color is None else p.color
                        if p.sprite_pattern == 1:
                            led_data[target_strip][pos] = color
                        else:
                            for i in range(8):
                                if p.sprite_pattern & (1 << i) != 0 and pos + i < self.driver.leds:
                                    led_data[target_strip][pos + i] = color

            if not is_alive or p.remove_after_next:
                self.particles.pop(particle_index)

#        print("render end: %d links, %d particles" % (len(self.links), len(self.particles)))

        return led_data
