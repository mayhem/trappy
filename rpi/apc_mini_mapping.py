#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from time import sleep
import json

import rtmidi

class APCMiniMk2Controller:

    def __init__(self):
        self.colors = []
        self.custom_colors = [ (0,0,0,None) for i in range(8) ]
        self.saturation = 1.0
        self.value = 1.0

    def startup(self):
        self.m_out = rtmidi.MidiOut()
        self.m_in = rtmidi.MidiIn()
        available_ports = self.m_out.get_ports()
        if available_ports:
            self.m_out.open_port(1)
            self.m_in.open_port(1)

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

        self.colors = colors

    def shutdown(self):
        del self.m_out
        del self.m_in

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

    def update_color(self, pad, hue):
        if hue is None:
            return
        r,g,b = hsv_to_rgb(hue, self.saturation, self.value)
        new_color = (int(r * 255),int(g * 255),int(b * 255),hue)
        self.set_pad_color(pad, new_color)
        self.custom_colors[pad] = new_color

    def run(self):

        dest_pad = None
        current_track = None
        while True:
            m = self.m_in.get_message()
            if m is None:
                sleep(.01)
                continue

            # key up
            if m[0][0] == 128: 
                continue

            # key down
            if m[0][0] == 144: 
                # track press
                if m[0][1] >= 100 and m[0][1] <= 107:
                    track = m[0][1]
                    if current_track is None:
                        self.blink_track(track)
                        current_track = track
                        dest_pad = track - 100
                        color = self.custom_colors[dest_pad]
                        self.update_color(dest_pad, color[3])
                    else:
                        self.clear_track(current_track)
                        if track != current_track:
                            self.blink_track(track)
                            current_track = track
                            dest_pad = track - 100
                            color = self.custom_colors[dest_pad]
                            self.update_color(dest_pad, color[3])
                        else:
                            current_track = None
                            dest_pad = None
                    continue

                # pad press
                if m[0][1] >= 0 and m[0][1] <= 63:
                    pad = m[0][1]

                    # Do nothing if you press a custom color button
                    if pad < 8:
                        continue

                    if dest_pad is not None:
                        color = self.colors[pad]
                        self.update_color(dest_pad, color[3])
                        continue
                # scene press
                if m[0][1] >= 112 and m[0][1] <= 119:
                    scene = m[0][1] - 112
                    print(scene)
                    continue
            
                print(m)
                continue

            # fader change 
            if m[0][0] == 176: 
                fader = m[0][1]

                # Saturation
                if fader == 48:
                    self.saturation = m[0][2] / 127.0
                    if dest_pad is not None:
                        self.update_color(dest_pad, self.custom_colors[dest_pad][3])
                        
                    continue
                # Value
                if fader == 49:
                    self.value = m[0][2] / 127.0
                    if dest_pad is not None:
                        self.update_color(dest_pad, self.custom_colors[dest_pad][3])
                    continue

                continue

            print(m)

apc = APCMiniMk2Controller()
apc.startup()
try:
    apc.run()
except KeyboardInterrupt:
    print("cleanup")
    apc.clear_pads()
    apc.clear_tracks()
    sleep(.1)
    apc.shutdown()
