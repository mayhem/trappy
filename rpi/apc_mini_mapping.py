#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from time import sleep
import json

from colors import sort_colors, simple_color_gradient
import rtmidi

def set_color_grid(m_out, page):
    msg = [0xF0, 0x47, 0x7F, 0x4F, 0x24]
    pad_msg = []
    if page == 0:
        r = (0, 32)
    else:
        r = (32, 64)
    for pad in range(r[0], r[1]):
        hue = (pad + 1) / 64
        r,g,b = hsv_to_rgb(hue, 1.0, 1.0)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        pad_msg.extend([pad, pad, r >> 7, r & 0x7F, g >> 7, g & 0x7F, b >> 7, b & 0x7F])

    num_bytes = len(pad_msg)
    msg.extend((num_bytes >> 7, num_bytes & 0x7F))
    msg.extend(pad_msg)
    msg.append(0xF7)

    m_out.send_message(msg)


m_out = rtmidi.MidiOut()
m_in = rtmidi.MidiIn()
available_ports = m_out.get_ports()
if available_ports:
    m_out.open_port(1)
    m_in.open_port(1)

with m_out:
    set_color_grid(m_out, 0)
    set_color_grid(m_out, 1)
    
del m_out
