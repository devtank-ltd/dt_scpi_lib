from collections import namedtuple
import sys
import os
import time
from dt_scpi_lib.ieee488 import ieee488_t, scpi_t
from dt_scpi_lib.parameter import *


class oscilloscope_t(object):

    def run():
        self.gpib.write(":run")

    def stop():
        self.gpib.write(":stop")

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

    def __init__(self, substrate):
        self.substrate = substrate
        self.idn = constant_t(self, "*IDN?")

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

    def __init__(self, substrate):
        self.substrate = substrate
        self.idn = constant_t(self, "*IDN?")

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

class dsox1204a(oscilloscope_t, ieee488_t):
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

    def __init__(self, substrate):
        self.substrate = substrate
        self.idn = constant_t(self, "*IDN?")
    
    def is_channel(self, name):
        return name in [self.d0, self.d1, self.d2, self.d3, self.channel1, self.channel2, self.channel3, self.channel3, self.ac]

    def measurement_parse(self, string):
        # Quote from the datasheet, page 350:
        # "If a measurement cannot be made (typically because the proper portion of the waveform is not displayed), the value 
        # +9.9E+37 is returned for that measurement." So far as I've seen, the scope will return the string "+99E+36" in this case.
        if string == "+99E+36":
            raise RuntimeError("The RIGOL DSOX1204 oscilloscope did not return a meaningful value")
        else:
            return float(string)

    def ieee_block_bytes(self):
        # TODO: The programming examples in the datasheet (written in some flavor of VBA) call this function "DoQueryIEEEBlock_Bytes"
        # which hints at the possibility that this format belongs in some IEEE standard. If that's the case, then this method ought to be moved to a superclass

        # The first byte is an ASCII character '1' thru '9', which is the length of the length, and the next 1 to 9 bytes are the
        # length. So if the block is 100 bytes long, then because 100 is a three-digit number the first four bytes in the block are
        # "3100". This scheme effectively limits the block length to just shy of 10 kilobytes; have I misunderstood something?
        i = int(self.gpib.get_byte())
        length = 0
        for i in range(0, i):
            length = length * 10 + int(self.gpib.get_byte())
        self.gpib.remark("Fetching a %u byte block" % length)

        for l in range(0, l):
            yield self.gpib(get_byte())

    def screenshot(self, filename):
        self.gpib.write(":HARDcopy:INKSaver OFF")
        self.gpib.write(":DISPlay:DATA? PNG, COLor")
        data = self.gpib.readblock()
        with open(filename, "w+b") as scrshot:
            scrshot.write(data)

    def channel_autoscale(self, channel):
        assert(self.is_channel(channel))
        self.gpib.write(":AUToscale %s" % channel)

    def channel_scale(self, channel, scale):
        assert(self.is_channel(channel))
        self.gpib.write(":%s:SCALe %fV" % (channel, scale))

    def channel_offset(self, channel, offset):
        assert(self.is_channel(channel))
        self.gpib.write(":%s:OFFSet %fV" % (channel, offset))

    def trigger_single(self):
        self.gpib.write(":SINGle")

    def trigger_force(self):
        self.gpib.write(":TRIGger:FORCe")

    def trigger_auto(self):
        self.gpib.write(":TRIGger:SWEep AUTO")

    def trigger_normal(self):
        self.gpib.write(":TRIGger:SWEep NORMal")

    def trigger_edge(self, source, edge_type): 
        assert(self.is_channel(source))
        self.gpib.write(":TRIGger:MODe EDGE")
        self.gpib.write(":TRIGger:EDGe:SOURce %s" % source)
        self.gpib.write(":TRIGger:EDGe:SLOPe %s" % edge_type)
    
    def measure(self, channel):
        assert(self.is_channel(channel))
        self.gpib.write(":MEASure:SOURce %s" % channel)

    def amplitude(self, channel=None):
        src = ("" if channel is None else channel)
        self.gpib.write(":MEASure:SOURce %s" % src)
        self.gpib.write(":MEASure:VAMPlitude %s" % src)
        return self.measurement_parse(self.gpib.read(":MEASure:VAMPlitude? %s" % src))

    def system_error(self):
        return self.gpib.read("SYSTem:ERRor?")
