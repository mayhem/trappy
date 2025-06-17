from time import sleep, monotonic
import cProfile
import pstats

from particle_system import Particle, ParticleSystemRenderer, ParticleLink, LinkType
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from config import NUM_LEDS, NUM_STRIPS


class EffectParticleLink(ParticleSystemRenderer):

    FADER_COUNT = 2
    FADER_SPRITE = 3
    SLUG = "particle-links"
    VARIANTS = 5
    MAX_PARTICLE_COUNT = 8

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.profile = True
        self.profiler = cProfile.Profile()

    def get_active_faders(self):
        return [ self.FADER_COUNT, self.FADER_SPRITE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            # scale to MAX_PARTICLE_COUNT
            return value * (self.MAX_PARTICLE_COUNT-1) + 1

        if fader == self.FADER_SPRITE:
            return value * 254 + 1

        return None
    
    def _run(self):

        t = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return
            
            self.driver.set(self.render_leds(t))
            t += self.direction 

            self.sleep()


    def run(self):

        t = 0
        if self.variant == 0:
            p0 = Particle(t, (0, 0, 0), 0.0, Particle.STRIP_ALL, 0.0, 0.0, 0, -1) 
            p1 = Particle(t, (128, 0, 128), 1.0, Particle.STRIP_ALL, 0.0, 0.0, 0, -1) 
            link = ParticleLink(p0, p1, LinkType.GRADIENT)
            self.add_link(link)

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

            elif self.variant == 1:
                if count == self.driver.strips:
                    velocity = 1 + randint(2, 6)
                    if self.direction == 1:
                        self.particles.append(Particle(t, None, 0, Particle.STRIP_ALL, velocity, 0.0, sprite))
                    else:
                        self.particles.append(Particle(t, None, self.driver.leds - 1, Particle.STRIP_ALL, velocity, 0.0, sprite))
                else:
                    strips = [ x for x in range(self.driver.strips)]
                    shuffle(strips)
                    for s in strips[:count]:
                        velocity = 1 + randint(2, 6)
                        if self.direction == 1:
                            self.particles.append(Particle(t, self.get_next_color(), 0, s, velocity, 0.0, sprite))
                        else:
                            self.particles.append(Particle(t, self.get_next_color(), self.driver.leds - 1, s, velocity, 0.0, sprite))
            elif self.variant == 2:
                strips = [ x for x in range(self.driver.strips)]
                shuffle(strips)
                for s in strips[:count]:
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, self.get_next_color(ignore_odd_colors=True), 0, s, velocity, 0.0, sprite))
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, self.get_next_color(ignore_odd_colors=True), self.driver.leds - 1, s, -velocity, 0.0, sprite))
                self.detect_collisions(t)

            elif self.variant == 3:
                if skip_count == 0:
                    skip_count = self.MAX_PARTICLE_COUNT - count + 1
                    velocity = 1 + randint(1, 3)
                    if self.direction == 1:
                        self.particles.append(Particle(t, self.get_next_color(), 0, spin_offset, velocity, 0.0625, sprite))
                    else:
                        self.particles.append(Particle(t, self.get_next_color(), self.driver.leds - 1, 0, 0.0, random() * 2, sprite))
                    spin_offset = (spin_offset + 2) % NUM_LEDS
                skip_count -= 1

            elif self.variant == 4:
                if skip_count == 0:
                    skip_count = self.MAX_PARTICLE_COUNT - count + 1
                    velocity = 1
                    self.particles.append(Particle(t, self.get_next_color(), 0, Particle.STRIP_ALL, velocity, 0.0, sprite))
                skip_count -= 1

            if self.profile:
                self.profiler.enable()
            tmp = self.render_leds(t)
            if self.profile:
                self.profiler.disable()
            self.driver.set_np(tmp)
            t += self.direction 
            row += 1
#            self.sleep()

        if self.profile:
            stats = pstats.Stats(self.profiler)
            stats.strip_dirs().sort_stats('cumulative').print_stats(20)
