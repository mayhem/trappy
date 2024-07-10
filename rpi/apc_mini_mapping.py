#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from time import sleep
import json

import rtmidi

def init_color_grid(m_out):
    pad_msg = []
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
        pad_msg.extend([pad, pad, r >> 7, r & 0x7F, g >> 7, g & 0x7F, b >> 7, b & 0x7F])

    num_bytes = len(pad_msg) // 2

    msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
    msg.extend((num_bytes >> 7, num_bytes & 0x7F))
    msg.extend(pad_msg[0:256])
    msg.append(0xF7)
    m_out.send_message(msg)
    sleep(.005)

    msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
    msg.extend((num_bytes >> 7, num_bytes & 0x7F))
    msg.extend(pad_msg[256:512])
    msg.append(0xF7)
    m_out.send_message(msg)
    sleep(.005)

def set_pad_color(m_out, pad, color):
    num_bytes = 8
    msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
    msg.extend((num_bytes >> 7, num_bytes & 0x7F))
    msg.extend([pad, pad, color[0] >> 7, color[0] & 0x7F, color[1] >> 7, color[1] & 0x7F, color[2] >> 7, color[2] & 0x7F])
    msg.append(0xF7)

    m_out.send_message(msg)
    sleep(.005)

def clear_pads(m_out):
    num_bytes = 8
    msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
    msg.extend((num_bytes >> 7, num_bytes & 0x7F))
    msg.extend([0, 63, 0, 0, 0, 0, 0, 0])
    msg.append(0xF7)

    m_out.send_message(msg)
    sleep(.005)

m_out = rtmidi.MidiOut()
m_in = rtmidi.MidiIn()
available_ports = m_out.get_ports()
if available_ports:
    m_out.open_port(1)
    m_in.open_port(1)

with m_out:
    clear_pads(m_out)
    init_color_grid(m_out)
    
del m_out
