from collections import namedtuple
import sys
import os
import time

class ieee488_t(object):

    # IEEE-488.2 - http://rfmw.em.keysight.com/rfcomms/refdocs/gsm/hpib_common.html
    @property
    def idn(self):
        return self.gpib.read("*idn?")

    @idn.setter
    def idn(self, enable):
        raise NotImplementedError

    def opc(self):
        self.gpib.write("*opc")

    @property
    def opc(self):
        self.gpib.write("*opc?")

    def cls(self):
        self.gpib.write("*cls")

    def rst(self):
        self.gpib.write("*rst")


class scpi_t(ieee488_t):

    def system_error(self):
        return self.gpib.read("SYSTem:ERRor")

    def system_version(self):
        return self.gpib.read("SYSTem:VERSion")


