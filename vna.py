from collections import namedtuple
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
import sys
import os
import time

class network_analyser_t(object):

    @property
    def start_freq(self):
        raise NotImplementedError

    @start_freq.setter
    def start_freq(self, freq):
        raise NotImplementedError

    @property
    def stop_freq(self):
        raise NotImplementedError

    @stop_freq.setter
    def stop_freq(self, freq):
        raise NotImplementedError

    @property
    def power_level(self):
        raise NotImplementedError

    @power_level.setter
    def power_level(self, level):
        raise NotImplementedError

    @property
    def sweep_pnt_count(self):
        raise NotImplementedError

    @sweep_pnt_count.setter
    def sweep_pnt_count(self, pnts):
        raise NotImplementedError

    @property
    def rf_power(self):
        raise NotImplementedError

    @rf_power.setter
    def rf_power(self, enable):
        raise NotImplementedError

    def set_marker(self, freq):
        raise NotImplementedError

    def read_marker(self):
        raise NotImplementedError

    def do_sweep(self):
        raise NotImplementedError

class hp8720d(network_analyser_t, ieee488_t):
    def __init__(self, f):
        self.gpib = f
        self.mstart_freq = 0
        self.mstop_freq = 0
        self.mpower_level = 0
        self.gpib.read("OPC?;PRES;CHAN2;REFP9;")
        self.gpib.read("OPC?;SING;")
        self.gpib.readline()

    def cal(self, slot):
        self.gpib.write("RECA%u;" % slot)

    def frequencyformat(self, freq):
        if freq % (1000 * 1000 * 1000) == 0:
            return "%d ghz" % (freq / (1000 * 1000 * 1000))
        if freq % (1000 * 1000) == 0:
            return "%d mhz" % (freq / (1000 * 1000))
        if freq % (1000) == 0:
            return "%d khz" % (freq / (1000))
        return "%d hz" % freq

    @property
    def start_freq(self):
        return self.mstart_freq

    @start_freq.setter
    def start_freq(self, freq):
        assert freq > 50000000, "The device does not support frequencies below 50MHz."
        assert freq < 20000000000, "The device does not support frequencies above 20GHz"
        self.mstart_freq = freq
        self.gpib.write("STAR%s;" % self.frequencyformat(freq))

    @property
    def stop_freq(self):
        return self.mstop_freq

    @stop_freq.setter
    def stop_freq(self, freq):
        assert freq > 50000000, "The device does not support frequencies below 50MHz."
        assert freq < 20000000000, "The device does not support frequencies above 20GHz"
        self.mstop_freq = freq
        self.gpib.write("STOP%s;" % self.frequencyformat(freq))

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
