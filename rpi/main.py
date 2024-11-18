#!/usr/bin/env python3

from threading import Thread, Lock
from queue import Queue
from random import seed
from time import sleep, monotonic

from scroller import EffectScroller
from gradient_scroller import EffectGradientScroller
from particle_system import EffectParticleSystem
from sparkles import EffectSparkles
from sweep import EffectSweep
from rainbow import EffectRainbowSweep
from pov import EffectPOV
from defs import NUM_LEDS, NUM_STRIPS
from led_driver import LEDDriver
from apc_mini_controller import APCMiniMk2Controller
from effect import EffectEvent, SpeedEvent, GammaEvent, FaderEvent, DirectionEvent

class EventQueue:
    """ Similar to the Lock object, but previous duplicate events are dropped. """

    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def put(self, item):
        self.lock.acquire()
        try:
            if type(self.queue[0]) == type(item):
                self.queue.pop(0)
        except IndexError:
            pass

        self.queue.append(item)
        self.lock.release()

    def get(self):
        self.lock.acquire()
        try:
            item = self.queue.pop(0)
        except IndexError:
            item = None
        self.lock.release()

        return item


class Trappy:

    def __init__(self):
        self.driver = LEDDriver(leds=NUM_LEDS, strips=NUM_STRIPS)
        for i in range(0):
            self.driver.fill((255, 0, 255))
            sleep(.1)
            self.driver.fill((255, 60, 0))
            sleep(.1)

        self.driver.clear()

        # setup effects
        self.effect_classes = []
        self.effect_classes.append(EffectGradientScroller)
        self.effect_classes.append(EffectParticleSystem)
        self.effect_classes.append(EffectSparkles)
        self.effect_classes.append(EffectSweep)
        self.effect_classes.append(EffectRainbowSweep)
        self.effect_classes.append(EffectPOV)
        self.effect_classes.append(EffectScroller)

        self.current_effect = None

        effect_variants = [ eff.VARIANTS for eff in self.effect_classes ]

        # setup the APC
        self.queue = EventQueue()
        self.apc = APCMiniMk2Controller(self.queue, effect_variants)
        self.apc.startup()
        self.apc.start()

        duration =  99999999
        seed(monotonic())

    def queue_event(self, event, avoid_duplicates=False):
        self.queue.put(event)

    def run(self):
        current_effect_index = -1
        try:
            print("main: wait for APC...")
            while not self.apc.is_connected:
                sleep(.1)

            print("main: starting")

            while self.apc.is_connected:
                event = self.queue.get()
                if not event:
                    continue

                if isinstance(event, EffectEvent):
                    if event.effect is None:
                        self.current_effect.accept_event(event)
                        continue

                    if event.effect >= 0 and event.effect < len(self.effect_classes):

                        # Is this effect currently running?
                        if current_effect_index == event.effect:

                            # Is it a new variant? If so, update the variant and leave the effect running
                            if self.current_effect.get_current_variant() != event.variant:
                                self.current_effect.set_current_variant(event.variant)
                                continue

                            # Same variant, in this case restart the effect.

                        if self.current_effect is not None:
                           self.current_effect.exit()
                           self.current_effect.join()
                           self.current_effect = None

                        self.current_effect = self.effect_classes[event.effect](self.driver, event, apc=self.apc)
                        current_effect_index = event.effect
                        faders = self.current_effect.get_active_faders()
                        for f in faders:
                            if f in [0,1,2,3]:
                                raise ValueError("Faders must be between 4 and 8.")

                        for f in range(4, 9):
                            if f in faders:
                                self.apc.track_on(f)
                            else:
                                self.apc.track_clear(f)

                        self.current_effect.start()

                    continue

                if isinstance(event, GammaEvent):
                    self.driver.set_gamma_correction(event.gamma)
                    continue

                # Pass all other events to the current effect
                if self.current_effect is not None:
                    self.current_effect.accept_event(event)

            print("main: APC exit")

        except KeyboardInterrupt:
            self.apc.exit()
            self.apc.shutdown()

        if self.current_effect is not None:
            self.current_effect.exit()
            self.current_effect = None

        self.driver.clear()

if __name__ == "__main__":
    while True:
        t = Trappy()
        t.run()
