from collections import namedtuple
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
from dt_scpi_lib.parameter import *
import sys
import os
import time

class hp8720d(ieee488_t):
    def __init__(self, f):
        self.gpib = f
        self.mpower_level = 0
        self.gpib.write("DEBU1;") # debugging info on VNA's screen
        self.gpib.write("*RST;")
       # self.gpib.read("OPC?;PRES;CHAN2;REFP9;")
        #self.gpib.read("OPC?;SING;")
        self.start_freq = frequency_t(memoizing_parameter_t(f, lambda hz: "STAR%d HZ;" % hz))
        self.stop_freq = frequency_t(memoizing_parameter_t(f, lambda hz: "STOP%d HZ;" % hz))
        self.start_freq.maximum = 20000000000
        self.start_freq.minimum = 50000000
        self.stop_freq.maximum = 20000000000
        self.stop_freq.minimum = 50000000

    def cal(self, slot):
        self.gpib.write("RECA%u;" % slot)

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write("POWE %d dB;" % level)

    @property
    def sweep_pnt_count(self):
        return self.msweep_pnt_count

    @sweep_pnt_count.setter
    def sweep_pnt_count(self, pnts):
        # TODO According to datasheet, this ought to be followed by a wait of two sweeps.
        self.msweep_pnt_count = pnts
        self.gpib.write("POIN%d;" % pnts)

    @property
    def rf_power(self):
        raise NotImplementedError

    @rf_power.setter
    def rf_power(self, enable):
        self.gpib.write("POWT " + ("OFF" if enable else "ON") + ";")

    def set_marker(self, point):
        assert point > self.start_freq, "Marker out of range"
        assert point < self.stop_freq, "Marker out of range"
        self.gpib.write("MARKCONT;")
        self.gpib.write("MARK1%d;" % point)
        self.gpib.read("OPC?;WAIT;")
        self.gpib.readline()

    def read_marker(self):
        self.gpib.write("MARK1;")
        # The network analyser will return three values separated by commas,
        # The first value is the gain in dBm
        # The second value is not significant
        # The third value is the marker's frequency (horizontal position on the display)
        return float(self.gpib.read("OUTPMARK;").split(',')[0].strip())

    def serial_number(self):
        return self.gpib.read("outpsern;")

    def do_sweep(self):
        self.gpib.write("REST;")

    def get_sweep(self):
        debug_print("Raw offsets: %s" % self.gpib.read("rawoffs?;"))

    def rf_power(self, enable):
        self.mrf_power = enable
        self.gpib.write(self.gpib_rf())

    @property
    def freq(self):
        return self.mfreq
    
    @freq.setter
    def freq(self, freq):
        self.mfreq = freq
        self.gpib.write(self.gpib_freq())

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write(self.gpib_pow())
