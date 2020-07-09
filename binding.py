from collections import namedtuple
import sys
import os
import serial
from io_stm32_fw import io_board_py_t
import time

def debug_print(msg):
    if "DEBUG" in os.environ:
        print(msg)

def set_debug_print(_func):
    global debug_print
    debug_print = _func

def get_debug_print():
    return debug_print

class prologix_substrate(object):

    def prologix_print(self, string):
        debug_print(string.strip())
        self.file.write(string.encode())

    def gpib_print(self, string):
        debug_print(string.strip())
        self.file.write(string.encode())

    def gpib_response(self, string):
        debug_print("Response from GPIB device: " + string.strip())

    def __init__(self, f):
        self.file = f
        self.prologix_print("++mode 1\n++ifc\n++read_tmo_ms 500\n")
        self.addr = None

    @property
    def address(self):
        return self.addr

    @address.setter
    def address(self, address):
        if self.addr != address:
            self.addr = address
            self.prologix_print('++addr %u\n' % address)

    def write(self, string):
        self.gpib_print(string + "\n")

    def flush(self):
        self.file.flush()

    def readline(self):
        self.prologix_print("++read 10\n")
        a = self.file.readline().rstrip().decode()
        self.gpib_response(a)
        return a

class gpib_device(object):
    def __init__(self, substrate, address):
        self.serial = substrate
        self.address = address

    def write(self, string):
        self.serial.address = self.address
        self.serial.write(string)

    def readline(self):
        return self.serial.readline()

    def read(self, string):
        self.serial.address = self.address
        self.serial.write(string)
        return self.serial.readline()

class dummy_substrate(object):
    def __init__(self):
        pass

    def write(self, string):
        pass

    def readline(self):
        pass

    def read(self, string):
        return ""

class usbtty(object):
    # A class that tries to behave exactly as does gpib_device above
    def __init__(self, f):
        self.serial = serial.Serial(f)

    def write(self, string):
        self.serial.write(string + "\n")

    def readline(self):
        return self.serial.readline()

    def read(self, string):
        self.write(string)
        return self.readline()

class usbtmc(object):
    def __init__(self, devpath):
        self._dev = open(devpath, "r+b")
        self._eol = "\n"

    def _raw_write(self, cmd):
        debug_print("usbtmc << :" + cmd)
        self._dev.write(cmd.encode() + self._eol.encode())

    def _raw_read(self):
        r = self._dev.readline().rstrip().decode()
        debug_print("usbtmc >> :" + r)
        return r

    def write(self, cmd):
        self._raw_write(cmd)

    def read(self, cmd):
        self.write(cmd)
        return self._raw_read()

    def readline(self):
        return self._raw_read()

class rf_dut_binding_info_t:
    def __init__(self, model):
        com_port = "/dev/prologix"
        interface = prologix_substrate(serial.Serial(com_port, baudrate=9600, timeout=1))
        self.interface = interface
        self.loti_tty = serial.Serial("/dev/serial/by-id/usb-Devtank_Ltd_IO_Board_Prototype-if00", baudrate=115200, timeout=1)
        if model == "PA1162":
            self.siggens = [
                    scpi_sig_gen(gpib_device(interface, 6)), # HP8648C
                    scpi_sig_gen(usbtmc("/dev/smbv100a")),   # Rohde & Schwarz SMBV100A
                    hmct2220(usbtty("/dev/hmct2220")),       # Hittite HMC-T2220
                    scpi_sig_gen(usbtmc("/dev/n5183b"))      # Keysight MXG NS5138B
               ]
        else:
            self.siggens = []
        self.model = model

class network_analyser_t(object):

    @property
    def start_freq(self):
        raise NotImplementedError

    @start_freq.setter
    def start_freq(self, freq):
        raise NotImplementedError

    @property
    def stop_freq(self):
        raise NotImplementedError

    @stop_freq.setter
    def stop_freq(self, freq):
        raise NotImplementedError

    @property
    def power_level(self):
        raise NotImplementedError

    @power_level.setter
    def power_level(self, level):
        raise NotImplementedError

    @property
    def sweep_pnt_count(self):
        raise NotImplementedError

    @sweep_pnt_count.setter
    def sweep_pnt_count(self, pnts):
        raise NotImplementedError

    @property
    def rf_power(self):
        raise NotImplementedError

    @rf_power.setter
    def rf_power(self, enable):
        raise NotImplementedError

    def set_marker(self, freq):
        raise NotImplementedError

    def read_marker(self):
        raise NotImplementedError

    def do_sweep(self):
        raise NotImplementedError

class rng_na(network_analyser_t):

    @property
    def start_freq(self):
        return self.mstart_freq

    @start_freq.setter
    def start_freq(self, freq):
        self.mstart_freq = freq

    @property
    def stop_freq(self):
        return self.mstop_freq

    @stop_freq.setter
    def stop_freq(self, freq):
        self.mstop_freq = freq

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level

    @property
    def sweep_pnt_count(self):
        return self.msweep

    @sweep_pnt_count.setter
    def sweep_pnt_count(self, pnts):
        self.msweep = pnts

    @property
    def rf_power(self):
        return self.mrf_power

    @rf_power.setter
    def rf_power(self, enable):
        self.mrf_power = enable

    def set_marker(self, freq):
        pass

    def read_marker(self):
        return random.random() * -60

    def do_sweep(self):
        pass

class hp8720d(network_analyser_t):
    def __init__(self, f):
        self.gpib = f
        self.mstart_freq = 0
        self.mstop_freq = 0
        self.mpower_level = 0
        self.gpib.read("OPC?;PRES;CHAN2;REFP9;")
        self.gpib.read("OPC?;SING;")
        self.gpib.readline()

    def cal(self, slot):
        self.gpib.write("RECA%u;" % slot)

    def frequencyformat(self, freq):
        if freq % (1000 * 1000 * 1000) == 0:
            return "%d ghz" % (freq / (1000 * 1000 * 1000))
        if freq % (1000 * 1000) == 0:
            return "%d mhz" % (freq / (1000 * 1000))
        if freq % (1000) == 0:
            return "%d khz" % (freq / (1000))
        return "%d hz" % freq

    @property
    def start_freq(self):
        return self.mstart_freq

    @start_freq.setter
    def start_freq(self, freq):
        assert freq > 50000000, "The device does not support frequencies below 50MHz."
        assert freq < 20000000000, "The device does not support frequencies above 20GHz"
        self.mstart_freq = freq
        self.gpib.write("STAR%s;" % self.frequencyformat(freq))

    @property
    def stop_freq(self):
        return self.mstop_freq

    @stop_freq.setter
    def stop_freq(self, freq):
        assert freq > 50000000, "The device does not support frequencies below 50MHz."
        assert freq < 20000000000, "The device does not support frequencies above 20GHz"
        self.mstop_freq = freq
        self.gpib.write("STOP%s;" % self.frequencyformat(freq))

    @property
    def power_level(self):
        return self.mpower_level

    @power_level.setter
    def power_level(self, level):
        self.mpower_level = level
        self.gpib.write("POWE %d dB;" % level)

    @property
    def sweep_pnt_count(self):
        return self.msweep_pnt_count

    @sweep_pnt_count.setter
    def sweep_pnt_count(self, pnts):
        # TODO According to datasheet, this ought to be followed by a wait of two sweeps.
        self.msweep_pnt_count = pnts
        self.gpib.write("POIN%d;" % pnts)

    @property
    def rf_power(self):
        raise NotImplementedError

    @rf_power.setter
    def rf_power(self, enable):
        self.gpib.write("POWT " + ("OFF" if enable else "ON") + ";")

    def set_marker(self, point):
        assert point > self.start_freq, "Marker out of range"
        assert point < self.stop_freq, "Marker out of range"
        self.gpib.write("MARKCONT;")
        self.gpib.write("MARK1%d;" % point)
        self.gpib.read("OPC?;WAIT;")
        self.gpib.readline()

    def read_marker(self):
        self.gpib.write("MARK1;")
        # The network analyser will return three values separated by commas,
        # The first value is the gain in dBm
        # The second value is not significant
        # The third value is the marker's frequency (horizontal position on the display)
        return float(self.gpib.read("OUTPMARK;").split(',')[0].strip())

    def idn(self):
        return self.gpib.read("*idn?;")

    def serial_number(self):
        return self.gpib.read("outpsern;")

    def do_sweep(self):
        self.gpib.write("REST;")

    def get_sweep(self):
        debug_print("Raw offsets: %s" % self.gpib.read("rawoffs?;"))

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

class rf_switch_t(object):
    def __init__(self, count, loti):
        self.count = count
        self.loti = loti
        self.mactive_channel = 1

    @property
    def active_channel(self):
        return self.mactive_channel

    @active_channel.setter
    def active_channel(self, index):
        self.loti.loti_gpio(18 + self.mactive_channel, 0)
        self.mactive_channel = index
        self.loti.loti_gpio(18 + self.mactive_channel, 1)
        time.sleep(1)

class input_switch_t(object):
    def __init__(self, count, loti):
        self.loti = loti
        self.mactive_channel = 1

    @property
    def active_channel(self):
        return self.mactive_channel

    @active_channel.setter
    def active_channel(self, index):
        assert index == 1 or index == 2
        self.loti.loti_gpio(0, index != 1)

    

atten_t       = namedtuple("atten_t", "v1 v2 v3")
mux_in_t      = namedtuple("mux_in_t", "v1 v2")
mux_out_t     = namedtuple("mux_out_t", "v1 v2")
saw_channel_t = namedtuple("saw_channel_t", "mux_in mux_out saw_name")

class rf_dut_binding_t(io_board_py_t):
    ATTENUATIONS = { 4 : atten_t(v1=0, v2=1, v3=1),
                     0 : atten_t(v1=1, v2=1, v3=1),
                     7 : atten_t(v1=0, v2=0, v3=0) }

    SAW_CHANNEL_FREQUENCY = {
                               875000 : saw_channel_t(mux_in_t(v2=0, v1=1), mux_out_t(v2=0,v1=0), "SAWChan1"  ), # PA1172
                              1000000 : saw_channel_t(mux_in_t(v2=1, v1=0), mux_out_t(v2=1,v1=1), "SAWChan2"  ),
                              1125000 : saw_channel_t(mux_in_t(v2=1, v1=1), mux_out_t(v2=1,v1=0), "SAWChan3"  ),
                              1250000 : saw_channel_t(mux_in_t(v2=0, v1=0), mux_out_t(v2=0,v1=1), "SAWChan4"  ),
                              1250200 : saw_channel_t(mux_in_t(v2=0, v1=0), mux_out_t(v2=0,v1=1), "SAWChan4"  ),

                              1900000 : saw_channel_t(mux_in_t(v2=0, v1=1), mux_out_t(v2=0,v1=0), "SAWChan1"  ), # PA1167 channels 1, 2, 3, 6, 7, & 8
                              2150000 : saw_channel_t(mux_in_t(v2=1, v1=0), mux_out_t(v2=1,v1=1), "SAWChan2"  ),
                              2400000 : saw_channel_t(mux_in_t(v2=1, v1=1), mux_out_t(v2=1,v1=0), "SAWChan3"  ),
                              2650000 : saw_channel_t(mux_in_t(v2=0, v1=0), mux_out_t(v2=0,v1=1), "SAWChan4"  ),

                              1800000 : saw_channel_t(mux_in_t(v2=0, v1=1), mux_out_t(v2=0,v1=0), "SAWChan1"  ), # PA1167 channels 4 & 5
                              2050000 : saw_channel_t(mux_in_t(v2=1, v1=0), mux_out_t(v2=1,v1=1), "SAWChan2"  ),
                              2300000 : saw_channel_t(mux_in_t(v2=1, v1=1), mux_out_t(v2=1,v1=0), "SAWChan3"  ),
                              2550000 : saw_channel_t(mux_in_t(v2=0, v1=0), mux_out_t(v2=0,v1=1), "SAWChan4"  ),
                            }

    def __init__(self, rf_dut_binding_info, uuid):
        self.network_analyser = hp8720d(gpib_device(rf_dut_binding_info.interface, 16))
        #self.network_analyser = rng_na()

        self.sig_gens = rf_dut_binding_info.siggens
        self.spec_ana = agilent_8563(gpib_device(rf_dut_binding_info.interface, 2)) # Apparently 2 is the gpib address. I don't know where that number came from
#        self.spec_ana = spec_ana_t(rf_dut_binding_info.spec_an_tty)
        self.input_switch = input_switch_t(2, self)
        self.output_switch = rf_switch_t(8, self)
        self.loti_tty = rf_dut_binding_info.loti_tty

        if rf_dut_binding_info.model == "PA1167":
            self.network_analyser.cal(2)
            self.chlatchmap = [-1, 10, 11, 12, 13, 14, 15, 16, 17]
            self.enable_power_5v(1)

        if rf_dut_binding_info.model == "PA1172":
            self.network_analyser.cal(1)
            self.chlatchmap = [-1, 10, 11, 12, 13, 14, 15, 16, 17]

        self.select_channel = 1
        self.attenuation = self.ATTENUATIONS[0]
        self.mamp_power_enable = False
        self.amp_enable = False
        for i in range(1, 9):
            self.select_channel = i
        self.enable_power_3v3(0)
        self.uuid = uuid
        for i in range(0, 27):
            self.loti_gpio(i, i == 1)

    def cal_setup(self):
        self.select_channel = 1
        self.output_switch.active_channel = 1
        self.enable_power_5v(1)

    def vna_ok(self):
        if self.network_analyser.idn() != "HEWLETT PACKARD,8720D,0,7.48":
            debug_print("Network analyser returned incorrect identification string " + self.network_analyser.idn)
            return False
        if self.network_analyser.serial_number() != "US38431279":
            debug_print("Network analyser has wrong serial number " + self.network_analyser.serial_number)
            return False
        return True

    def loti_command(self, string):
        debug_print(string)
        self.loti_tty.write(("%s\n" % string).encode())
        time.sleep(0.001)

    def loti_qry(self, string):
        self.loti_tty.flushInput()
        self.loti_command(string)
        time.sleep(.5)
        a = self.loti_tty.readline().decode("utf-8")
        while a != '':
            debug_print("Response from LoTI: " + a.strip())
            yield a
            a = self.loti_tty.readline().decode("utf-8").strip()

    def loti_gpio(self, gpio_num, lvl):
        self.loti_command("output %d %d" % (gpio_num, 1 if lvl else 0))

    def enable_power_3v3(self, ma):
        self.m3v3 = ma
        self.loti_gpio(18, ma)
        time.sleep(1)
        return True

    def enable_power_5v(self, ma):
        self.m5v = ma
        self.loti_gpio(27, ma)
        self.loti_gpio(28, ma)
        return True

    def depower(self):
        # this is called when the test ends, and ensures that the board is powered down.
        self.enable_power_3v3(0)
        self.enable_power_5v(0)

    @property
    def amp_power_enable(self):
        return self.mamp_power_enable

    @amp_power_enable.setter
    def amp_power_enable(self, enable):
        self.mamp_power_enable = enable
        self.loti_gpio(1, enable)
        time.sleep(3)

    def read_current_3v3(self):
        for a in self.loti_qry("adc 5"): 
            if a.startswith('Avg : '):
                s = a.split(':')[1]
                assert min([c in "0123456789()/+-*. " for c in s])
                return (((eval(s) / 4096.0) * 3.3) * .5) * 1000

    def read_current_5v(self):
        raise NotImplementedError

    def set_rtn_oe_1_n(self, is_low):
        #self.loti_gpio(0, not is_low)
        pass

    @property
    def saw_channel(self):
        return self.msawchan

    @saw_channel.setter
    def saw_channel(self, saw_channel):
        debug_print("setting saw channel")
        self.msawchan = saw_channel
        self.loti_gpio(6, self.saw_channel.mux_out.v2)
        self.loti_gpio(5, self.saw_channel.mux_out.v1)
        self.loti_gpio(3, self.saw_channel.mux_in.v2)
        self.loti_gpio(2, self.saw_channel.mux_in.v1)
        self.strobe_ch_latch()

    @property
    def attenuation(self):
        return self.mattenuation

    def all_off(self):
        self.amp_power_enable(0)
        self.loti_tty.close()

    @attenuation.setter
    def attenuation(self, atten):
        self.mattenuation = atten
        self.loti_gpio(9, atten.v1)
        self.loti_gpio(8, atten.v2)
        self.loti_gpio(7, atten.v3)
        self.strobe_ch_latch()

    def strobe_ch_latch(self):
        self.loti_gpio(self.chlatchmap[self.mselect_channel], 1)
        time.sleep(.2)
        self.loti_gpio(self.chlatchmap[self.mselect_channel], 0)

    @property
    def select_channel(self):
        return self.mselect_channel

    @select_channel.setter
    def select_channel(self, channel):
        debug_print("selecting channel %d")
        self.mselect_channel = channel
        self.strobe_ch_latch()



boards = {
        "PA1172" : lambda uuid: rf_dut_binding_t(rf_dut_binding_info_t("PA1172"), uuid),
        "PA1167" : lambda uuid: rf_dut_binding_t(rf_dut_binding_info_t("PA1167"), uuid),
        "PA1162" : lambda uuid: rf_dut_binding_t(rf_dut_binding_info_t("PA1162"), uuid)
        }

