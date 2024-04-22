#!/usr/bin/env python3

import sys
from time import sleep
import serial
from struct import pack, unpack
from random import randint

class TrappyDriver:

    num_leds = 144
    num_strips = 8
    buffer_size = num_leds * num_strips * 3

    def __init__(self, device, baud_rate):
        self.device = device
        self.baud_rate = baud_rate
        self.ser = None

    def open(self):

        try:
            self.ser = serial.Serial(self.device,
                                     300 , #self.baud_rate,
                                     bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE)
        except serial.serialutil.SerialException as e:
            print("Serial io failed")
            sys.exit(-1)

    def write_frame(self, frame):
        self.ser.write(b"AB1")
        chunk_size = 1024
        while len(frame) > 0:
            data = bytes(frame[:chunk_size])
            frame = frame[chunk_size:]
            self.ser.write(data)

        ch = self.ser.read(1)

    def write_show(self):
        self.ser.write(b"AB2")
        self.ser.read(1)

    def write_clear(self):
        self.ser.write(b"AB3")
        self.ser.read(1)

    def set_pixel(self, buffer, strip, index, red, green, blue):
        offset = (strip * self.num_leds + index) * 3
        buffer[offset] = red
        buffer[offset + 1] = green
        buffer[offset + 2] = blue

    def test(self):
        i = 0
        while True:
            buffer = bytearray(self.buffer_size)
            for j in range(self.num_strips):
                for k in range(self.num_leds):
                    if (k == i):
                        self.set_pixel(buffer, j, k, 255, 0, 255)
            i = (i+1) % self.num_leds
            td.write_frame(bytes(buffer))

#td = TrappyDriver("/dev/ttyACM0", 460800)
td = TrappyDriver("/dev/ttyACM0", 300)
td.open()
try:
    td.test()
except KeyboardInterrupt:
    td.write_clear()
