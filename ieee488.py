from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.parameter import *

class ieee488_t(object):
    # IEEE-488.2 - http://rfmw.em.keysight.com/rfcomms/refdocs/gsm/hpib_common.html
    def __init__(self):
        self.idn = constant_t(self)
        self.idn.getter = "*IDN?"
        self.idn.__str__ = lambda: self.idn.get()

        self.opt = constant_t(self)
        self.opt.getter = "*OPT?"
        self.opt.__str__ = lambda: self.opt.get()

        self.sre = constant_t(self)
        self.sre.getter = "*SRE?"
        self.sre.__str__ = lambda: self.sre.get()

        self.ese = parameter_t(self, lambda _: "*ESE")
        self.ese.getter = "*ESE?"

        self.opc = parameter_t(self, lambda _: "*OPC")
        self.opc.getter = "*OPC?"

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


