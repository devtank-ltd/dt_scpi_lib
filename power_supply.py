from collections import namedtuple
import sys
import os
import time

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

class thurlby_pl330(power_supply_t):
    def __init__(self, chan, tty):
        self.gpib = tty
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

class n6700(power_supply_t):
    def __init__(self, chan, gpib):
        self.gpib = gpib
        self.chan = chan
        self.mcurrent_limit = 0;
        self.mvoltage = 0;

    @property
    def voltage(self, v):
        return self.mvoltage

    @voltage.setter
    def voltage(self, enable):
        self.mvoltage = v
        self.gpib.write("VOLT %f,(@%u)" % (v, self.chan))

    @property
    def current_limit(self):
        return self.mcurrent_limit

    @current_limit.setter
    def current_limit(self, i):
        self.mcurrent_limit = i
        self.gpib.write("CURRent:LIMit %f,(@%u)" % (i, self.chan))
