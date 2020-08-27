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

class tektronix_tds(oscilloscope_t):

    channel1 = "CH1"
    channel2 = "CH2"
    channel3 = "CH3"
    channel4 = "CH4"
    ext = "EXT"
    ext5 = "EXT5"
    ext10 = "EXT10"

    rising = "RISe"
    falling = "FALL"

    def __init__(self, f):
        self.gpib = f

    def is_channel(self, name):
        return name in [self.channel1, self.channel2, self.channel3, self.channel3, self.ext, self.ext5, self.ext10]

    def trigger_q(self):
        self.gpib.read("TRIGger?")

    def trigger_single(self):
        self.gpib.write(":SINGle")

    def trigger_force(self):
        self.gpib.write("TRIGger FORCe")

    def trigger_edge(self, source, edge_type):
        # This is not working, but I'm not going to try and find out why yet.
        assert(self.is_channel(source))
        self.gpib.write("TRIGger:MAIn:MODe NORMal")
        self.gpib.write("TRIGger:MAIn:EDGE:SOURce %s" % source)
        self.gpib.write("TRIGger:MAIn:EDGE:SLOPe %s" % edge_type)

class rigol_ds1000z_t(oscilloscope_t):
    # It's true; this oscilloscope has some SCPI-like language, but actually is not SCPI.
    # And it also does not accept most IEEE-488.2 commands either
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
    
    def idn(self):
        # This command is specified by IEEE-488.2, but the device doesn't support all of IEEE-488.2
        # so we can't inherit from that class; we just need to reimplement this one command
        return self.gpib.write("*IDN?")

    def is_channel(self, name):
        return name in [self.d0, self.d1, self.d2, self.d3, self.channel1, self.channel2, self.channel3, self.channel3, self.ac]

    def trigger_single(self):
        self.gpib.write(":SINGle")

    def trigger_force(self):
        self.gpib.write(":TFORce")

    def trigger_edge(self, source, edge_type): 
        assert(self.is_channel(source))
        self.gpib.write(":TRIGger:MODe EDGE")
        self.gpib.write(":TRIGger:EDGe:SOURce %s" % source)
        self.gpib.write(":TRIGger:EDGe:SLOPe %s" % edge_type)

    def amplitude(self):
        return self.gpib.read(":MEASure:VAMPlitude?")

class dsox1204a(oscilloscope_t):
    # It's true; this oscilloscope has some SCPI-like language, but actually is not SCPI.
    # And it also does not accept most IEEE-488.2 commands either
    d0 = "D0"
    d1 = "D1"
    d2 = "D2"
    d3 = "D3" # These go all the way up to 15 but I can't be bothered to type.
    channel1 = "CHANnel1"
    channel2 = "CHANnel2"
    channel3 = "CHANnel3"
    channel4 = "CHANnel4"
    ac = "AC"

    rising = "POS"
    falling = "NEG"
    rising_falling = "EITHer"

    def __init__(self, f):
        self.gpib = f
    
    def is_channel(self, name):
        return name in [self.d0, self.d1, self.d2, self.d3, self.channel1, self.channel2, self.channel3, self.channel3, self.ac]

    def trigger_single(self):
        self.gpib.write(":SINGle")

    def trigger_force(self):
        self.gpib.write(":TRIGger:FORCe")

    def trigger_edge(self, source, edge_type): 
        assert(self.is_channel(source))
        self.gpib.write(":TRIGger:MODe EDGE")
        self.gpib.write(":TRIGger:EDGe:SOURce %s" % source)
        self.gpib.write(":TRIGger:EDGe:SLOPe %s" % edge_type)
    
    def measure(self, channel):
        assert(self.is_channel(channel))
        self.gpib.write(":MEASure:SOURce %s" % channel)

    def amplitude(self, channel=None):
        src = ("" if not channel is None else channel)
        self.gpib.write(":MEASure:VAMPlitude %s" % src)
        return self.gpib.read(":MEASure:VAMPlitude? %s" % src)
