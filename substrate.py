import sys
import os
import serial
import time
import socket
import select
from stat import *

class fakelog(object):
    def __init__(self):
        pass

    def command(self, string):
        pass

    def response(self, string):
        pass

class stderr_log(object):
    def __init__(self, name):
        self.name = name

    def command(self, string):
        print("sent to       %s: \"%s\"" % (self.name, string), file=sys.stderr, flush=True)

    def response(self, string):
        print("received from %s: \"%s\"" % (self.name, string), file=sys.stderr, flush=True)

    def remark(self, string):
        print("remark about  %s: \"%s\"" % (self.name, string), file=sys.stderr, flush=True)

class log(object):
    def __init__(self, fn):
        self.fn = fn
        open(fn, 'a').close() # Create the file if it doesn't exist
        if S_ISSOCK(os.stat(fn).st_mode):
            self.mode = 'a'
        else:
            self.mode = 'a'

    def command(self, string):
        with open(self.fn, self.mode) as f:
            f.write(">>> " + string + '\n')

    def response(self, string):
        with open(self.fn, self.mode) as f:
            f.write("<<< " + string + '\n')

    def remark(self, string):
        with open(self.fn, self.mode) as f:
            f.write("... " + string + '\n')

class prologix_tty():
    def __init__(self, f, log=None):
        self.file = serial.Serial(f)
        self.addr = None
        self.log = log
        if not self.log:
            self.log = fakelog()
        self.file.write("++mode 1".encode())
        self.file.write("++ifc".encode())
        self.file.write("++read_tmo_ms 500".encode())
        self.file.write("++eoi 1".encode())

    def write(self, addr, string):
        if self.addr != addr:
            self.log.command(("++addr %u" % addr))
            self.file.write(("++addr %u" % addr).encode())
            self.addr = addr
        self.file.write(string.encode())
        self.log.command(string)

    def read_eoi(self):
        self.write("++read eoi".encode())
        a = self.file.readline().rstrip().decode()
        self.log.response(a)
        return a

    def read_lf(self):
        self.write("++read 10".encode())
        a = self.file.readline().rstrip().decode()
        self.log.response(a)
        return a

class gpib_device(object):
    def __init__(self, substrate, address, log=None):
        self.serial = substrate
        self.address = address
        self.log = log
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)
        self.serial.write(self.address, string)

    def readline(self):
        return self.serial.read_eoi()

    def read(self, string):
        self.write(string)
        return self.readline()

class dummy_substrate(object):
    def __init__(self, log=None):
        self.log = log
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)

    def readline(self):
        self.log.response("dummy substrate")
        return "dummy substrate"

    def read(self, string):
        self.write(string)
        return self.readline()

class excruciating_debug_substrate(object):
    # "Kinda" Implements the USBTMC protocol
    # (trying to debug that keysight power meter we have)

    def __init__(self, devpath, log=None):
        # The file needs to be opened as a binary file, and the strings need to be decoded and encoded.
        # Otherwise the slave device will claim that the query has been interrupted, will will cause the _raw_read method to time out.
        # I am not sure why this is.
        self._dev = open(devpath, "r+b")
        self._eol = "\n"
        self.log = log
        if not self.log:
            self.log = fakelog()

    def _raw_write(self, cmd):
        self.log.command(cmd)
        self._dev.write(cmd.encode() + self._eol.encode())

    def _raw_read(self):
        r = ""
        c = ""
        while c != "\n":
            c = self._dev.readline(1).decode()
            self.log.response(r)
            r += c
            self.log.response(r)
        return r

    def write(self, cmd):
        self._raw_write(cmd)

    def read(self, cmd):
        self.write(cmd)
        return self._raw_read()

    def readline(self):
        return self._raw_read()

    def readblock(self):
        # Apparently, some RIGOL devices lie about the size of the block length.
        # Here, an IEEE block starts with a '#' character,
        # Then a single ASCII digit saying how long the length is,
        # then the length.
        # For example, if the block proper is 100 bytes long, then because 100 is a three digit number,
        # the header will be the five bytes; '#3100'
        c = self._dev.read(1)
        if c != b'#':
            raise RuntimeError("The device did not respond with a valid IEEE block")
        c = int(self._dev.read(1))
        length = 0
        for i in range(0, c):
            length = length * 10 + int(self._dev.read(1))

        self.log.remark("Fetching a block of length %u" % length)

        data = b''
        for i in range(0, length):
            data += self._dev.read(1)
        return data


class usbtty(object):
    # A class that tries to behave exactly as does gpib_device above
    def __init__(self, f, log=None):
        self.serial = serial.Serial(f)
        self.log = log
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(cmd)
        self.serial.write(string + "\n")

    def readline(self):
        return self.serial.readline()

    def read(self, string):
        self.write(string)
        return self.readline()

class usbtmc(object):
    # Implements the USBTMC protocol
    # (Does not try to do anything to work around any quirks that various instruments might have)

    def __init__(self, devpath, log=None, eol="\n"):
        # The file needs to be opened as a binary file, and the strings need to be decoded and encoded.
        # Otherwise the slave device will claim that the query has been interrupted, will will cause the _raw_read method to time out.
        # I am not sure why this is.
        self._dev = open(devpath, "r+b")
        self._eol = eol
        self.log = log
        self.timeout = 5
        if not self.log:
            self.log = fakelog()

    def _raw_write(self, cmd):
        self.log.command(cmd)
        self._dev.write(cmd.encode() + self._eol.encode())

    def _raw_read(self):
        for i in range(self.timeout):
            r, w, e = select.select([ self._dev ], [], [], 0)
            if self._dev in r:
                r = self._dev.readline().rstrip().decode()
                self.log.response(r)
                return r
            self.log.remark("time passes...")
            time.sleep(1)


    def write(self, cmd):
        self._raw_write(cmd)

    def read(self, cmd):
        self.write(cmd)
        return self._raw_read()

    def readline(self):
        return self._raw_read()

    def readblock(self):
        # Apparently, some RIGOL devices lie about the size of the block length.
        # Here, an IEEE block starts with a '#' character,
        # Then a single ASCII digit saying how long the length is,
        # then the length.
        # For example, if the block proper is 100 bytes long, then because 100 is a three digit number,
        # the header will be the five bytes; '#3100'
        c = self._dev.read(1)
        if c != b'#':
            raise RuntimeError("The device did not respond with a valid IEEE block")
        c = int(self._dev.read(1))
        length = 0
        for i in range(0, c):
            length = length * 10 + int(self._dev.read(1))

        self.log.remark("Fetching a block of length %u" % length)

        data = b''
        for i in range(0, length):
            data += self._dev.read(1)
        return data


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
        self.log.response(string.decode())
        return string

    def read(self, string):
        self.write(string)
        return self.readline()

    def readblock(self):
        # Gon read 1 kilobyte at a time
        dat = self.sock.recv(1024)
        i = int(dat[0].encode())
        length = int(dat[1, 1+i])
        self.log.remark("Fetching a %u byte block" % length)

        dat = dat[1+i:]
        while len(dat) < length:
            dat += self.sock.recv(1024)

        return dat
