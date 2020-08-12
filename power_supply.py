from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t

class power_supply_t(object):
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

class thurlby_pl330(ieee488_t):
    def __init__(self, chan, gpib):
        self.gpib = gpib
        self.chan = chan
        self.mcurrent_limit = 0
        self.mvoltage = 0

    @property
    def voltage(self, v):
        return self.mvoltage

    @voltage.setter
    def voltage(self, v):
        self.mvoltage = v
        self.gpib.write("V%uV %f\n" % (self.chan, v))

    @property
    def current_limit(self):
        return self.mcurrent_limit

    @current_limit.setter
    def current_limit(self, i):
        self.mcurrent_limit = i
        self.gpib.write("I%u %f\n" % (self.chan, i))

class n6700(scpi_t):
    def __init__(self, chan, gpib):
        self.gpib = gpib
        self.chan = chan
        self.mcurrent_limit = 0;
        self.mvoltage = 0;

    @property
    def voltage(self):
        return self.mvoltage

    @voltage.setter
    def voltage(self, volts):
        self.mvoltage = volts
        self.gpib.write("VOLT %f,(@%u)" % (volts, self.chan))

    @property
    def current_limit(self):
        return self.mcurrent_limit

    @current_limit.setter
    def current_limit(self, i):
        self.mcurrent_limit = i
        self.gpib.write("CURRent:LIMit %f,(@%u)" % (i, self.chan))

    @property
    def current(self):
        return float(self.gpib.read("MEASure:CURRent?,(@%u)" % self.chan))
