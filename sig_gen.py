from dt_scpi_lib.parameter import *
from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t

class sig_gen_t(ieee488_t):
    @property
    def rf_power(self):
        raise NotImplementedError

    @rf_power.setter
    def rf_power(self, enable):
        raise NotImplementedError

    @property
    def freq(self):
        raise NotImplementedError

    @freq.setter
    def frequency(self, freq):
        raise NotImplementedError

    @property
    def power_level(self):
        raise NotImplementedError

    @power_level.setter
    def power_level(self, level):
        raise NotImplementedError


class hmct2220(sig_gen_t):
    def __init__(self, tty):
        self.gpib = tty
        self.mrf_power = False
        self.mfreq = 0
        self.mpower_level = 0

    def frequencyformat(self, freq):
        if freq % (1000 * 1000 * 1000) == 0:
            return "%dghz" % (freq / (1000 * 1000 * 1000))
        if freq % (1000 * 1000) == 0:
            return "%dmhz" % (freq / (1000 * 1000))
        if freq % (1000) == 0:
            return "%dkhz" % (freq / (1000))
        return "%dhz" % freq

    def gpib_rf(self):
        return "outp " + ("on" if self.mrf_power else "off") + ";"

    def gpib_freq(self):
        return "freq " + self.frequencyformat(self.mfreq) + ";"

    def gpib_pow(self):
        return "pow " + str(self.mpower_level) + "dBm;"

    def quickie(self, frequency, powerlevel, enable):
        self.mrf_power = enable
        self.mfreq = frequency
        self.mpower_level = powerlevel
        # The datasheet says it's worth putting all these commands on one line because "optimisation".
        # That's because all three commands affect the attenuators. See point 3.3.20.2.
        self.gpib.write("".join([self.gpib_freq(), self.gpib_pow(), self.gpib_rf()]))
        self.gpib.read("SYST:ERR?")

    def serialnumber(self):
        return self.gpib.read("*idn?;").split(",")[2]

    @property
    def rf_power(self):
        return self.mrf_power

    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable
        self.gpib.write(self.gpib_rf())

    @property
    def freq(self):
        return self.mfreq
    
    @freq.setter
    def freq(self, freq):
        self.mfreq = freq
        self.gpib.write(self.gpib_freq())

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write(self.gpib_pow())

class fake_sig_gen(sig_gen_t):
    def __init__(self):
        self.mfreq = 0
        self.mrf_power = False
        self.mpower_level = 0

    def idn(self):
        return "Devtank Fake Signal Generator"

    @property
    def rf_power(self):
        return self.mrf_power
   
    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable

    @property
    def freq(self):
        return self.mfreq
    
    @freq.setter
    def freq(self, freq):
        self.mfreq = freq
    
    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level

class scpi_sig_gen(scpi_t):
    def __init__(self, substrate):
        super().__init__()
        #self.frequency = frequency_t(memoizing_parameter_t(substrate, lambda hz: "freq %dHz; " % hz))
        self.frequency = frequency_t(requerying_parameter_t(substrate, lambda hz: "SOUR1:FREQ %dHz; " % hz, getter="SOUR1:FREQ?"))
        self.substrate = substrate
        self.mrf_power = False
        self.mpower_level = 0

    @property
    def rf_power(self):
        return self.mrf_power
   
    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable
        self.substrate.write("outp %s;" % ("1" if enable else "0"))

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.substrate.write("pow %f;" % level)

    def freqQ(self):
        return int(self.substrate.read("freq?;"))


class smbv100a(scpi_sig_gen):
    def __init__(self, tty):
        self.gpib = tty
        super().__init__()
        self.mfreq = 0
        self.mrf_power = False

    def single_pulse(self, period, width):
        # period is specified in nanoseconds,
        # width ditto.
        def durstr(ns):
            if ns > 1000:
                return "%d us" % int(ns / 1000)
            else:
                return "%d ns" % int(ns)

        self.gpib.write(":PULM:MODE SING")
        self.gpib.write("PULM:PER %s" % durstr(period))
        self.gpib.write("PULM:WIDT %s" % durstr(width))
        self.gpib.write("PULM:STAT ON")

    def continuous_wave(self):
        self.gpib.write("PULM:STAT OFF") # turn off PWM.

    def screenshot(self, filename):
        self.gpib.write(":HCOPy:DEVice:LANGuage PNG")
        self.gpib.write(":HCOPy:FILE:NAME:AUTO:STATe 1")
        self.gpib.write(":HCOPy:REGion ALL")
        self.gpib.write(":HCOPy:EXECute")
        self.gpib.read(":HCOPy:FILE:AUTO:FILE?")
        self.gpib.write(":HCOPy:DATA?")
        data = self.gpib.readblock()
        with open(filename, "w+b") as scrshot:
            scrshot.write(data)

    def save(self, slot):
        self.gpib.write("*SAV %d" % slot)
    def recall(self, slot):
        self.gpib.write("*RCL %d" % slot)

class smw200a(scpi_sig_gen):
    def __init__(self, substrate):
        super().__init__(substrate)
        self.substrate = substrate
        self.substrate.timeout = 10
        self.mfreq = 0
        self.mrf_power = False
        self.frequency = frequency_t(requerying_parameter_t(substrate, lambda hz: "SOUR1:FREQ %dHz; " % hz, getter="SOUR1:FREQ?"))

    def single_pulse(self, period, width):
        # period is specified in nanoseconds,
        # width ditto.
        def durstr(ns):
            if ns > 1000:
                return "%d us" % int(ns / 1000)
            else:
                return "%d ns" % int(ns)

        self.substrate.write(":PULM:MODE SING")
        self.substrate.write("PULM:PER %s" % durstr(period))
        self.substrate.write("PULM:WIDT %s" % durstr(width))
        self.substrate.write("PULM:STAT ON")

    def continuous_wave(self):
        self.substrate.write("PULM:STAT OFF") # turn off PWM.

    def screenshot(self, filename):
        self.substrate.write(":HCOPy:DEVice:LANGuage PNG")
        self.substrate.write(":HCOPy:FILE:NAME:AUTO:STATe 1")
        self.substrate.write(":HCOPy:REGion ALL")
        self.substrate.write(":HCOPy:EXECute")
        self.substrate.read(":HCOPy:FILE:AUTO:FILE?")
        self.substrate.write(":HCOPy:DATA?")
        data = self.substrate.readblock()
        with open(filename, "w+b") as scrshot:
            scrshot.write(data)

    def system_errors_all(self):
        return self.substrate.read(":SYSTem:ERRor:ALL?")
    def save(self, slot):
        self.substrate.write("*SAV %d" % slot)
    def recall(self, slot):
        self.substrate.write("*RCL %d" % slot)
        

class hp8648(sig_gen_t):
    def __init__(self, tty):
        self.gpib = gpib_device(tty, 5)
        self.mfreq = 0
        self.mrf_power = False
        self.mpower_level = 0

    @property
    def rf_power(self):
        return self.mrf_power
   
    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable
        if enable:
            self.gpib.write("pow:enab 1;")
        else:
            self.gpib.write("pow:enab 0;")

    @property
    def freq(self):
        return self.mfreq
    
    @freq.setter
    def freq(self, freq):
        self.mfreq = freq
        self.gpib.write("fm:int:freq %d hz;" % freq)
    
    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write("fm:pow:ampl %d db;" % level)


