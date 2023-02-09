"""CLI serial booter."""
# The MIT License (MIT)
# Copyright (c) 2019 ezflash
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import logging
import sys

import serial

from ezFlashCLI.cli import __version__

BAUDRATE = 115200
TIMEOUT = 5


class da1469xSerialLoader(object):
    """Load an application binary in RAM through the serial UART booter in the Smartbond device."""

    def __init__(self):
        """Initialize and parse the input parameters."""
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.argument_parser()

        if self.args.version:
            self.logger.info("{}".format(__version__))
            sys.exit(0)

        if not self.args.port:
            self.logger.error("Port not specified")
            self.parser.print_help()
            sys.exit(1)

        if not self.args.application:
            self.logger.error("Application not specified")
            self.parser.print_help()
            sys.exit(1)

        self.sp = serial.Serial(self.args.port, BAUDRATE, timeout=TIMEOUT)

        self.load()

    def load(self):
        """Load application in the Smartbond device."""
        try:
            with open(self.args.application, "rb") as fp:

                data = fp.read()
                size = len(data)
        except Exception as ex:
            self.logger.error("Failed to read application. Err: {}".format(ex))
            return 1

        self.logger.debug("Loading App size {}".format(size))

        crc = 0
        for d in data:
            crc ^= d

        if not self.get_stx():
            self.logger.debug("Press Reset")
            if not self.get_stx():
                self.logger.info("Failed to detect Smartbond device")
                return
        self.logger.info("Reset detected")
        # self.sp.write(b'\x01') # send SOH
        if size < 2**16:
            self.sp.write(b"\x01" + size.to_bytes(2, byteorder="little"))
        else:
            self.sp.write(b"\x01\x00\x00" + size.to_bytes(3, byteorder="little"))

        if self.args.one:
            self.sp.read(3)

        if self.sp.read(1) != b"\x06":
            self.logger.error("Failed to get length ACK")
            return

        chunkSize = 1024
        if self.args.one:
            while len(data):
                if len(data) >= chunkSize:
                    self.sp.write(data[:chunkSize])
                    self.sp.read(chunkSize)
                    data = data[chunkSize:]
                else:
                    self.sp.write(data)
                    self.sp.read(len(data))
                    data = []
        else:
            self.sp.write(data)

        read_crc = int.from_bytes(self.sp.read(1), byteorder="little")
        if read_crc != crc:
            self.logger.debug("Failed to get data ACK {} {}".format(read_crc, crc))
            return

        self.sp.write(b"\x06")
        self.logger.info("Loading success")

    def get_stx(self):
        """Capture the STX character from the smarbond."""
        if self.sp.read(1) == b"\x02":
            return True

        return False

    def argument_parser(self):
        """Initialize the arguments passed from the command line."""
        self.parser = argparse.ArgumentParser(
            description="Smartbond Serial loader v%s" % __version__, prog="ezSerialCLI"
        )

        self.parser.add_argument(
            "port", nargs="?", help="Serial port name", default=None
        )
        self.parser.add_argument(
            "application", nargs="?", help="Application to load", default=None
        )

        self.parser.add_argument(
            "-v", "--verbose", help="increase verbosity", action="store_true"
        )

        self.parser.add_argument(
            "--version", help="return version number", action="store_true"
        )

        self.parser.add_argument(
            "-o", "--one", help="setup 1-wire mode", action="store_true"
        )

        self.args = self.parser.parse_args()


def main():
    """Create da1469xSerialLoader instance."""
    da1469xSerialLoader()


if __name__ == "__main__":

    main()
