import sys
import os
import serial
import time
import socket
from stat import *

class fet_emulator(object):
    # This substrate emulates a field-effect transistor;
    # It measures the gate voltage and always returns the drain current
    def __init__(self, gate, log=None):
        self.log = log
        self.gate = gate
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)

    def readline(self):
        if(self.gate.voltage < -4):
            return "0"
        if(self.gate.voltage < -3.4):
            return "0.1"
        if(self.gate.voltage < -2.9):
            return "0.2"
        if(self.gate.voltage < -2.8):
            return "0.3"
        return "20"

    def read(self, string):
        self.write(string)
        r = self.readline()
        self.log.response(r)
        return r

class fake_customer_dut(object):

    coeff = {
            17000000000: (-0.005580396614879, +0.761813397330639, +24.9853189339396),
            17500000000: (-0.015435139573071, +0.949698960043788, +29.0305993431855),
            18000000000: (-0.016799278084325, +0.958828137075802, +30.1448372240428),
            18500000000: (-0.016442044545493, +0.953755420824387, +30.1478379857690),
            19000000000: (-0.012226853606164, +0.909225716811925, +28.7099684223822),
            19500000000: (-0.008883625952592, +0.898740895120207, +26.8691528777736),
            20000000000: (-0.009382047071702, +0.910235569028672, +26.7498413540483),
            20500000000: (-0.010505494505495, +0.98117264957265,  +24.6195443223443),
            21000000000: (-0.007065911212970, +0.946994720312365, +23.5683588914354)
            }

    def __init__(self, sig_gen, log=None):
        self.log = log
        self.sig_gen = sig_gen
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)
        if "*idn?" in string.lower():
            self.response = "Customer Faker"
        if "ampl" in string.lower():
            c = self.coeff[int(self.sig_gen.frequency.get())]
            pin = self.sig_gen.power_level
            self.response = pow(pin, 2) * c[0] + pin * c[2] + c[2]


    def readline(self):
        return self.response

    def read(self, string):
        self.write(string)
        r = self.readline()
        self.log.response(r)
        return r
