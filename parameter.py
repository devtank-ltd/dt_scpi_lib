from collections import namedtuple
import sys
import os
import time

class parameter_t(object):
    """
    Use in objects representing test & measurement devices
    """
    def __init__(self, parent, setter, getter=None):
        self.parent = parent
        self.setter = setter
        self.getter = getter
        self.minimum, self.maximum, self.value = None, None, None

    def query(self):
        return self.parent.substrate.read(self.getter)

    def get(self):
        self.value = self.query()
        return self.value

    def boundscheck(self, value):
        assert self.minimum is None or value >= self.minimum
        assert self.maximum is None or value <= self.maximum

    def set(self, value):
        self.boundscheck(value)
        self.parent.substrate.write(self.setter(value))

    def __str__(self):
        return self.get()

    def __call__(self, val=None):
        if val is not None:
            self.set(val)
        return self.get()

class memoizing_parameter_t(parameter_t):

    def __init__(self, parent, setter, getter=None):
        super().__init__(parent, setter, getter)
        self.ready = False

    def get(self):
        if self.ready:
            return self.value
        else:
            super().get()
            self.ready = True
            return self.value

    def set(self, value):
        self.ready = True
        self.value = value
        super().set(value)

class requerying_parameter_t(parameter_t):
    # Some instruments don't actually set the thing until you query it. 
    # We may never know why
    def set(self, value):
        while super().query() != value: # Fix for some instruments that don't always
            self.super().substrate.write(self.setter(value))
        self.value = self.query()


class constant_t(memoizing_parameter_t):
    def __init__(self, parent, getter):
        super().__init__(parent, None, getter)

    def set(self, value):
        raise Exception("This parameter cannot be set")

    def get(self):
        return super().get()

class integer_constant_t(constant_t):
    def get(self):
        return int(super().get())

class lockable_parameter_t(parameter_t):
    """
    Use in client code that needs to set a parameter on several instruments at
    once.
    Example: a test needs to run at a given frequency. So you need to change
    the signal generator's frequency, and the cursor on the VNA, and at the
    same time send a trigger command to the oscilloscope.
    The way you can do that is instantiate an object of this class, and add to
    it the VNA's cursor, the sig gen's baseband frequency and the scope's
    trigger, and then assign a frequency to it by calling set(something). This
    last operation will assign the frequency to all the others, taking care of
    bounds checking, device quirks, and what have you.
    """
    def __init__(self, locklist = None):
        self.ready = False
        self.value = None
        self.locklist = locklist
        if self.locklist is None:
            self.locklist = []

    def append(self, lock):
        self.locklist.append(lock)

    def get(self):
        if self.ready:
            return self.value
        else:
            self.value = self.parent.read(self.getter())
            self.ready = True
            return self.value

    def set(self, value):
        print("lockable_parameter_t.set(%f)" % value)
        self.ready = False
        self.value = value
        for l in self.locklist:
            l.set(value)

class frequency_t(parameter_t):
    def __init__(self, param):
        self.param = param

    def __getattr__(self, name):
        return getattr(self.param, name)

    @property
    def hz(self):
        return self.get()

    @hz.setter
    def hz(self, value):
        self.set(value)

    @property
    def khz(self):
        return self.hz / 1000.0

    @khz.setter
    def khz(self, value):
        self.hz = value * 1000

    @property
    def mhz(self):
        return self.khz / 1000.0

    @khz.setter
    def mhz(self, value):
        self.khz = value * 1000

    @property
    def ghz(self):
        return self.mhz / 1000.0

    @ghz.setter
    def ghz(self, value):
        self.mhz = value * 1000

class timespan_t(parameter_t):
    def __init__(self, param):
        self.param = param

    def __getattr__(self, name):
        return getattr(self.param, name)

    @property
    def milliseconds(self):
        return self.get()

    @milliseconds.setter
    def milliseconds(self, value):
        self.set(value)

    @property
    def seconds(self):
        return self.ms / 1000.0

    @seconds.setter
    def seconds(self, value):
        self.ms = value * 1000
