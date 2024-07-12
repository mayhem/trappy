#!/usr/bin/env python3

from threading import Thread
from random import seed
from time import sleep, monotonic

from apc_mini_controller import APCMiniMk2Controller
from trappy import Trappy

def controller_main(apc):
    apc.startup()
    apc.run()
    apc.clear_pads()
    apc.clear_tracks()
    sleep(.1)
    apc.shutdown() 

def main():

    apc = APCMiniMk2Controller()
    apc_thread = Thread(target=controller_main, args=(apc,))
    apc_thread.start()

    print("controller thread started")

    duration = 12 
    seed(monotonic())

    trappy = Trappy()
    try:
        while True:
            trappy.effect_gradient_chase(monotonic() + duration)
            trappy.effect_chase(monotonic() + duration)
            trappy.effect_checkerboard(monotonic() + duration)
    except KeyboardInterrupt:
        apc.exit(True)
        trappy.driver.clear()
        apc_thread.join()


if __name__ == "__main__":
    main()
