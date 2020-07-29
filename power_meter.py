from collections import namedtuple
import sys
import os
import time

class power_meter_t(object):
    @property
    def voltage(self):
        raise NotImplementedError

    @voltage.setter
    def voltage(self, enable):
        raise NotImplementedError

    @property
    def current_limit(self):
        raise NotImplementedError

    @current_limit.setter
    def current_limit(self, i):
        raise NotImplementedError

    @property
    def current(self):
        raise NotImplementedError

class u2020_t(power_meter_t):
    def __init__(self, gpib):
        self.gpib = gpib

    def measure():
        self.gpib.write("SYST:PRES") # Presets the U2020 X-Series to default values.
        self.gpib.write("SENS:FREQ 50MHz") # Sets the frequency to 50 MHz.
        self.gpib.write("INIT:CONT ON") # Initiates the trigger sequence.
        self.gpib.write("UNIT:POW DBM") # Sets the power measurement unit for CALC1 to W.
        self.gpib.write("FORM REAL") # Sets the data format to REAL.
        self.gpib.write("CAL:ZERO:AUTO OFF") # Disables auto-zeroing.
        self.gpib.write("CAL:AUTO OFF") # Disables auto-calibration.
        self.gpib.write("SENS:AVER:SDET OFF") # Disables step detection.
        self.gpib.write("SENS:DET:FUNC NORM") # Sets the measurement mode to normal.
        self.gpib.write("SENS:MRAT FAST") # Sets the measurement speed to fast mode.
        self.gpib.write("TRIG:COUN 100") # Sets the buffer size of the U2020 X-Series to 100 to store 100 measurement readings.
        return self.gpib.read("FETC?") # Fetches the reading.

