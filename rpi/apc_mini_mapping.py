#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from time import sleep
import json

import rtmidi

class APCMiniMk2Controller:

    def __init__(self):
        self.m_out = rtmidi.MidiOut()
        self.m_in = rtmidi.MidiIn()
        available_ports = self.m_out.get_ports()
        if available_ports:
            self.m_out.open_port(1)
            self.m_in.open_port(1)

        self.custom_colors = [ (0,0,0) for i in range(8) ]

    def shutdown(self):
        del self.m_out
        del self.m_in

    def init_color_grid(self):
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
            colors.append((r,g,b))
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

        return colors

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

    def run(self):
        self.clear_pads()
        colors = self.init_color_grid()

        dest_pad = None
        while True:
            m = self.m_in.get_message()
            if m is None:
                sleep(.01)
                continue

            if m[0][0] == 144: 
                pad = m[0][1]
                if pad < 8:
                    if dest_pad is None:
                        self.blink_pad_fast(pad)
                        dest_pad = pad
                    continue
                if dest_pad is not None:
                    self.clear_pad(dest_pad)
                    self.set_pad_color(dest_pad, colors[pad])
                    self.custom_colors[dest_pad] = colors[pad]
                    dest_pad = None

apc = APCMiniMk2Controller()
try:
    apc.run()
except KeyboardInterrupt:
    print("cleanup")
    apc.clear_pads()
    sleep(.1)
    apc.shutdown()
