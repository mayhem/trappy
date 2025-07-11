#!/usr/bin/env python3

from colorsys import hsv_to_rgb, rgb_to_hsv
from color import hue_to_rgb, shift_color
from copy import copy
from random import random
from time import sleep, monotonic
from threading import Thread, Lock
import json
import sys
import os

import rtmidi
from effect import *
from blinker import Blinker
import usb.core


class APCMiniMk2ControllerWatchdog(Thread):

    def __init__(self, controller):
        Thread.__init__(self)
        self.controller = controller
        self._exit = False

    def exit(self):
        self._exit = True
        self.join()

    def run(self):
        while not self._exit:
            sleep(.1)
            dev = usb.core.find(idVendor=0x09e8, idProduct=0x004f)
            if dev:
                if not self.controller.is_connected:
                    self.controller.is_connected = True
                continue

            if self.controller.is_connected:
                os._exit(-1)
                return


class APCMiniMk2Controller(Thread):

    NUM_BOOKMARKS = 63
    SCREENS = {"hue": 0, "scene": 1, "bookmark": 2 }

    def __init__(self, queue, effect_variants):
        Thread.__init__(self)

        self._is_connected = False
        self.queue = queue
        self.lock = Lock()
        self.colors = []
        self.custom_colors = [ (0,0,0) for i in range(8) ]
        hue = random()
        self.custom_colors[0] = hue_to_rgb(hue)
        self.custom_colors[1] = hue_to_rgb(hue + .1, value=.9)
        self.custom_colors[2] = hue_to_rgb(hue + .2, value=.8)
        self.custom_colors[3] = hue_to_rgb(hue + .3, value=.7)
        self.saturation = 1.0
        self.value = 1.0
        self.hue_shift = 1.0
        self._exit = False
        self.blinker = Blinker(self)
        self.blinker.start()
        self.fader_values = [ 1.0, 1.0, .5, .5, .5, .5, .5, .5, .5 ]
        self.active_faders = []
        self.direction = DirectionEvent.OUTWARD
        self.key_down_time = None
        self.effect_variants = effect_variants

        self.watchdog = APCMiniMk2ControllerWatchdog(self)
        self.watchdog.start()

    @property
    def is_connected(self):
        self.lock.acquire()
        ret = self._is_connected
        self.lock.release()
        return ret

    @is_connected.setter
    def is_connected(self, connected):
        self.lock.acquire()
        self._is_connected = connected
        self.lock.release()

    def exit(self):
        self._exit = True
        self.watchdog.exit()
        self.blinker.exit()

    def startup(self):
        self.m_out = rtmidi.MidiOut()
        self.m_in = rtmidi.MidiIn()

        print("APC: Wait for APC mini...", end="")
        sys.stdout.flush()
        while not self.is_connected:
            sleep(.1)

        print("APC connected, run startup")
        available_ports = self.m_out.get_ports()
        for index, port in enumerate(available_ports):
            if port.startswith("APC mini mk2"):
                self.m_out.open_port(index)
                self.m_in.open_port(index)
                break

        self.pads_clear_all()
        self.scenes_clear_all()
        self.tracks_clear_all()

        self.screen = self.SCREENS["hue"]
        self.update_screen(0)
        for i in self.SCREENS:
            self.scene_on(self.SCREENS[i])

    def update_custom_colors(self):
        for i, col in enumerate(self.custom_colors):
            shifted = shift_color(col, self.hue_shift)
            self.set_pad_color(i, shifted)

    def set_active_faders(self, faders):
        self.active_faders = faders


    def enable_faders(self):
        for f in self.active_faders:
            if f in [0,1]:
                raise ValueError("Faders must be between 2 and 8.")

        for f in range(2, 9):
            if f in self.active_faders:
                self.track_on(f)
            else:
                self.track_clear(f)

    def update_screen(self, screen):

        if screen < 0 or screen > len(self.SCREENS):
            return

        self.screen = screen
        if self.screen == self.SCREENS["hue"]:
            self.setup_hue_screen()
            return

        if self.screen == self.SCREENS["scene"]:
            self.setup_scene_screen()
            self.enable_faders()
            return

        if self.screen == self.SCREENS["bookmark"]:
            self.setup_bookmark_screen()
            return


    def setup_hue_screen(self):

        pad_msg = []
        colors = []
        for pad in range(0, 64):
            hue = 0
            if pad < 8:
                r,g,b = (0,0,0)
            else:
                hue = (pad - 7) / 56
                r,g,b = hsv_to_rgb(hue, 1.0, 1.0)
                r = int(r * 255)
                g = int(g * 255)
                b = int(b * 255)
            colors.append((r,g,b, hue))
            pad_msg.extend([pad, pad, r >> 7, r & 0x7F, g >> 7, g & 0x7F, b >> 7, b & 0x7F])

        self.send_pad_msgs(pad_msg)

        self.update_custom_colors()

        self.colors = colors

        # set the faders
        self.tracks_clear_all()
        self.track_on(0)
        self.track_on(1)
        self.track_on(2)


    def setup_scene_screen(self):

        pad_msg = []

        hue = 0.0
        for col in range(8):
            try:
                num_sub_effects = self.effect_variants[col]
            except IndexError:
                num_sub_effects = 0

            for row in range(8):
                if row < num_sub_effects:
                    r,g,b = hsv_to_rgb(hue, 1.0, 1.0 - (.125 * row))
                    r = int(r * 255)
                    g = int(g * 255)
                    b = int(b * 255)
                else:
                    r = g = b = 0

                pad = ((7 - row) * 8) + col
                pad_msg.append([pad, pad, r >> 7, r & 0x7F, g >> 7, g & 0x7F, b >> 7, b & 0x7F])

            hue += .125

        pad_msg = sorted(pad_msg, key=lambda a: a[0])
        pad_msg = [x for xs in pad_msg for x in xs]

        self.send_pad_msgs(pad_msg)

        # set the faders
        self.tracks_clear_all()
        self.track_on(0)
        self.track_on(1)

    def setup_bookmark_screen(self):

        bookmarks = [ [[0,0,0], None] for i in range(self.NUM_BOOKMARKS + 1) ]
        bookmarks[0][0] = (255, 255, 255)
        row = 0
        col = 0
        pad_msg = []
        for bookmark in bookmarks:
            color = bookmark[0]
            pad = ((7 - row) * 8) + col
            pad_msg.append([pad, pad, color[0] >> 7, color[0] & 0x7F, color[1] >> 7, color[1] & 0x7F, color[2] >> 7, color[2] & 0x7F])
            col += 1
            if col == 8:
                col = 0
                row += 1

        pad_msg = sorted(pad_msg, key=lambda a: a[0])
        pad_msg = [x for xs in pad_msg for x in xs]

        self.send_pad_msgs(pad_msg)
        self.tracks_clear_all()


    def send_pad_msgs(self, pad_msg):
   
        num_bytes = len(pad_msg) // 2

        msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
        msg.extend((num_bytes >> 7, num_bytes & 0x7F))
        msg.extend(pad_msg[0:256])
        msg.append(0xF7)
        self.m_out.send_message(msg)
        sleep(.01)

        msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
        msg.extend((num_bytes >> 7, num_bytes & 0x7F))
        msg.extend(pad_msg[256:512])
        msg.append(0xF7)
        self.m_out.send_message(msg)
        sleep(.01)


    def shutdown(self):
        # Wait for pending operations to finish
        print("stopping....")
        sleep(.5)
        del self.m_out
        del self.m_in

    def send_intro_msg(self):
        # The data returned can be corrupted, moving on
        self.m_in.ignore_types(sysex=False)

        msg = [ 0xF0, 0x47, 0x7F, 0x4F, 0x60, 0x00, 0x04, 0x00, 0x01, 0x01, 0x00, 0xF7]
        self.m_out.send_message(msg)
        if m[0][0] == 240:
            print(m[0])
            if m[0][:5] == [240, 71, 127, 79, 97]:
                print("Got intro message!")
                for i in range(9):
                    print("fader %d: %d" % (i, m[0][i + 7]))

    def set_pad_color(self, pad, color):
        num_bytes = 8
        msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
        msg.extend((num_bytes >> 7, num_bytes & 0x7F))
        msg.extend([pad, pad, color[0] >> 7, color[0] & 0x7F, color[1] >> 7, color[1] & 0x7F, color[2] >> 7, color[2] & 0x7F])
        msg.append(0xF7)

        self.m_out.send_message(msg)
        sleep(.005)

    def pads_clear_all(self):
        for pad in range(64):
            self.m_out.send_message([0x96, pad, 0])
            sleep(.0001)

    def blink_pad_fast(self, pad):
        self.m_out.send_message([0x9E, pad, 3])
        sleep(.005)

    def blink_pad_slow(self, pad):
        self.m_out.send_message([0x9f, pad, 3])
        sleep(.005)

    def clear_pad(self, pad):
        self.m_out.send_message([0x96, pad, 0])
        sleep(.005)

    def tracks_clear_all(self):
        for track in range(8):
            self.m_out.send_message([0x90, 0x64 + track, 0])
            sleep(.0001)

    def track_on(self, track):
        self.m_out.send_message([0x90, 0x64 + track, 1])
        sleep(.005)

    def track_blink(self, track):
        self.m_out.send_message([0x90, 0x64 + track, 2])
        sleep(.005)

    def track_clear(self, track):
        self.m_out.send_message([0x90, 0x64 + track, 0])
        sleep(.005)

    def scene_on(self, track):
        self.m_out.send_message([0x90, 0x70 + track, 1])
        sleep(.005)

    def scene_blink(self, track):
        self.m_out.send_message([0x90, 0x70 + track, 2])
        sleep(.005)

    def scene_clear(self, track):
        self.m_out.send_message([0x90, 0x70 + track, 0])
        sleep(.005)

    def scenes_clear_all(self):
        for track in range(8):
            self.scene_clear(track)
            sleep(.0001)

    def update_color(self, pad, color):
        hue, _, _ = rgb_to_hsv(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
        r,g,b = hsv_to_rgb(hue, self.saturation, self.value)
        new_color = (int(r * 255),int(g * 255),int(b * 255))
        self.blinker.update_blink_color(pad, new_color)

    def handle_effect_pad_press(self, pad):

        row = 7 - (pad // 8)
        col = pad - ((7 - row) * 8)

        # the column determines the effect, the row the variant
        effect = col
        variant = row

        colors = []
        for col in self.custom_colors:
            if col != (0,0,0):
                colors.append(shift_color(col, self.hue_shift))

        # Note: This could send events for effects that do not exist!
        self.queue.put(EffectEvent(effect, variant, color_values=colors, fader_values=self.fader_values))

    def handle_bookmark_pad_press(self, pad):

        row = 7 - (pad // 8)
        col = pad - ((7 - row) * 8)

        # the column determines the effect, the row the variant
        effect = col
        variant = row


    def run(self):

        current_track = None
        key_down_time = None
        reset_count = 0
        while not self._exit:
            m = self.m_in.get_message()
            if m is None:
                sleep(.01)
                continue

            # key down
            if m[0][0] == 144: 
                key_down_time = monotonic()
                continue

            # key up
            if m[0][0] == 128: 
                if key_down_time is not None:
                    press_duration = monotonic() - key_down_time
                else:
                    press_duration = 0.0

                # track press
                if m[0][1] >= 100 and m[0][1] <= 107:
                    track = m[0][1] - 100
                    if track == 2:
                        self.update_custom_colors()
                    continue

                # shift press
                if m[0][1] >= 0x7A:
                    self.direction = DirectionEvent.OUTWARD if self.direction == DirectionEvent.INWARD else DirectionEvent.INWARD
                    self.queue.put(DirectionEvent(self.direction))
                    continue

                # pad press
                if m[0][1] >= 0 and m[0][1] <= 63:
                    pad = m[0][1]

                    if self.screen == self.SCREENS["scene"]:
                        self.handle_effect_pad_press(pad)
                        continue

                    if self.screen == self.SCREENS["bookmark"]:
                        self.handle_bookmark_pad_press(pad)
                        continue

                    # Check to see if this is a long press
                    if press_duration > .5 and pad < 8:
                        self.custom_colors[pad] = (0,0,0)
                        self.set_pad_color(pad, (0,0,0))
                        continue

                    # did we press a custom color button?
                    if pad < 8:
                        if self.blinker.is_blinking(pad):
                            # Set the color according to the hue/value sliders
                            color = self.blinker.get_blink_color(pad)
                            self.blinker.unblink(pad, color)
                            self.custom_colors[pad] = shift_color(color, self.hue_shift)
                        else:
                            self.blinker.blink(pad, shift_color(self.custom_colors[pad], self.hue_shift))
                        continue

                    # If it is a regular button and we have blinking buttons, assign it/them
                    blinking = self.blinker.get_blinking()
                    if blinking:
                        for bpad in blinking:
                            self.blinker.unblink(bpad, self.colors[pad])
                            self.custom_colors[bpad] = shift_color(self.colors[pad], self.hue_shift)
                            continue
                    else:
                        self.queue.put(InstantColorEvent(self.colors[pad][:3]))

                    continue

                # scene press
                if m[0][1] >= 112 and m[0][1] <= 119:
                    scene = m[0][1] - 112
                    if scene == 7:
                        reset_count += 1
                        print("reset count %d" % reset_count)
                        if reset_count == 5:
                            os._exit(1)
                    else:
                        reset_count = 0

                    self.update_screen(scene)

                    continue
            
                continue

            # fader change 
            if m[0][0] == 176: 
                fader = m[0][1]

                # save non-mapped fader values
                value = m[0][2] / 127.0
                self.fader_values[fader - 48] = value

                if self.screen == self.SCREENS["hue"]:
                    # Saturation
                    if fader == 48:
                        self.saturation = m[0][2] / 127.0
                        blinking = self.blinker.get_blinking()
                        for bpad in blinking:
                            self.update_color(bpad, shift_color(self.custom_colors[bpad], self.hue_shift))
                        continue
                            
                    # Value
                    if fader == 49:
                        self.value = m[0][2] / 127.0
                        blinking = self.blinker.get_blinking()
                        for bpad in blinking:
                            self.update_color(bpad, shift_color(self.custom_colors[bpad], self.hue_shift))
                        continue

                    # Hue shift
                    if fader == 50:
                        self.hue_shift = m[0][2] / 127.0

                if self.screen == self.SCREENS["scene"]:
                    # brightness
                    if fader == 48:
                        value = m[0][2] / 127.0
                        self.queue.put(BrightnessEvent(value))
                        continue
               
                    # speed
                    if fader == 49:
                        value = m[0][2] / 127.0
                        self.queue.put(SpeedEvent(value))
                        continue

                    # General fader, passed to effect
                    if fader >= 50 and fader <= 56:
                        # calculate 0 - 1.0
                        self.queue.put(FaderEvent(fader - 48, value))
                        continue

                continue

            print(m)

        self.pads_clear_all()
        self.tracks_clear_all()
        self.scenes_clear_all()
