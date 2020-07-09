from collections import namedtuple
import sys
import os
import time

class sig_gen_t(object):
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
    def freq(self, freq):
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

class scpi_sig_gen(sig_gen_t):
    def __init__(self, tty):
        self.gpib = tty
        self.mfreq = 0
        self.mrf_power = False
        self.mpower_level = 0

    def idn(self):
        return self.gpib.read("*idn?;i\n")

    @property
    def rf_power(self):
        return self.mrf_power
   
    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable
        self.gpib.write("outp %s;\n" % ("1" if enable else "0"))

    @property
    def freq(self):
        return self.mfreq
    
    @freq.setter
    def freq(self, freq):
        self.mfreq = freq
        self.gpib.write("freq %fGHz;\n" % (freq/float((1000.0*1000.0*1000.0))))
    
    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write("pow %d;\n" % level)

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

