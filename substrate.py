import sys
import os
import serial
import time
import socket
from stat import *
import fcntl
import datetime

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

class prologix_substrate(object):
    def prologix_print(self, string):
        self.file.write(string.encode())

    def gpib_print(self, string):
        self.log.command(string)
        self.file.write(string.encode())

    def __init__(self, f, log=None):
        self.file = f
        self.prologix_print("++mode 1\n++ifc\n++read_tmo_ms 500\n")
        self.addr = None
        self.log = log
        if not self.log:
            self.log = fakelog()

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
        self.serial.address = self.address
        self.log.command(cmd)
        self.serial.write(string)

    def readline(self):
        return self.serial.readline()

    def read(self, string):
        self.serial.address = self.address
        self.serial.write(string)
        return self.serial.readline()

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

    def __init__(self, devpath, log=None):
        # The file needs to be opened as a binary file, and the strings need to be decoded and encoded.
        # Otherwise the slave device will claim that the query has been interrupted, will will cause the _raw_read method to time out.
        # I am not sure why this is.
        self._dev = open(devpath, "r+b", buffering=0)
        fd = self._dev.fileno()
        flag = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFD, flag | os.O_NONBLOCK)
        self._eol = "\n"
        self.log = log
        self.timeout = 5
        if not self.log:
            self.log = fakelog()

    def _raw_write(self, cmd):
        self.log.command(cmd)
        self._dev.write(cmd.encode() + self._eol.encode())
        self._dev.flush()

    def _raw_read(self):
        begin = datetime.datetime.now()
        deadline = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
        r = b""
        try:
            c = self._dev.read(1)
            while c:
                if datetime.datetime.now() > deadline:
                    self.log.remark("Timeout event after %d seconds, having received \"%s\"" % (self.timeout, r))
                    raise TimeoutError("Timeout event after %d seconds, having received \"%s\"" % (self.timeout, r))
                r += c
                c = self._dev.read(1)
                if c == b'\n':
                    break
        except TimeoutError as e:
            self.log.remark("Timeout event after %d seconds, having received \"%s\"" % (self.timeout, r))
            raise e
        r = r.rstrip().decode()

        self.log.response(r)
        return r

    def write(self, cmd):
        self._raw_write(cmd)

    def read(self, cmd):
        print("cmd", cmd)
        self.write(cmd)
        #return self._raw_read()
        try:
            return self._raw_read()
        except TimeoutError as e:
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
