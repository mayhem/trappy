#!/usr/bin/env python3

import sys
from time import sleep
import serial
from struct import pack, unpack
from random import randint

class TrappyDriver:

    def __init__(self, device, baud_rate):
        self.device = device
        self.baud_rate = baud_rate
        self.ser = None

    def open(self):

        try:
            self.ser = serial.Serial(self.device,
                                     self.baud_rate,
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

    def test(self):
        buffer_size = 144 * 8 * 3
        while True:
            for i in range(144):
                frame = bytearray(buffer_size);
                for s in range(8):
                    frame[s * 144 * 3 + (i * 3)] = 255
                td.write_frame(frame)

#td = TrappyDriver("/dev/ttyACM0", 460800)
td = TrappyDriver("/dev/ttyACM0", 921600)
td.open()
try:
    td.test()
except KeyboardInterrupt:
    td.write_clear()
