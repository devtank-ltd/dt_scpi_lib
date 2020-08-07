from collections import namedtuple
import sys
import os
import time

class ieee488_t(object):

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

