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

    def opc(self):
        return self.gpib.read("*opc?")

    def pulsed(self, freq, delay, time):
        # freq is the frequency in Hz
        # delay is how much time after the trigger event to start measuring in seconds
        # time is the duration of the time-gated period

        # Presets the U2020 X-Series to default values.
        self.gpib.write("SYST:PRES")

        # Sets the frequency.
        self.gpib.write("SENS:FREQ %u" % freq)

        # Sets the trigger source to external trigger input.
        self.gpib.write("TRIG:SOUR EXT") # TODO, is this the correct trigger type?

        # On reset, the trigger is configured to happen on the rising edge of a signal, which is exactly what we need

        # Sets the measurement speed to fast mode.
        self.gpib.write("SENS:MRAT FAST")

        # Sets the buffer size of the U2020 X-Series to 100 to store 1 measurement readings.
        self.gpib.write("TRIG:COUN 1")

        # Disables auto-zeroing.
        self.gpib.write("CAL:ZERO:AUTO OFF")

        # Disables auto-calibration.
        self.gpib.write("CAL:AUTO OFF")

        # Set the delay between the triggered point and the start of the time-gated period.
        self.gpib.write("SENS:SWE:OFFS:TIME %u" % delay)

        # Set the duration of the time-gated period
        self.gpib.write("SENS:SWE:TIME %u" % time)

        # Sets the power measurement unit for CALC1 to W.
        self.gpib.write("UNIT:POW W") # TODO: do we want watts or dB?

        # Sets the data format to ASC; this means the result is human-readable and convertible by standard library functions.
        # (It also is possible to do "FORM REAL" - This makes the meter to output an IEEE-754 floating point number)
        self.gpib.write("FORM ASC")

        # Fetches the reading.
        return self.gpib.read("FETC?")

    def measure(self):
        # Presets the U2020 X-Series to default values.
        self.gpib.write("SYST:PRES") 

        # Sets the frequency to 50 MHz.
        self.gpib.write("SENS:FREQ 50MHz") 

        # Initiates the trigger sequence.
        self.gpib.write("INIT:CONT ON") 

        # Sets the power measurement unit for CALC1 to W.
        self.gpib.write("UNIT:POW DBM") 

        # Sets the data format to REAL.
        self.gpib.write("FORM REAL") 

        # Disables auto-zeroing.
        self.gpib.write("CAL:ZERO:AUTO OFF") 

        # Disables auto-calibration.
        self.gpib.write("CAL:AUTO OFF") 

        # Disables step detection.
        self.gpib.write("SENS:AVER:SDET OFF") 

        # Sets the measurement mode to normal.
        self.gpib.write("SENS:DET:FUNC NORM") 

        # Sets the measurement speed to fast mode.
        self.gpib.write("SENS:MRAT FAST") 

        # Sets the buffer size of the U2020 X-Series to 100 to store 100 measurement readings.
        self.gpib.write("TRIG:COUN 100") 

        # Fetches the reading.
        return self.gpib.read("FETC?") 


