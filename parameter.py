from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t

class parameter_t(object):

    def __init__(self, parent, lambda setter, lambda getter):
        self.parent = parent
        self.setter = setter
        self.getter = getter
        self.ready = False
        self.value = None
        self.locklist = []

    def addlock(self, lock):
        self.locklist.append(lock)

    def get(self):
        if self.ready:
            return self.value
        else:
            self.value = self.parent.read(self.getter())
            self.ready = True
            return self.value

    def set(self, value):
        self.ready = False
        self.value = value
        self.parent.write(self.setter(value))
        
        for l in self.locklist:
            l.set(value)


