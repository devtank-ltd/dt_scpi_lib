from collections import namedtuple
import sys
import os
import time

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
        self.gpib.write("*CLS")

    def esr(self):
        return self.gpib.read("*ESR?");

    def rst(self):
        self.gpib.write("*RST")

    def stbQ(self):
        return self.gpib.write("*STB?")


class scpi_t(ieee488_t):

    def system_error(self):
        return self.gpib.read("SYSTem:ERRor:NEXT?")

    def system_version(self):
        return self.gpib.read("SYSTem:VERSion?")


