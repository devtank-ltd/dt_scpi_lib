from collections import namedtuple
import sys
import os
import time

class spec_ana_t(object):

    @property
    def centre_freq(self):
        raise NotImplementedError

    @centre_freq.setter
    def centre_freq(self, freq):
        raise NotImplementedError

    @property
    def sweep_time(self):
        raise NotImplementedError

    @sweep_time.setter
    def sweep_time(self, ms):
        raise NotImplementedError

    @property
    def res_band_width(self):
        raise NotImplementedError

    @res_band_width.setter
    def res_band_width(self):
        raise NotImplementedError

    @property
    def freq_span(self):
        raise NotImplementedError

    @freq_span.setter
    def freq_span(self, freq):
        raise NotImplementedError

    @property
    def ref_level(self):
        raise NotImplementedError

    @ref_level.setter
    def ref_level(self, db):
        raise NotImplementedError

    @property
    def divider(self):
        raise NotImplementedError

    @divider.setter
    def divider(self, db):
        raise NotImplementedError

    def do_sweep(self):
        raise NotImplementedError

    def marker_to_peak(self):
        raise NotImplementedError

    def read_marker(self):
        raise NotImplementedError

class agilent_8563(spec_ana_t):
    def __init__(self, serial):
        self.gpib = serial
        self.mcentre_frequency = 0
        self.msweep_time = 0 
        self.mres_band_width = 0
        self.mfreq_span = 0
        self.mref_level = 0
        self.mdivider = 0
        self.reset()

    @property
    def centre_freq(self):
        return self.mcentre_frequency

    @centre_freq.setter
    def centre_freq(self, freq):
        self.gpib.write("cf %.4f;" % (freq/1000000000.0))
        self.mcentre_frequency = freq

    @property
    def sweep_time(self):
        return self.msweep_time

    @sweep_time.setter
    def sweep_time(self, ms):
        self.gpib.write("st %d;\n" % (ms/1000.0))
        self.msweep_time = ms

    @property
    def res_band_width(self):
        return self.mres_band_width

    @res_band_width.setter
    def res_band_width(self, width):
        self.gpib.write("rb %d;" % width)
        self.mres_band_width = width

    @property
    def freq_span(self):
        return self.mfreq_span

    @freq_span.setter
    def freq_span(self, freq):
        self.gpib.write("sp %.4f;" % (freq/1000000000.0))
        self.mfreq_span = freq

    @property
    def ref_level(self):
        return self.mref_level

    @ref_level.setter
    def ref_level(self, db):
        raise NotImplementedError

    @property
    def divider(self):
        raise NotImplementedError

    @divider.setter
    def divider(self, db):
        raise NotImplementedError

    def do_sweep(self):
        self.gpib.write("ts;")
        time.sleep(self.msweep_time)

    def marker_to_peak(self):
        self.gpib.write("mkpk nr;")

    def read_marker(self):
        self.gpib.write("mka?;")
        for i in range(0,10):
            a = self.gpib.readline()
            if a:
                return float(a)

    def reset(self):
        self.gpib.write("ip;")

class e4440(spec_ana_t):
    def __init__(self, serial):
        self.gpib = gpib_device(serial, 18)
        self.mcentre_frequency = 0
        self.msweep_time = 0
        self.mres_band_width = 0
        self.mfreq_span = 0
        self.mref_level = 0
        self.mdivider = 0

    @property
    def centre_freq(self):
        return self.mcentre_frequency

    @centre_freq.setter
    def centre_freq(self, freq):
        self.gpib.write("freq:cent %f GHz\n" % freq)
        self.mcentre_frequency = freq

    @property
    def sweep_time(self):
        return self.msweep_time

    @sweep_time.setter
    def sweep_time(self, ms):
        self.gpib.write("swe:time %d ms\n" % ms)
        self.msweep_time = ms

    @property
    def res_band_width(self):
        return self.mres_band_width

    @res_band_width.setter
    def res_band_width(self, width):
        self.gpib.write("wav:band %dkhz\n" % width)
        self.mres_band_width = width

    @property
    def freq_span(self):
        return self.mfreq_span

    @freq_span.setter
    def freq_span(self, freq):
        self.gpib.write("freq:cent %f GHz\n" % freq)
        self.mfreq_span = freq

    @property
    def ref_level(self):
        return self.mref_level

    @ref_level.setter
    def ref_level(self, db):
        self.gpib.write("disp:wind:trac:y:rlev %d dbm\n" % db)
        self.mref_level = db

    @property
    def divider(self):
        # TODO: What is this?
        # I believe it's for adjusting the graticule divisions on the display.
        return self.mdivider

    @divider.setter
    def divider(self, db):
        # TODO: What is this?
        # I believe it's for adjusting the graticule divisions on the display.
        self.mdivider = db
        self.gpib.write(":disp:wind:trac:y:pdiv %d db" % db)

    def do_sweep(self):
        # TODO: What is this?
        raise NotImplementedError

    def marker_to_peak(self):
        # TODO: What is this?
        raise NotImplementedError

    def read_marker(self):
        # TODO: What is this?
        raise NotImplementedError

