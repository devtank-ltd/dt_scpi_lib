from collections import namedtuple
import sys
import os
import time

class ieee488_t(object):

    # IEEE-488.2 - http://rfmw.em.keysight.com/rfcomms/refdocs/gsm/hpib_common.html
    @property
    def idn(self):
        return self.gpib.read("*IDN?")

    @idn.setter
    def idn(self, enable):
        raise NotImplementedError

    def opc(self):
        self.gpib.write("*OPC")

    def opcQ(self):
        self.gpib.write("*OPC?")

    def cls(self):
        self.gpib.write("*CLS")

    def rst(self):
        self.gpib.write("*RST")

    def stbQ(self):
        self.gpib.write("*STB?")


class scpi_t(ieee488_t):

    def system_error(self):
        return self.gpib.read("SYSTem:ERRor:NEXT?")

    def system_version(self):
        return self.gpib.read("SYSTem:VERSion?")


