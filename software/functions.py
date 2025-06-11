#!/usr/bin/env python3

import abc
import math
import random
import common

class ParametricFunction:

    def __init__(self, period, phase, amplitude, offset):
        self.period = period
        self.phase = phase
        self.amplitude = amplitude
        self.offset = offset

        if type(self.period) in (int, float):
            self.period_f = None
        else:
            self.period_f = self.period
            self.period = self.period_f[0]

        if self.period == 0.0:
            raise ValueError("Period 0 is invalid")

        if type(self.phase) in (int, float):
            self.phase_f = None
        else:
            self.phase_f = self.phase
            self.phase = self.phase_f[0]

        if type(self.amplitude) in (int, float):
            self.amplitude_f = None
        else:
            self.amplitude_f = self.amplitude
            self.amplitude = self.amplitude_f[0]

        if type(self.offset) in (int, float):
            self.offset_f = None
        else:
            self.offset_f = self.offset
            self.offset = self.offset_f[0]

    @abc.abstractmethod
    def __getitem__(self, t):
        pass


class Sin(ParametricFunction):

    def __init__(self, period = 1.0, phase = 0, amplitude = .5, offset = .5):
        # convert from using pesky pi to using parametric values
        super().__init__(period, phase, amplitude, offset)

    def __getitem__(self, t):
        period = math.pi / (self.period/2.0)
        phase = (-math.pi / 2.0) + (math.pi * 2 * self.phase)
        v = math.sin(t * period + phase) * self.amplitude + self.offset
        return v

class Square(ParametricFunction):

    def __init__(self, period = 1.0, phase = 0.0, amplitude = 1.0, offset = 0.0, duty=.5):
        super().__init__(period, phase, amplitude, offset)
        self.duty = duty
        if type(self.duty) in (int, float):
            self.duty_f = None
        else:
            self.duty_f = self.duty
            self.duty = self.duty_f[0]

    def __getitem__(self, t):
        v = (t / self.period) + self.phase
        if float(v) % 1 < self.duty:
            return self.amplitude + self.offset
        else:
            return self.offset

class Sawtooth(ParametricFunction):

    def __init__(self, period = 1.0, phase = 0.0, amplitude = 1.0, offset = 0.0):
        super().__init__(period, phase, amplitude, offset)

    def __getitem__(self, t):
        period = 1.0 / self.period
        return (t * period + self.phase) % 1.0 * self.amplitude + self.offset

class Step(ParametricFunction):

    def __init__(self, period = 1.0, phase = 0.0, amplitude = 1.0, offset = 0.0):
        super().__init__(period, phase, amplitude, offset)

    def __getitem__(self, t):
        v = (t / self.period) + self.phase
        if v >= 0.0:
            return self.amplitude + self.offset
        else:
            return self.offset

class Impulse(ParametricFunction):

    def __init__(self, period = 1.0, phase = 0.0, amplitude = 1.0, offset = 0.0):
        super().__init__(period, phase, amplitude, offset)

    def __getitem__(self, t):
        v = (t / self.period) + self.phase
        if v >= 0.0 and v < 1.0:
            return self.amplitude + self.offset
        else:
            return self.offset
