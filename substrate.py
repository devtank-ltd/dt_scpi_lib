from __future__ import print_function
import sys
import os
import serial
import time
import socket
import select
from stat import *
import fcntl
import datetime

class stdout_log(object):
    def __init__(self, tag):
        self.tag = ((16 - len(tag[:16])) * " ") + tag

    def emit(self, string):
        print(string)

    def revelations(self, string):
        return string.replace("\n", "\\n").replace("\r", "\\r")

    def command(self, string):
        self.emit(self.tag + " >>> \"" + self.revelations(string) + "\"")

    def remark(self, string):
        self.emit(self.tag + " ... \"" + self.revelations(string) + "\"")

    def response(self, string):
        self.emit(self.tag + " <<< \"" + self.revelations(string) + "\"")

class fakelog(object):
    def __init__(self):
        pass

    def emit(self, string):
        pass

class stderr_log(stdout_log):
    def __init__(self, tag):
        stdout_log.__init__(self, tag)

    def emit(self, string):
        print(string, file=sys.stderr)
        sys.stderr.flush()

class log(stdout_log):
    def __init__(self, tag, fn):
        stdout_log.__init__(self, tag)
        self.fn = fn
        open(fn, 'a').close() # Create the file if it doesn't exist
        if S_ISSOCK(os.stat(fn).st_mode):
            self.mode = 'a'
        else:
            self.mode = 'a'

    def emit(self, string):
        with open(self.fn, self.mode) as f:
            f.write(string + '\n')


class teelog(stdout_log):
    def __init__(self, loglist):
        self.loglist = loglist

    def emit(selF, string):
        for l in self.loglist:
            l.emit(string)

class prologix_tty():
    def __init__(self, f, log=None):
        self.file = serial.Serial(f)
        self.addr = None
        self.log = log
        if not self.log:
            self.log = fakelog()
        for s in ["++mode 1", "++ifc", "++read_tmo_ms 500", "++eoi 1", "++eos 2"]:
            self.dwrite(s)

    def dwrite(self, string):
        self.log.command("\n" + string + "\n")
        self.file.write(("\n" + string + "\n").encode())

    def write(self, addr, string):
        if self.addr != addr:
            self.dwrite("++addr %u" % addr)
            self.addr = addr
        self.file.write(string.encode())
        self.log.command(string)

    def read_eoi(self):
        self.dwrite("++read eoi")
        a = self.file.readline().rstrip().decode()
        self.log.response(a)
        return a

    def read_lf(self):
        self.dwrite("++read 10")
        a = self.file.readline().rstrip().decode()
        self.log.response(a)
        return a

class gpib_device(object):
    def __init__(self, substrate, address, eol="", log=None):
        self.serial = substrate
        self.address = address
        self.log = log
        self.eol = eol
        if not self.log:
            self.log = fakelog()

    def write(self, string):
        self.log.command(string)
        self.serial.write(self.address, string + self.eol)

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

    def __init__(self, devpath, log=None, eol="\n", timeout=0):
        # The file needs to be opened as a binary file, and the strings need to be decoded and encoded.
        # Otherwise the slave device will claim that the query has been interrupted, will will cause the _raw_read method to time out.
        # I am not sure why this is.
        self._dev = open(devpath, "r+b")
        self._eol = eol
        self.log = log
        self.timeout = timeout
        if not self.log:
            self.log = fakelog()

    def _raw_write(self, cmd):
        self.log.command(cmd)
        self._dev.write(cmd.encode() + self._eol.encode())
        self._dev.flush()

    def _raw_read(self):
        if self.timeout == 0:
            r = self._dev.readline().rstrip().decode()
            self.log.response(r)
            return r

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
        print("cmd", cmd)
        self.write(cmd)
        #return self._raw_read()
        try:
            return self._raw_read()
        except IOError as e:
            time.sleep(1)
            print("retry")
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
