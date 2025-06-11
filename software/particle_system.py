from abc import abstractmethod
from enum import Enum
from colorsys import hsv_to_rgb
from color import hue_to_rgb
import itertools
from time import sleep, monotonic
from math import fmod

from gradient import Gradient
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
                self.gradient = Gradient([ (0.0, self.particle0.color), (1.0, self.particle1.color) ])
        
    def get_color(self, offset : float) -> tuple:
        match self.link_type:
            case LinkType.GRADIENT:
                return self.gradient.get_color(offset)
            case LinkType.RAINBOW:
                return hue_to_rgb(offset)
                

class ParticleSystemRenderer(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []
        self.links = []
        
    def add_particle(self, particle):
        self.particles.append(particle)

    def add_link(self, link):
        self.links.append(link)

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def render_leds(self, t, background_color=(0,0,0)):

        led_data = [ list(background_color) for x in range(self.driver.strips * self.driver.leds) ]

        still_alive = []
        for l in self.links:
            start_pos = int(l.particle0.velocity * (t - l.particle0.t) + l.particle0.position)
            end_pos = int(l.particle1.velocity * (t - l.particle1.t) + l.particle1.position)
            step = 1.0 / (end_pos - start_pos)
            leds = int((end_pos - start_pos) * NUM_LEDS)
            
            if l.particle0.r_position is None:
                strips = list(range(NUM_STRIPS))
            else:
                strips = [int(l.particle0.r_position * NUM_STRIPS)]
            for s, strip in enumerate(strips):
                for i, led in enumerate(range(leds)):
                    offset = start_pos + (step * i)
                    led_data[(strip * self.driver.leds) + led] = l.get_color(offset)

        for p in sorted(self.particles, key=lambda x: x.z_order, reverse=True):
            is_alive = True
            if p.r_position is None:
                strips = list(range(NUM_STRIPS))
            else:
                strips = [int(p.r_position * NUM_STRIPS)]
            for s, strip in enumerate(strips):
                pos = int(p.velocity * (t - p.t) + p.position)
                if pos >= self.driver.leds or pos < 0:
                    is_alive = False
                if p.r_position is None:
                    r_pos = s / NUM_STRIPS
                else:
                    r_pos = fmod(p.r_velocity * (t - p.t) + p.r_position, 1.0)
                target_strip = int(r_pos * NUM_STRIPS)
                if is_alive:
                    color = self.get_next_color() if p.color is None else p.color
                    if p.sprite_pattern == 1:
                        led_data[(target_strip * self.driver.leds) + pos] = color
                    else:
                        for i in range(8):
                            if p.sprite_pattern & (1 << i) != 0 and pos + i < self.driver.leds:
                                led_data[(target_strip * self.driver.leds) + pos + i] = color

            if is_alive and not p.remove_after_next:
                still_alive.append(p)

        self.particles = still_alive

        return led_data
