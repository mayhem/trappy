from abc import abstractmethod
from time import sleep

# TODO: How to send messages to MIDI device for button states/colors?

class ControlMessage:

    def __init__(self, control, float_value=None, color_volue=None):
        # Which control is sending this message?
        self.control = control
        self.float_val = float_value
        self.color_val = color_value

    @property
    def float_value(self):
        return self.float_val

    @property
    def color_value(self):
        return self.color_val


class MidiControl()
    """ Maps midi control input to parametric inputs. Sliders are 0-100%, but input might need to be -1.0 - 1.0. """

    def __init__(self, name):
        self.name = name
        self.effect = None
        self.current_value = None

    def set_effect(self, effect):
        """ The effect must be set before we can start receiving messages! """
        self.effect = effect

    def map(self, value):
        """ Override this function if you need a different range of input values """
        return value

    def receive_midi_message(self, msg):
        """ Callback used by the main loop to pass midi messages to the controls. The internal state of
        this controller should be updated if the message pertains to this contol. """

    def value(self):
        """ Return the current value of this control (after being mapped into the right input range  """

        return self.map(self.current_value)


class Effect:

    def __init__(self, driver):
        self.driver = driver

        # list controls required for this effect to work. In order to start an effect, each of the
        # controls must send an INIT message, so the Control object can be set.
        self.speed_control = None

    def receive_message(self, control_name, msg: ControlMessage):
        """ Used by controls to send control messages to the effect. """

    @abstractmethod
    def run(self, timeout):
        pass


