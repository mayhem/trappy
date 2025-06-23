from abc import abstractmethod
from enum import Enum
from colorsys import hsv_to_rgb
from color import hue_to_rgb
import itertools
from time import sleep, monotonic
from math import fmod
from bisect import insort_left
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
        
class LinkType(Enum):
    GRADIENT = 1
    RAINBOW = 2
    BLACK_WHITE = 3
    
class ParticleLink:

    def __init__(self, particle0: Particle, particle1: Particle, link_type: LinkType, reverse: bool = False):
        self.particle0 = particle0
        self.particle1 = particle1
        self.link_type = link_type
        
        if self.particle0.z_order != self.particle1.z_order:
            raise ValueError("Cannot create particle link with particles in different z_orders.")

        if self.particle0.r_position != self.particle1.r_position:
            raise ValueError("Cannot create particle link with particles of different strips (r_position).")

        match link_type:
            case LinkType.GRADIENT:
                self.gradient = create_gradient([ (0.0, self.particle0.color), (1.0, self.particle1.color) ])
        
    def get_color(self, led : int) -> tuple:
        match self.link_type:
            case LinkType.GRADIENT:
                return self.gradient[led]
            case LinkType.RAINBOW:
                return hue_to_rgb(led / NUM_LEDS)

    def __str__(self):
        return "(%s)-(%s)" % (self.particle0.__str__(), self.particle1.__str__())
                

class ParticleSystemRenderer(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []
        self.links = []
        
    def add_particle(self, particle):
        insort_left(self.particles, particle, key=lambda x: x.z_order)

    def add_link(self, link):
        insort_left(self.links, link, key=lambda x: x.particle0.z_order)

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def render_leds(self, t):

        led_data = np.zeros((self.driver.strips, self.driver.leds, 3), dtype=np.uint8)

#        print("render begin: %d links, %d particles" % (len(self.links), len(self.particles)))
        for link_index, l in enumerate(self.links):
            start_pos = int(l.particle0.velocity * (t - l.particle0.t) + l.particle0.position)
            end_pos = int(l.particle1.velocity * (t - l.particle1.t) + l.particle1.position)
#            print("t: %.3f start: %d end: %d" % (t, start_pos, end_pos))
#            print(l)
            start_bad = True if (start_pos < 0 or start_pos >= NUM_LEDS) else False
            end_bad = True if (end_pos < 0 or end_pos >= NUM_LEDS) else False
            if (start_bad and end_bad):
                del self.links[link_index]
                continue

            leds = (end_pos - start_pos) - 1
#            print("start %d stop %d step: %.3f leds: %d" % (start_pos, end_pos, step, leds))
            if leds < 1:
                continue
            
            if l.particle0.r_position is None:
                strips = list(range(NUM_STRIPS))
            else:
                strips = [int(l.particle0.r_position * NUM_STRIPS)]
            gradient_step = 1.0 / (end_pos - start_pos)  # distance between leds in gradient space
            led_step = 1.0 / NUM_LEDS                    # distance between leds in led space
            for s, strip in enumerate(strips):
                for led in range(start_pos, end_pos):
                    # calc percentage in LED space from start end pos
                    pos = int(led / (NUM_LEDS-1) * gradient_step) 
# TDOO: Change get_color to get_gradient_range, to avoid repeated function calls and setup overhead
# TODO: Currently we calculate a whole palette, even if we fetch 2 or 3 pixels. improve that!
                    led_data[strip][led] = l.get_color(pos)

        for particle_index, p in enumerate(self.particles):
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
