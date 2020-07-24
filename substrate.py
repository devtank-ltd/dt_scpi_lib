import sys
import os
import serial
import time
import socket

def debug_print(msg):
    if "DEBUG" in os.environ:
        print(msg)

def set_debug_print(_func):
    global debug_print
    debug_print = _func

def get_debug_print():
    return debug_print

class fakelog(object):
    def __init__(self):
        pass

    def command(self, string):
        pass

    def response(self, string):
        pass

class log(object):
    def __init__(self, fn):
        self.fn = fn

    def command(self, string):
        with open(self.fn, 'a') as f:
            f.write(">>> " + string + '\n')

    def response(self, string):
        with open(self.fn, 'a') as f:
            f.write("<<< " + string + '\n')

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
        self._dev = open(devpath, "r+")
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

class socket_comm(object):
    def __init__(self, host, port, log=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((host, port))
        self.log = log
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)
        self.sock.sendall(string.encode())

    def readline(self):
        string = self.sock.recv(1024)
        self.log.response(string)
        return string

    def read(self, string):
        self.write(string)
        return self.readline()


