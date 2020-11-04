from collections import namedtuple
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
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
    
    def __init__(self, gpib):
        self.gpib = gpib
        
        # Do the same as what the pcap dump from Thomas does
        ignore_me = self.idn
        self.opc()
        self.cls()
        self.esrQ()
        self.rst()
        self.esrQ()
        
        self.unit_power_q(1)
        self.unit_power_db(1)
        self.esrQ()
        self.list_errors()

    def system_error(self):
        # Overridden because this power meter works subtly differently from the SCPI standard
        # and so does not support the :NEXT query of the SYSTem:ERRor subsystem
        return self.gpib.read("SYSTem:ERRor?")

    def unit_power_q(self, unit):
        return self.gpib.read("UNIT%d:POW?" % unit)
    def unit_power_db(self, unit):
        self.gpib.write("UNIT%d:POW DB" % unit)
    def unit_power_watts(self, unit):
        self.gpib.write("UNIT%d:POW W" % unit)

    @property
    def frequency(self):
        return float(self.gpib.read("SENS1:FREQ?"))

    @frequency.setter
    def frequency(self, freq):
        self.gpib.write("SENS:FREQ %d" % freq)

    def calc_math_expression(self, block, expr):
        return self.gpib.read("CALC%d:MATH \"%s\"" % block)

    def calc_math_expressionQ(self, block):
        return self.gpib.read("CALC%d:MATH?" % block)

    def calc_math_feedQ(self, block, feed):
        return self.gpib.read("CALC%d:FEED%d?" % (block, feed))

    def calc_math_feed(self, block, feed, f, sweep = None):
        if sweep is None:
            self.gpib.write("CALC%d:FEED%d \"%s\"" % (block, feed, f))
        else:
            self.gpib.write("CALC%d:FEED%d \"%s ON SWEEP %d\"" % (block, feed, f, sweep))

    def conf(self, block):
        return self.gpib.read("CONF%d?" % block)

    def trigger_single(self):
        self.gpib.write("INIT1:CONT 0")
        self.gpib.write("TRIG:DEL:AUTO 0")

    def trigger_continuous(self):
        self.gpib.write("INIT1:CONT 1")
        self.gpib.write("TRIG:DEL:AUTO 0")

    def cal_zero(self):
        self.gpib.write("CAL:AUTO ONCE")
        self.gpib.write("CAL:ZERO:AUTO ONCE")

    def list_errors(self):
        while self.esrQ() == "+16":
            self.system_error()

    def calibrate(self):
        self.gpib.write("CAL1:ALL")
        self.system_error()

    def setup_customer_padcal(self):
        self.trigger_single()
        for b in [1, 2, 3, 4]:
            self.gpib.write("UNIT%d:POW W" % b)
            self.gpib.read("CALC%d:MATH?" % b)
            self.gpib.read("CALC%d:FEED1?" % b)
            self.gpib.read("CALC%d:FEED2?" % b)
        self.gpib.write("SENS1:AVER:COUN 8")
        self.gpib.write("TRAC1:MEAS:TILT:UNIT PCT")
        self.calc_math_feed(1, 1, "POW:AVER")
        self.calc_math_feed(1, 2, "POW:AVER")
        self.calc_math_expression(1, "(SENS1)")
        self.calc_math_feed(2, 1, "POW:PEAK")
        self.calc_math_feed(2, 2, "POW:AVER")
        self.calc_math_expression(2, "(SENS1)")
        # I am fairly certain that all of the following is unnecessary.
        for t in ["TRAC1:UNIT?", "TRAC1:STAT?", "TRAC1:DEF:TRAN:REF?", "TRAC1:DEF:DUR:REF?", "TRAC1:MEAS:TILT:UNIT PCT", "SENS1:BAND:VID?", "PST1:CCDF:DAT:MAX?", "SENS1:AVER?" ,
                "SENS1:AVER:COUN:AUTO?", "SENS1:AVER:COUN?", "SENS1:CORR:GAIN2:STAT?", "SENS1:CORR:GAIN2?", "SENS1:AVER:SDET?", "SENS1:FREQ?", "SENS1:AVER2:COUNT?", "SENS1:AVER2:STATE?",
                "TRIG1:DEL:AUTO 0", "INIT1:CONT?", "TRIG1:DEL:AUTO?", "TRIG1:SOUR?", "OUTP:REC1:STAT?", "OUTP:REC1:LIM:LOW?", "SERV:BIST:VID:STAT?"
            self.gpib.read(t)
        
        self.calibrate()

    def read(self, ch):
        return float(self.gpib.read("READ%d?" % ch))

