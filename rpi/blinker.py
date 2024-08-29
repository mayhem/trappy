from time import sleep
from threading import Thread, Lock


class Blinker(Thread):

    def __init__(self, apc):
        Thread.__init__(self)
        self.apc = apc
        self.blinking = {}
        self.state = False
        self.lock = Lock()
        self._exit = False

    def exit(self):
        self._exit = True
        self.join()

    def blink(self, pad, color):
        if pad < 0 or pad > 7:
            return

        self.lock.acquire()
        self.blinking[pad] = color
        self.lock.release()
        self.apc.set_pad_color(pad, color)

    def update_blink_color(self, pad, color):
        if pad < 0 or pad > 7:
            return

        self.lock.acquire()
        self.blinking[pad] = color
        self.lock.release()

    def get_blink_color(self, pad):
        if pad < 0 or pad > 7:
            return

        self.lock.acquire()
        color = self.blinking[pad]
        self.lock.release()

        return color

    def unblink(self, pad, color):
        if pad < 0 or pad > 7:
            return

        self.lock.acquire()
        del self.blinking[pad]
        self.lock.release()
        self.apc.set_pad_color(pad, color)

    def is_blinking(self, pad):
        if pad < 0 or pad > 7:
            return

        self.lock.acquire()
        isb = pad in self.blinking
        self.lock.release()

        return isb

    def get_blinking(self):
        self.lock.acquire()
        blinking = [ k for k in self.blinking.keys() ]
        self.lock.release()

        return blinking


    def run(self):
        while not self._exit:
            self.lock.acquire()
            if len(self.blinking) == 0:
                self.lock.release()
                sleep(.05)
                continue

            for pad in self.blinking:
                if self.state:
                    self.apc.set_pad_color(pad, self.blinking[pad])
                else:
                    self.apc.set_pad_color(pad, (128,128,128))

            self.state = not self.state

            self.lock.release()
            sleep(.3)
