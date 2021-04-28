from collections import namedtuple
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
from dt_scpi_lib.parameter import *
import sys
import os
import time

class power_meter_t(ieee488_t):
    @property
    def voltage(self):
        raise NotImplementedError

    @voltage.setter
    def voltage(self, enable):
        raise NotImplementedError

    @property
    def current_limit(self):
        raise NotImplementedError

    @current_limit.setter
    def current_limit(self, i):
        raise NotImplementedError

    @property
    def current(self):
        raise NotImplementedError

class u2020_t(scpi_t):

    peak_power = "POW:PEAK"
    peak_to_average_power = "POW:PTAV"
    average_power = "POW:AVER"
    minimum_power = "POW:MIN"
    
    def __init__(self, serial):
        self.substrate = serial
        self.frequency = frequency_t(memoizing_parameter_t(self, lambda hz: "SENS:FREQ %dHz; " % hz))
        self.averaging = memoizing_parameter_t(self, lambda boolean: "SENS1:AVER %d" % (1 if boolean else 0))
        super().__init__()
        
        # Do the same as what the pcap dump from Thomas does
        ignore_me = self.idn
        self.opc()
        self.cls()
        self.esr()
        self.rst()
        self.esr()
        
        self.unit_power_q(1)
        self.unit_power_db(1)
        self.esr()
        self.list_errors()

    def system_error(self):
        # Overridden because this power meter works subtly differently from the SCPI standard
        # and so does not support the :NEXT query of the SYSTem:ERRor subsystem
        return self.substrate.read("SYSTem:ERRor?")

    def unit_power_q(self, unit):
        return self.substrate.read("UNIT%d:POW?" % unit)
    def unit_power_db(self, unit):
        self.substrate.write("UNIT%d:POW DBM" % unit)
    def unit_power_watts(self, unit):
        self.substrate.write("UNIT%d:POW W" % unit)

    def calc_math_expression(self, block, expr):
        return self.substrate.write("CALC%d:MATH \"%s\"" % (block, expr))

    def calc_math_expressionQ(self, block):
        return self.substrate.read("CALC%d:MATH?" % block)

    def calc_math_feedQ(self, block, feed):
        return self.substrate.read("CALC%d:FEED%d?" % (block, feed))

    def calc_math_feed(self, block, feed, f, sweep = None):
        if sweep is None:
            self.substrate.write("CALC%d:FEED%d \"%s\"" % (block, feed, f))
        else:
            self.substrate.write("CALC%d:FEED%d \"%s ON SWEEP %d\"" % (block, feed, f, sweep))

    def conf(self, block):
        return self.substrate.read("CONF%d?" % block)

    def trigger_single(self):
        self.substrate.write("INIT1:CONT 0")
        self.substrate.write("TRIG:DEL:AUTO 0")

    def trigger_continuous(self):
        self.substrate.write("INIT1:CONT 1")
        self.substrate.write("TRIG:DEL:AUTO 0")

    def cal_zero(self):
        self.substrate.write("CAL:AUTO ONCE")
        self.substrate.write("CAL:ZERO:AUTO ONCE")

    def list_errors(self):
        error = ""
        while not error.startswith("+0"):
            error = self.system_error()

    def calibrate(self):
        self.substrate.write("CAL1:ALL")
        self.system_error()

    def setup_customer_padcal(self):
        self.trigger_single()
        for b in [1, 2, 3, 4]:
            self.unit_power_db(b)
            self.substrate.read("CALC%d:MATH?" % b)
            self.substrate.read("CALC%d:FEED1?" % b)
            self.substrate.read("CALC%d:FEED2?" % b)
        self.substrate.write("TRAC1:MEAS:TILT:UNIT PCT")
        self.calc_math_feed(1, 1, "POW:AVER")
        self.calc_math_feed(1, 2, "POW:AVER")
        self.calc_math_expression(1, "(SENS1)")
        self.calc_math_feed(2, 1, "POW:PEAK")
        self.calc_math_feed(2, 2, "POW:AVER")
        self.calc_math_expression(2, "(SENS1)")
        self.substrate.write("SENS1:AVER 0")
        # I am fairly certain that all of the following is unnecessary.
        self.substrate.write("TRAC1:MEAS:TILT:UNIT PCT")
        self.substrate.write("TRIG1:DEL:AUTO 0")
        for t in ["TRAC1:UNIT?", "TRAC1:STAT?", "TRAC1:DEF:TRAN:REF?", "TRAC1:DEF:DUR:REF?", "SENS1:BAND:VID?", "PST1:CCDF:DAT:MAX?", "SENS1:AVER?" ,
                "SENS1:AVER:COUN:AUTO?", "SENS1:AVER:COUN?", "SENS1:CORR:GAIN2:STAT?", "SENS1:CORR:GAIN2?", "SENS1:AVER:SDET?", "SENS1:FREQ?", "SENS1:AVER2:COUNT?", "SENS1:AVER2:STATE?",
                "INIT1:CONT?", "TRIG1:DEL:AUTO?", "TRIG1:SOUR?", "OUTP:REC1:STAT?", "OUTP:REC1:LIM:LOW?", "SERV:BIST:VID:STAT?"]:
            self.substrate.read(t)
        
        self.calibrate()

    def read(self, ch):
        return float(self.substrate.read("READ%d?" % ch))

