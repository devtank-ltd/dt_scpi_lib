from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t

class multimeter_t(object):

    def run():
        self.gpib.write(":run")

    def stop():
        self.gpib.write(":stop")

    @property
    def idn(self):
        return self.gpib.read("*idn?")

    @idn.setter
    def idn(self, enable):
        raise NotImplementedError

class keithley2110(scpi_t):

    def __init__(self, f):
        self.gpib = f
   
    def display(self, message):
        self.gpib.write(":DISPlay:TEXT \"%s\"" % message)

    def display_clear(self):
        self.gpib.write(":DISPlay:TEXT:CLEar")

    def display_enable(self, onoff):
        self.gpib.write(":DISPlay %u" % (1 if onoff else 0))

    def dc_voltage(self):
        self.gpib.write('FUNCtion "VOLTage:DC"')
        self.gpib.write('VOLT:RANGe:AUTO 1')
        return float(self.gpib.read("READ?"))

    def ac_voltage(self):
        self.gpib.write('FUNCtion "VOLTage:AC"')
        self.gpib.write('VOLT:RANGe:AUTO 1')
        return float(self.gpib.read("READ?"))

    def dc_current(self):
        self.gpib.write('FUNCtion "CURRent:DC"')
        self.gpib.write('CURR:RANGe:AUTO 1')
        return float(self.gpib.read("READ?"))

    def ac_current(self):
        self.gpib.write('FUNCtion "CURRent:AC"')
        self.gpib.write('CURR:RANGe:AUTO 1')
        return float(self.gpib.read("READ?"))

    def system_error(self):
        return float(self.gpib.read(":SYSTem:ERRor?"))
