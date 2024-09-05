#!/usr/bin/env python3

from colorsys import hsv_to_rgb, rgb_to_hsv
from copy import copy
from time import sleep, monotonic
from threading import Thread, Lock
import json
import sys

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
                self.controller.is_connected = False


class APCMiniMk2Controller(Thread):

    def __init__(self, queue):
        Thread.__init__(self)

        self._is_connected = False
        self.queue = queue
        self.lock = Lock()
        self.colors = []
        self.custom_colors = [ (0,0,0) for i in range(8) ]
        self.custom_colors[0] = (255, 0, 0)
        self.custom_colors[1] = (255, 0, 255)
        self.custom_colors[2] = (255, 120, 0)
        self.saturation = 1.0
        self.value = 1.0
        self._exit = False
        self.blinker = Blinker(self)
        self.blinker.start()
        self.fader_values = [ 0.0, 0.0, 1.0, .5, .5, .5, .5, .5, .5 ]
        self.direction = DirectionEvent.OUTWARD
        self.key_down_time = None

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

        self.clear_pads()
        self.clear_tracks()
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

        for i, col in enumerate(self.custom_colors):
            self.set_pad_color(i, col)

        self.colors = colors


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

    def clear_pads(self):
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

    def clear_tracks(self):
        for track in range(8):
            self.m_out.send_message([0x90, 0x64 + track, 0])
            sleep(.0001)

    def blink_track(self, track):
        self.m_out.send_message([0x90, track, 2])
        sleep(.005)

    def clear_track(self, track):
        self.m_out.send_message([0x90, track, 0])
        sleep(.005)

    def update_color(self, pad, color):
        hue, _, _ = rgb_to_hsv(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
        r,g,b = hsv_to_rgb(hue, self.saturation, self.value)
        new_color = (int(r * 255),int(g * 255),int(b * 255))
        self.blinker.update_blink_color(pad, new_color)

    def run(self):


        current_track = None
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
                    track = m[0][1]
                    continue

                # shift press
                if m[0][1] >= 0x7A:
                    self.direction = DirectionEvent.OUTWARD if self.direction == DirectionEvent.INWARD else DirectionEvent.INWARD
                    self.queue.put(DirectionEvent(self.direction))
                    continue

                # pad press
                if m[0][1] >= 0 and m[0][1] <= 63:
                    pad = m[0][1]
    
                    # Check to see if this is a long press
                    if press_duration > .5 and pad < 8:
                        self.custom_colors[pad] = (0,0,0)
                        self.set_pad_color(pad, (0,0,0))
                        continue

                    # did we press a custom color button?
                    if pad < 8:
                        if self.blinker.is_blinking(pad):
                            color = self.blinker.get_blink_color(pad)
                            self.blinker.unblink(pad, color)
                            self.custom_colors[pad] = color
                        else:
                            self.blinker.blink(pad, self.custom_colors[pad])
                        continue

                    # If it is a regular button and we have blinking buttons, assign it/them
                    blinking = self.blinker.get_blinking()
                    if blinking:
                        for bpad in blinking:
                            self.blinker.unblink(bpad, self.colors[pad])
                            self.custom_colors[bpad] = self.colors[pad][:3]
                            continue
                    else:
                        self.queue.put(InstantColorEvent(self.colors[pad][:3]))

                # scene press
                if m[0][1] >= 112 and m[0][1] <= 119:
                    scene = m[0][1] - 112
                    colors = []
                    for col in self.custom_colors:
                        if col != (0,0,0):
                            colors.append(col)
                    self.queue.put(EffectEvent(scene, color_values=colors, fader_values=self.fader_values))
                    continue
            
                continue

            # fader change 
            if m[0][0] == 176: 
                fader = m[0][1]

                # save non-mapped fader values
                value = m[0][2] / 127.0
                self.fader_values[fader - 48] = value

                # Saturation
                if fader == 48:
                    self.saturation = m[0][2] / 127.0
                    blinking = self.blinker.get_blinking()
                    for bpad in blinking:
                        self.update_color(bpad, self.custom_colors[bpad])
                    continue
                        
                # Value
                if fader == 49:
                    self.value = m[0][2] / 127.0
                    blinking = self.blinker.get_blinking()
                    for bpad in blinking:
                        self.update_color(bpad, self.custom_colors[bpad])
                    continue
           
                # speed
                if fader == 50:
                    value = m[0][2] / 127.0
                    self.queue.put(SpeedEvent(value))
                    continue

                # General fader, passed to effect
                if fader >= 51 and fader <= 56:
                    # calculate 0 - 1.0
                    self.queue.put(FaderEvent(fader - 48, value))
                    continue

                continue


            print(m)

        self.clear_pads()
        self.clear_tracks()
