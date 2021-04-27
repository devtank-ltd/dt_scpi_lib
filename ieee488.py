from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.parameter import *

class ieee488_t(object):
    # IEEE-488.2 - http://rfmw.em.keysight.com/rfcomms/refdocs/gsm/hpib_common.html
    def __init__(self):
        self.idn = constant_t(self, "*IDN?")
        self.opt = constant_t(self, "*OPT?")
        self.sre = constant_t(self, "*SRE?")
        self.ese = parameter_t(self, lambda _: "*ESE", getter="*ESE?")
        self.opc = parameter_t(self, lambda _: "*OPC", getter="*OPC?")

    def cls(self):
        self.substrate.write("*CLS")

    def esr(self):
        return self.substrate.read("*ESR?");

    def rst(self):
        self.substrate.write("*RST")

    def stbQ(self):
        return self.substrate.write("*STB?")


class scpi_t(ieee488_t):

    def __init__(self):
        super().__init__()

    def system_error(self):
        return self.gpib.read("SYSTem:ERRor:NEXT?")

    def system_version(self):
        return self.gpib.read("SYSTem:VERSion?")


