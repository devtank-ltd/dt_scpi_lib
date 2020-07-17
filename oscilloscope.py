from collections import namedtuple
import sys
import os
import time

class oscilloscope_t(object):

    def run():
        self.gpib.write(":run")

    def stop():
        self.gpib.write(":stop")

    def idn(self):
        return self.gpib.read("*idn?;")

class rigol_ds1000z_t(oscilloscope_t):

    d0 = "D0"
    d1 = "D1"
    d2 = "D2"
    d3 = "D3" # These go all the way up to 15 but I can't be bothered to type.
    channel1 = "CHAN1"
    channel2 = "CHAN2"
    channel3 = "CHAN3"
    channel4 = "CHAN4"
    ac = "AC"

    rising = "POS"
    falling = "NEG"
    rising_falling = "RFALI"

    def __init__(self, f):
        self.gpib = f

    def is_channel(self, name):
        return name in [d0, d1, d2, d3, channel1, channel2, channel3, channel3, ac]

    def trigger_single(self):
        self.gpib.write(":SINGle")

    def trigger_force(self):
        self.gpib.write(":TFORce")

    def trigger_edge(self, source, edge_type): 
        assert(is_channel(source))
        self.gpib.write(":TRIGger:MODe EDGE")
        self.gpib.write(":TRIGger:EDGe:SOURce %s" % source)
        self.gpib.write(":TRIGger:EDGe:SLOPe %s" % edge_type)


