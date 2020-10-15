from collections import namedtuple
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
import sys
import os
import time

class power_meter_t(ieee488_t):
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

class u2020_t(scpi_t):
    def __init__(self, gpib):
        self.gpib = gpib
        
        # Do the same as what the pcap dump from Thomas does
        ignore_me = self.idn
        self.opc()
        self.cls()
        self.esr()
        self.rst()
        self.esr()
        
        self.unit_power_q()
        self.unit_power_watts()
        self.esr()

    def system_error(self):
        # Overridden because this power meter works subtly differently from the SCPI standard
        # and so does not support the :NEXT query of the SYSTem:ERRor subsystem
        return self.gpib.read("SYSTem:ERRor?")

    def unit_power_q(self):
        return self.gpib.read("UNIT1:POW?")
    def unit_power_db(self):
        self.gpib.read("UNIT1:POW DB")
    def unit_power_watts(self):
        self.gpib.read("UNIT1:POW W")

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
        self.gpib.write("SENS:SWE:OFFS:TIME %f" % delay)

        # Set the duration of the time-gated period
        self.gpib.write("SENS:SWE:TIME %f" % time)

        # Sets the power measurement unit for CALC1 to W.
        self.gpib.write("UNIT:POW W") # TODO: do we want watts or dB?

        # Sets the data format to ASC; this means the result is human-readable and convertible by standard library functions.
        # (It also is possible to do "FORM REAL" - This makes the meter to output an IEEE-754 floating point number)
        self.gpib.write("FORM ASC")

        # Fetches the reading.
        return self.gpib.read("FETC?")

    def measure(self, frequency):
        # Presets the U2020 X-Series to default values.
        self.gpib.write("SYST:PRES") 

        # Sets the frequency to 50 MHz.
        self.gpib.write("SENS:FREQ %d" % frequency) 

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


