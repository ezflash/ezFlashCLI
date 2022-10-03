#!/usr/bin/env python3
"""CLI interface for ezFlash."""
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
import json
import logging
import os
import sys

import ezFlashCLI.ezFlash.smartbond.smartbondDevices as sbdev
from ezFlashCLI import __version__
from ezFlashCLI.ezFlash.pyjlink import pyjlink


class ezFlashCLI:
    """Command line interpreter class."""

    flashid = None

    def __init__(self):
        """Initialize the class and parse command line arguments."""
        # parse the command line arguments
        self.argument_parser()

        # load the flash database
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "flash_database.json"
            )
        ) as json_file:
            self.flash_db = json.load(json_file)

            json_file.close()

        # set the verbosity
        if self.args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        logging.info("{} v{}".format(self.__class__.__name__, __version__))
        logging.info("By using the program you accept the SEGGER J-link™ license")

        # list the jlink interfaces
        if self.args.version:
            logging.info("{}".format(__version__))
            sys.exit(0)

        # using JLINK for operations
        if not self.args.port:
            self.link = pyjlink()
            self.link.init()
            self.rawdevicelist = self.link.browse()

            if self.rawdevicelist is None:
                logging.error("No JLink device found")
                sys.exit(1)

            self.devicelist = []
            for device in self.rawdevicelist:
                if device.SerialNumber != 0:
                    self.devicelist.append(device)

            self.devicelist.sort()
            if (
                len(self.devicelist) > 1
                and not self.args.jlink
                and self.args.operation != "list"
            ):
                logging.warning("JLink interface must be selected using -j option")
                logging.warning(
                    "Multiple interfaces detected, the lowest serial number is selected"
                )
                self.display_jlink_devices()

                logging.warning(
                    "Selecting interfface {}".format(self.devicelist[0].SerialNumber)
                )
                self.args.jlink = self.devicelist[0].SerialNumber

        # list the jlink interfaces
        if self.args.operation == "list":
            self.display_jlink_devices()

        elif self.args.operation == "probe":
            self.probeDevice()

            logging.info(
                "Smartbond chip: {}".format(
                    sbdev.SMARTBOND_PRETTY_IDENTIFIER[self.deviceType]
                )
            )

            self.probeFlash()
            logging.info("Flash information:")
            if self.flashid is not None:
                logging.info("  - Device Id: {}".format(self.flashid["name"]))
            else:
                logging.info("  - Device Id: {}".format("Not Found"))

            # # check the flash header
            # if self.flashid:
            #     print("  - Product header programmed: {}".format(self.flashProductHeaderIsCorrect()))

        elif self.args.operation == "go":
            self.probeDevice()
            logging.info(
                "Smartbond chip: {}".format(
                    sbdev.SMARTBOND_PRETTY_IDENTIFIER[self.deviceType]
                )
            )
            self.go()

        elif self.args.operation == "erase_flash":
            self.probeDevice()
            self.probeFlash()

            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)

            if self.da.flash_erase():
                logging.info("Flash erase success")
            else:
                logging.error("Flash erase failed")
                sys.exit(1)

        elif self.args.operation == "read_flash":

            self.probeDevice()
            self.probeFlash()
            self.da.flash_configure_controller(self.flashid)
            data = self.da.read_flash(self.args.addr, self.args.length)
            current_address = self.args.addr
            line_width = 16
            while len(data):
                dataByes = " ".join("{:02x}".format(x) for x in data[:line_width])
                logging.info("{:08X}: {}".format(current_address, dataByes))
                data = data[line_width:]
                current_address += line_width
        elif self.args.operation == "read_flash_bin":

            with open(self.args.file, "wb") as fp:
                self.probeDevice()
                self.probeFlash()
                self.da.flash_configure_controller(self.flashid)
                data = self.da.read_flash(self.args.addr, self.args.length)
                for datum in data:
                    fp.write(datum.to_bytes(1, "little"))
                fp.close()

        elif self.args.operation == "write_flash_bytes":
            # decode the command
            logging.info(
                "Writing at 0x{:08x}. Data: {}".format(self.args.addr, self.args.data)
            )
            # decode the data
            data = b""

            for d in self.args.data:
                if "0x" in d:
                    try:
                        data += bytes().fromhex(d[2:])
                    except Exception as ex:
                        logging.error("Failed to decode byte: {}: {}".format(d, ex))
                        sys.exit(0)
                else:
                    data += int(d).to_bytes(1, "little")

            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)

            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            if self.da.flash_program_data(data, self.args.addr):
                logging.info("Flash write success")
            else:
                logging.error("Flash write failed")

            sys.exit(1)

        elif self.args.operation == "write_flash":

            try:
                fp = open(self.args.filename, "rb")
            except Exception as ex:
                logging.error(
                    "Failed to open {}. Err: {}".format(self.args.filename, ex)
                )
                sys.exit(1)

            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)

            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            fileData = fp.read()
            logging.info("Program file size {}".format(len(fileData)))
            fp.close()

            if self.da.flash_program_data(fileData, self.args.addr):
                logging.info("Flash write success")
            else:
                logging.error("Flash write failed")
                sys.exit(1)

        elif self.args.operation == "image_flash":

            try:
                fp = open(self.args.filename, "rb")
            except Exception as ex:
                logging.error(
                    "Failed to open {}. Err:{}".format(self.args.filename, ex)
                )
                sys.exit(1)

            parameters = {}
            parameters["active_fw_image_address"] = self.args.active_image_address
            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)
            parameters["flashid"] = self.flashid

            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            fileData = fp.read()
            fp.close()
            if self.da.flash_program_image(fileData, parameters):
                logging.info("Flash image success")
            else:
                logging.error("Flash image failed")
                sys.exit(1)

        elif self.args.operation == "image_bootloader_flash":

            try:
                fp = open(self.args.filename, "rb")
            except Exception as ex:
                logging.error(
                    "Failed to open {}. Err:{}".format(self.args.filename, ex)
                )
                sys.exit(1)

            parameters = {}
            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)
            parameters["flashid"] = self.flashid

            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            parameters["fileData"] = fp.read()
            fp.close()
            if self.da.flash_program_image_with_bootloader(parameters):
                logging.info("Flash image success")
            else:
                logging.error("Flash image failed")
                sys.exit(1)

        elif self.args.operation == "linker_header":
            """Generate the product header based on the probed flash

            This can be pasted in your linker script to adapt custom flash

            """
            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)

            logging.info(
                self.da.scatterfile_product_header(
                    self.flashid["flash_burstcmda_reg_value"],
                    self.flashid["flash_burstcmdb_reg_value"],
                    self.flashid["flash_write_config_command"],
                )
            )

        elif self.args.operation == "product_header_check":
            """Performs sanity check on the product header
            it will verify the content is consistent with the probed flash

            Args:
                None

            Returns:
                True if the Header is consistent with the attached flash

            """

            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)

            productHeaderCalculated = self.calculateProductHeader()

            self.da.connect(self.args.jlink)
            self.da.flash_configure_controller(self.flashid)
            productHeader = self.da.read_product_header()

            if productHeaderCalculated == productHeader:
                logging.info("Product header OK")
            else:
                logging.error("Product header mismatch")

        elif self.args.operation == "read_otp":

            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            count, offset = self.da.otp_read(self.args.key)
            if offset < 0:
                sys.exit(1)

        elif self.args.operation == "write_otp":

            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            result = self.da.otp_write(self.args.key, self.args.values, self.args.force)
            if result < 0:
                sys.exit(1)

        elif self.args.operation == "otp_blank_check":

            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            if self.da.otp_blank_check() is True:
                logging.info("OTP is blank")
                sys.exit(0)
            else:
                logging.info("OTP is NOT blank")
                sys.exit(1)

        elif self.args.operation == "read_otp_hex":

            self.probeDevice()
            self.probeFlash()
            self.importAndAssignDevice(self.deviceType)
            self.da.connect(self.args.jlink)
            data = self.da.otp_read_raw(self.args.addr, self.args.length)
            current_address = self.args.addr
            line_width = 16
            while len(data):
                dataByes = " ".join("{:02x}".format(x) for x in data[:line_width])
                logging.info("{:08X}: {}".format(current_address, dataByes))
                data = data[line_width:]
                current_address += line_width

        elif self.args.operation == "read_otp_bin":

            with open(self.args.file, "wb") as fp:
                self.probeDevice()
                self.probeFlash()
                self.importAndAssignDevice(self.deviceType)
                self.da.connect(self.args.jlink)
                data = self.da.otp_read_raw(self.args.addr, self.args.length)
                for datum in data:
                    fp.write(datum.to_bytes(1, "little"))
                fp.close()

        else:
            self.parser.print_help(sys.stderr)
        sys.exit(0)

    def importAndAssignDevice(self, device):
        """Import the device from the database.

        Assign the device to the self.da variable

        Args:
            device: device name (string)
        """
        self.da = eval("sbdev.{}".format(device))()

    def go(self):
        """Reset the device and run."""
        self.link.connect(self.args.jlink)
        self.link.reset()
        self.link.go()

    def probeDevice(self):
        """Look for attached smarbond device."""
        try:
            self.deviceType = sbdev.SMARTBOND_IDENTIFIER[
                self.link.connect(self.args.jlink)
            ]
            self.link.close()

        except Exception as inst:
            logging.error("Device not responding: {}".format(inst))
            sys.exit(1)

    def probeFlash(self):
        """Look for attached flash."""
        # try:
        self.importAndAssignDevice(self.deviceType)
        self.da.connect(self.args.jlink)
        dev = self.da.flash_probe()
        self.flashid = self.da.get_flash(dev, self.flash_db)
        return self.flashid
        # except Exception as inst:
        #     logging.error("No Flash detected {}".format(inst))

        return None

    def calculateProductHeader(self):
        """Calculate the product header."""
        return self.da.make_product_header(
            self.flashid["flash_burstcmda_reg_value"],
            self.flashid["flash_burstcmdb_reg_value"],
            self.flashid["flash_write_config_command"],
        )

    def display_jlink_devices(self):
        """List the JLink devices."""
        logging.info("JLink devices:")
        for device in self.devicelist:
            if device.SerialNumber != 0:
                logging.info("  - {}".format(device.SerialNumber))

    def argument_parser(self):
        """Initialize the arguments passed from the command line."""
        self.parser = argparse.ArgumentParser(
            description="Smartbond tool v%s - Dialog Smartbond devices flash management tool"
            % __version__,
            prog="ezFlashCLI",
        )

        self.parser.add_argument(
            "-c",
            "--chip",
            help="Smartbond chip version",
            choices=[
                "auto",
                "DA14531",
                "DA14580",
                "DA14585",
                "DA14681",
                "DA14683",
                "DA1469x",
            ],
            default=os.environ.get("SMARTBOND_CHIP", "auto"),
        )

        self.parser.add_argument(
            "-p",
            "--port",
            help="Serial port device",
            default=os.environ.get("SMARTBOND_PORT", None),
        )

        self.parser.add_argument(
            "-j",
            "--jlink",
            help="JLink device identifier",
            default=os.environ.get("SMARTBOND_JLINK_ID", None),
        )

        self.parser.add_argument(
            "-v", "--verbose", help="increase verbosity", action="store_true"
        )
        self.parser.add_argument(
            "--version", help="return version number", action="store_true"
        )

        self.subparsers = self.parser.add_subparsers(
            dest="operation", help="Run  {command} -h for additional help"
        )

        self.subparsers.add_parser("list", help="list JLink interfaces")
        self.subparsers.add_parser(
            "probe", help="Perform Chip detection and its associated flash"
        )

        self.subparsers.add_parser("go", help="Reset and start the CPU")
        self.subparsers.add_parser(
            "erase_flash", help="Perform Chip Erase on SPI/QSPI flash"
        )

        otp_read_parser = self.subparsers.add_parser(
            "read_otp", help="Read specified OTP config script value"
        )
        otp_read_parser.add_argument(
            "key",
            nargs="?",
            type=lambda x: int(x, 0),
            default=0xFFFFFFFF,
            help="Key to read (example: 0x100c0040)",
        )

        otp_write_parser = self.subparsers.add_parser(
            "write_otp", help="Write specified OTP config script value"
        )
        otp_write_parser.add_argument(
            "key", type=lambda x: int(x, 0), help="Key to write (example: 0x50020A18)"
        )
        otp_write_parser.add_argument(
            "values",
            nargs="+",
            type=lambda x: int(x, 0),
            help="Value(s) to write (example: 0x200)",
        )

        otp_write_parser.add_argument(
            "--force",
            help="Force adding key even if it already exists",
            action="store_true",
        )

        flash_parser = self.subparsers.add_parser(
            "write_flash", help="Write binary file at specified address"
        )

        flash_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the flash area"
        )
        flash_parser.add_argument("filename", help="Binary file path")

        flash_write_bytes_parser = self.subparsers.add_parser(
            "write_flash_bytes", help="Write arbitrary data at a specified address"
        )

        flash_write_bytes_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the flash area"
        )

        flash_write_bytes_parser.add_argument(
            "data",
            nargs="+",
            default=[],
            help="data bytes list as decimal (0-255) or hexadecimal (0x00-0xFF)",
        )

        flash_parser = self.subparsers.add_parser(
            "read_flash", help="read data at specified address and length"
        )

        flash_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the flash area"
        )
        flash_parser.add_argument(
            "length", type=lambda x: int(x, 0), help="number of bytes to read"
        )

        read_otp_parser = self.subparsers.add_parser(
            "read_otp_hex", help="read data at specified address and length"
        )

        read_otp_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the otp area"
        )
        read_otp_parser.add_argument(
            "length", type=lambda x: int(x, 0), help="number of bytes to read"
        )

        flash_parser = self.subparsers.add_parser(
            "image_flash", help="Write the flash binary"
        )
        flash_parser.add_argument("filename", help="Binary file path")

        flash_parser.add_argument(
            "--active_image_address",
            type=lambda x: int(x, 0),
            required=False,
            help="Active image address",
        )

        flash_parser = self.subparsers.add_parser(
            "product_header_check", help="Read the product header and check"
        )
        flash_parser = self.subparsers.add_parser(
            "linker_header",
            help="Generate product header which can be copied in the linker script",
        )

        bootloader_flash_parser = self.subparsers.add_parser(
            "image_bootloader_flash", help="Write an image to flash and add bootloader"
        )
        bootloader_flash_parser.add_argument("filename", help="Binary file path")
        # TODO add custom bootloader

        bootloader_flash_parser = self.subparsers.add_parser(
            "otp_blank_check", help="Check if OTP is blank"
        )

        binary_parser = self.subparsers.add_parser(
            "read_flash_bin",
            help="Read flash and output to file",
        )
        binary_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the flash area"
        )
        binary_parser.add_argument(
            "length", type=lambda x: int(x, 0), help="number of bytes to read"
        )

        binary_parser.add_argument("file", type=str, help="output file")

        otp_binary_parser = self.subparsers.add_parser(
            "read_otp_bin",
            help="Read OTP and output to file",
        )
        otp_binary_parser.add_argument(
            "addr", type=lambda x: int(x, 0), help="Address in the OTP area"
        )
        otp_binary_parser.add_argument(
            "length", type=lambda x: int(x, 0), help="number of bytes to read"
        )

        otp_binary_parser.add_argument("file", type=str, help="output file")

        self.args = self.parser.parse_args()


def main():
    """Create da1469xSerialLoader instance."""
    ezFlashCLI()


if __name__ == "__main__":
    main()
