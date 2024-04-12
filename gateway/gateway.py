import board
import time
import usb_cdc
import neopixel
from adafruit_neopxl8 import NeoPxl8

class NeoPixelGateway:

    def __init__(self):
        self.pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
        for i in range(3):
            self.pixel.fill((255, 0, 255))
            time.sleep(0.15)
            self.pixel.fill((160, 80, 0))
            time.sleep(0.15)

        self.pixel.fill((0, 0, 0))

        self.leds = 144
        self.strips = 8

        self.pixels = NeoPxl8(
            board.NEOPIXEL0,
            self.leds * self.strips,
            num_strands=self.strips,
            auto_write=False,
            brightness=.25
        )
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

        self.ser = usb_cdc.data

    def handle_frame(self, data):
        """ Expects self.leds * self.strips colors """
        try:
            for i in range(self.leds * self.strips * 3):
                self.pixels[i] = (data[i * 3], data[i*3+1], data[i*3+2])
        except IndexError:
            pass

        self.pixels.show()

    def handle_show(self):
        self.pixels.show()

    def handle_clear(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def run(self):

        # Packet structure:
        # 0xFF 0x34 [packet] [payload]

        self.handle_show()

        while True:
            header = 0
            while True:
                ch = self.ser.read(1)
                if ch == b'A':
                    header += 1
                    continue
                if header > 0 and ch == b'B':
                    break;

                header = 0

            ch = self.ser.read(1)
            if ch not in (b"1", b"2", b"3"):
                self.ser.write("0")
                continue

            if ch == b"1":  # frame
                data = bytes()
                while True:
                    data += self.ser.read(128)
                    if len(data) >= self.leds * self.strips * 3:
                        break

                self.handle_frame(data)
                self.ser.write("1")
                continue

            if ch == b"2":  # show
                self.handle_show()
                self.ser.write("1")
                continue

            if ch == b"3":  # clear
                self.handle_clear()
                self.ser.write("1")
                continue

            self.ser.write("0")

t = NeoPixelGateway()
t.run()
