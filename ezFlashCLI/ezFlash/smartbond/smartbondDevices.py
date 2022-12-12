"""Collection of smartbond devices abstraction classes."""

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


import binascii
import logging
import struct
import sys
import time
from ctypes import c_char_p, c_uint32
from enum import IntEnum

from ..pyjlink import pyjlink

SPI_FLASH_PAGE_SIZE = 256
SPI_FLASH_SECTOR_SIZE = 4096
_69x_DEFAULT_IMAGE_ADDRESS = 0x2000
_69x_DEFAULT_IMAGE_OFFSET = 0x400
_69X_OTP_BASE_ADDR = 0x10080000
_69X_OTP_CFG_SCRIPT_ADDR = _69X_OTP_BASE_ADDR + 0x0C00


class HW_QSPI_BREAK_SEQ_SIZE(IntEnum):
    """QSPI break size enumeration."""

    SIZE_1B = (0,)
    SIZE_2B = 1


class HW_QSPI_BUS_MODE(IntEnum):
    """QSPI bus mode enumeration."""

    SINGLE = (0,)  # Bus mode in single mode
    DUAL = (1,)  # Bus mode in dual mode
    QUAD = 2  # Bus mode in quad mode


class HW_QSPI_COMMON_CMD(IntEnum):
    """QSPI commands enumeration."""

    WRITE_STATUS_REGISTER = (0x01,)
    PAGE_PROGRAM = (0x02,)
    READ_DATA = (0x03,)
    WRITE_DISABLE = (0x04,)
    READ_STATUS_REGISTER = (0x05,)
    WRITE_ENABLE = (0x06,)
    READ_PROTECTION_REGISTERS = (0x3C,)
    PROTECT_SECTOR = (0x36,)
    UNPROTECT_SECTOR = (0x39,)
    SECTOR_ERASE = (0x20,)
    QUAD_PAGE_PROGRAM = (0x32,)
    QPI_PAGE_PROGRAM = (0x02,)
    BLOCK_ERASE = (0x52,)
    CHIP_ERASE = (0xC7,)
    FAST_READ_QUAD = (0xEB,)
    READ_JEDEC_ID = (0x9F,)
    EXIT_CONTINUOUS_MODE = (0xFF,)
    RELEASE_POWER_DOWN = (0xAB,)
    ENTER_POWER_DOWN = (0xB9,)
    FAST_READ_QUAD_4B = (0xEC,)
    SECTOR_ERASE_4B = (0x21,)
    QUAD_PAGE_PROGRAM_4B = (0x34,)
    ENTER_QPI_MODE = (0x38,)  # Requires single mode for the command entry!
    EXIT_QPI_MODE = 0xFF  # Requires quad mode for the command entry!


SMARTBOND_IDENTIFIER = {
    "[50, 53, 50, 50]": "da1469x",
    "[50, 55, 54, 51]": "da1469x",
    "[51, 48, 56, 48]": "da1469x",
    "[50, 55, 57, 56]": "da1470x",
    "[51, 49, 48, 55]": "da1470x",
    "[54, 56, 48, 0, 65]": "da14681",
    "[54, 56, 48, 0, 66]": "da14683",
    "[53, 56, 53, 1, 65]": "da14585",
    "[53, 56, 53, 0, 65]": "da14585",
    "[53, 56, 48, 1, 65]": "da14580",
    "[50, 0, 50, 0, 54]": "da14531",
}


SMARTBOND_PRETTY_IDENTIFIER = {
    "da1470x": "DA1470x",
    "da1469x": "DA1469x",
    "da14681": "DA14680/DA14681",
    "da14683": "DA14682/DA14683",
    "da14585": "DA14585/DA14586",
    "da14580": "DA14580",
    "da14531": "DA14531",
}


class da14xxx:
    """Handler for the Smartbond devices Flash memory."""

    CLK_AMBA_REG = 0x50000000

    def __init__(self, device=None):
        """Initalizate the da14xxxx devices class."""
        self.flash_address_size = 3
        self.polling_interval = 0.01
        self.wait_timeout = 30

        self.link = pyjlink()
        if device:
            logging.debug("Set device to {}".format(device))
            self.link.Device = device
        self.link.init()

    def connect(self, id):
        """Connect through jlink."""
        id = self.link.connect(id)

        if not len(id):
            raise Exception("Device not found")
        return id

    def get_flash(self, flashId, flash_db):
        """Get the flash device id and return its name.

        Args:
            flashId: manufacturer,deviceid,device denisity
            i.e: 0xC22536 for P25Q80H

        Returns:
            Flash configuration

        """
        for flash in flash_db["flash_configurations"]:

            if flashId == (
                int(flash["flash_manufacturer"], 16),
                int(flash["flash_device_type"], 16),
                int(flash["flash_density"], 16),
            ):
                return flash

        return None

    def flash_configure_controller(self, flashid):
        """Set the controller in Continuous mode according flash configuration parameters.

        Notes:
            Requires the flash device to be successfully probed

        """
        pass

    def otp_read(self, key):
        """Fallback function for OTP read."""
        logging.error("OTP not implemented for this device")
        return 0, -9

    def otp_write(self, key, values, force):
        """Fallback function for OTP write."""
        logging.error("OTP not implemented for this device")
        return -9

    def otp_blank_check(self):
        """Fallback function for OTP blank check."""
        logging.error("OTP not implemented for this device")
        sys.exit(1)


class da1453x_da1458x(da14xxx):
    """Derived class for the DA145xx and DA1458xx devices."""

    FLASH_ARRAY_BASE = 0x16000000

    SET_FREEZE_REG = 0x50003300
    PAD_LATCH_REG = 0x5000030C
    SYS_CTRL_REG = 0x50000012
    HWR_CTRL_REG = 0x50000300
    CLK_PER_REG = 0x50000004

    SPI_CTRL_REG = 0x50001200
    SPI_CONFIG_REG = 0x50001204
    SPI_CLOCK_REG = 0x50001208
    SPI_FIFO_CONFIG_REG = 0x5000120C
    SPI_FIFO_STATUS_REG = 0x50001218
    SPI_FIFO_READ_REG = 0x5000121C
    SPI_FIFO_WRITE_REG = 0x50001220
    SPI_CS_CONFIG_REG = 0x50001224

    P0_DATA_REG = 0x50003000
    P00_MODE_REG = 0x50003006
    P00_MODE_REG_RESET = 0x00000200

    OUTPUT = 0x300
    INPUT = 0
    # Word Size 8 bits
    SPI_MODE_8BIT = 0
    # Word Size 16 bits
    SPI_MODE_16BIT = 1
    # Word Size 32 bits
    SPI_MODE_32BIT = 2

    def __init__(self, device=None):
        """Initalizate the da14xxxx parent devices class."""
        da14xxx.__init__(self, device)

    def shift16(self, a):
        """Shit function."""
        shift = 0
        while not (a & 0x1):
            shift += 1
            a = a >> 1
        return shift

    def SetWord16(self, addr, data):
        """Write a 16 bits word."""
        self.link.wr_mem(16, addr, data)

    def SetBits16(self, addr, bitfield_mask, data):
        """Set a 16 bits word according to the mask."""
        reg = self.link.rd_mem(16, addr, 1)[0]
        reg = (reg & (~bitfield_mask)) & 0xFFFF
        wr_data = reg | (data << (self.shift16(bitfield_mask)))
        self.link.wr_mem(16, addr, wr_data)

    def GPIO_SetPinFunction(self, port, pin, mode, function):
        """Set GPIO Pin function."""
        data_reg = self.P0_DATA_REG + (port << 5)
        mode_reg = data_reg + 0x6 + (pin << 1)
        self.link.wr_mem(16, mode_reg, mode | function)

    def GPIO_SetActive(self, port, pin):
        """Set GPIO active."""
        data_reg = self.P0_DATA_REG + (port << 5)
        set_data_reg = data_reg + 2
        self.link.wr_mem(16, set_data_reg, 1 << pin)

    def GPIO_SetInactive(self, port, pin):
        """Set GPIO inactive."""
        data_reg = self.P0_DATA_REG + (port << 5)
        set_data_reg = data_reg + 4
        self.link.wr_mem(16, set_data_reg, 1 << pin)

    def read_flash(self, address, length):
        """Read the flash device.

        Args:
            address: 24 bits int
            length: access length
        """
        read_data = []

        self.flash_init()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_DATA)
        self.spi_access8(address & 0xFF)
        self.spi_access8((address >> 8) & 0xFF)
        self.spi_access8((address >> 16) & 0xFF)
        while length:
            read_data.append(self.spi_access8(0xFF))
            length -= 1

        self.spi_cs_high()

        return read_data

    def flash_probe(self):
        """Probe the flash device.

        Args:
            None
        """
        # reset and halt the cpu
        self.link.reset()

        # init the flash
        self.flash_init()

        # read JEADEC id
        self.spi_set_bitmode(self.SPI_MODE_8BIT)
        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_JEDEC_ID)
        manufacturer = self.spi_access8(0xFF)
        deviceId = self.spi_access8(0xFF)
        density = self.spi_access8(0xFF)
        self.spi_cs_high()

        return (manufacturer, deviceId, density)

    def flash_get_software_protection(self):
        """Read the protected regions of flash.

        Args:
            None
        """
        # reset and halt the cpu
        self.link.reset()

        # init the flash
        self.flash_init()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER)
        protection_bits = (
            self.spi_access8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER) & 0xC
        ) >> 2
        self.spi_cs_high()
        return protection_bits

    def flash_software_unprotect(self):
        """Send the write enable command.

        Args:
            None
        """
        logging.debug("Disabling flash protection.")
        # reset and halt the cpu
        self.link.reset()

        # init the flash
        self.flash_init()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.spi_cs_high()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.WRITE_STATUS_REGISTER)
        self.spi_access8(0x00)
        self.spi_cs_high()

    def flash_erase(self):
        """Execute chip erase.

        Args:
            None
        """
        # reset and halt the cpu
        self.link.reset()

        # init the flash
        self.flash_init()

        if self.flash_get_software_protection() != 0:
            self.flash_software_unprotect()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.spi_cs_high()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.CHIP_ERASE)
        self.spi_cs_high()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER)

        while self.spi_access8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER) & 0x1:
            pass
        self.spi_cs_high()

        return 1

    def flash_program_image(self, fileData, parameters):
        """Program image in the flash.

        Args:
            fileData: file data
            address: start address to program
        """
        if fileData[0] != 0x70 or fileData[1] != 0x50:
            logging.info("Not a bootable image")
            if fileData[3] != 0x7:
                print(
                    "This is not a binary with stack pointer at the beginning",
                    fileData[3],
                )
                return 0
            else:
                logging.info("append booting data")
                header = b"\x70\x50\x00\x00\x00\x00" + struct.pack(">H", len(fileData))

                data = header + fileData
        else:
            # bootable image
            data = fileData

        if self.flash_get_software_protection() != 0:
            self.flash_software_unprotect()

        self.link.jl.JLINKARM_BeginDownload(c_uint32(0))
        self.link.jl.JLINKARM_WriteMem(self.FLASH_ARRAY_BASE, len(data), c_char_p(data))
        bytes_flashed = self.link.jl.JLINKARM_EndDownload()
        if bytes_flashed < 0:
            logging.error("Download failed with code: {}".format(bytes_flashed))
            return 0

        # reset and halt the cpu
        self.link.reset()

        return 1

    def flash_program_data(self, fileData, address=0x0):
        """Program raw data in the flash.

        Args:
            my_data_array: bytes array
            address: destination address
        """
        if self.flash_get_software_protection() != 0:
            self.flash_software_unprotect()

        self.link.jl.JLINKARM_BeginDownload(c_uint32(0))
        self.link.jl.JLINKARM_WriteMem(
            self.FLASH_ARRAY_BASE + address, len(fileData), c_char_p(fileData)
        )
        bytes_flashed = self.link.jl.JLINKARM_EndDownload()
        if bytes_flashed < 0:
            logging.error(
                "Download failed with code: @address {}, {}".format(
                    address, bytes_flashed
                )
            )
            return 0

        # reset and halt the cpu
        self.link.reset()

        return 1

    def make_image_header(self, image):
        """Image header generation.

        Args:
            Image: byte array containing the application
        """
        header = (
            b"\x70\x51\xAA\x01"  # Signature
            + struct.pack("<I", len(image))  # Binary size
            + struct.pack("<I", binascii.crc32(image))  # Crc32
            + b"ezFlashCLI\x00\x00\x00\x00\x00\x00"  # Version string
            + struct.pack("<I", int(time.time()))  # Timestamp
        )
        for i in range(32):
            header += struct.pack("b", 0x0)
        return header

    def flash_program_image_with_bootloader(self, parameters):
        """Program a secondary bootloader and an image in the flash.

        Args:
            parameters: dictionary of parameters
        """
        fileData = parameters["fileData"]
        if "bootloader" in parameters and parameters["bootloader"] is not None:
            bootloader = parameters["bootloader"]
        else:
            bootloader_file = open(
                "ezFlashCLI\\ezFlash\\smartbond\\binaries\\secondary_bootloader_531.bin",
                "rb",
            )
            bootloader = bootloader_file.read()
            bootloader_file.close()

        image1_address = 0x4000
        image2_address = 0xF000
        product_header_position = 0x1A000
        if (
            "product_header_position" in parameters
            and parameters["product_header_position"] is not None
        ):
            product_header_position = parameters["product_header_position"]
        if "image1_address" in parameters and parameters["image1_address"] is not None:
            image1_address = parameters["image1_address"]
        if "image2_address" in parameters and parameters["image2_address"] is not None:
            image2_address = parameters["image2_address"]
        product_header = (
            b"\x70\x52\x00\x00"
            + struct.pack("<I", image1_address)
            + struct.pack("<I", image2_address)
        )

        if fileData[0] != 0x70 or fileData[1] != 0x51:
            logging.info("Not a single image")
            if fileData[3] != 0x7:
                print(
                    "This is not a binary with stack pointer at the beginning",
                    fileData[3],
                )
                return 0
            else:
                logging.info("adding image header")
                header = self.make_image_header(fileData)
                data = header + fileData
        else:
            # Already single image
            data = fileData

        if self.flash_program_data(product_header, product_header_position):
            logging.info("Flash product header success")
        else:
            logging.error("Flash product header failed")
            return 0

        if self.flash_program_data(data, image1_address):
            logging.info("Flash image success")
        else:
            logging.error("Flash image failed")
            return 0

        if self.flash_program_data(data, image2_address):
            logging.info("Flash image success")
        else:
            logging.error("Flash image failed")
            return 0
        if self.flash_program_image(bootloader, parameters):
            logging.info("Flash bootloader success")
            return 1
        else:
            logging.error("Flash bootloader failed")
            return 0


class da14531(da1453x_da1458x):
    """Derived class for the da14531 devices."""

    OTPC_MODE_REG = 0x07F40000
    OTPC_STAT_REG = 0x07F40004
    OTPC_TIM1_REG = 0x07F40010
    OTPC_TIM2_REG = 0x07F40014
    OTPC_MODE_DSTBY = 0  # OTP cell is powered on, LDO is inactive
    OTPC_MODE_STBY = 1  # OTP cell and LDO are powered on, chip select is deactivated
    OTPC_MODE_READ = 2  # OTP cell can be read
    OTPC_MODE_PROG = 3  # OTP cell can be programmed
    OTPC_MODE_PVFY = 4  # OTP cell can be read in PVFY margin read mode
    OTPC_MODE_RINI = 5  # OTP cell can be read in RINI margin read mode
    OTPC_MODE_AREAD = 6  # OTP cell can be read by the internal DMA

    OTPC_TIM1_REG_RESET = 0x0999000F
    OTPC_TIM2_REG_RESET = 0xA4040409
    OTP_START = 0x07F80000
    OTP_HEADER_START = 0x07F87ED0
    OTP_SIZE = 0x8000
    OTP_CELL_SIZE = 0x04
    OTP_HEADER_SIZE = OTP_SIZE - (OTP_HEADER_START - OTP_START)
    OTP_CELL_NUM = int(OTP_SIZE / OTP_CELL_SIZE)  # Maximum number of OTP cells
    OTP_HEADER_CELL_NUM = int(OTP_HEADER_SIZE / OTP_CELL_SIZE)

    SPI_PORT = 0
    SPI_CLK_PIN = 4
    SPI_CS_PIN = 1
    SPI_DI_PIN = 3
    SPI_DO_PIN = 0

    def __init__(self):
        """Initalizate the da14xxxx parent devices class."""
        da1453x_da1458x.__init__(self, b"DA14531")

    def spi_cs_low(self):
        """Set the flash CS low."""
        self.SetBits16(self.SPI_CTRL_REG, 0x20, 0)  # release reset fifo
        self.SetWord16(self.SPI_CS_CONFIG_REG, 1)

    def spi_cs_high(self):
        """Set the flash CS high."""
        self.SetWord16(self.SPI_CS_CONFIG_REG, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x20, 1)  # reset fifo

    def flash_init(self):
        """Initialize flash controller and make sure the Flash device exits low power mode.

        Args:
            None
        """
        self.SetWord16(self.CLK_AMBA_REG, 0x00)  # set clocks (hclk and pclk ) 16MHz
        self.SetWord16(self.SET_FREEZE_REG, 0x8)  # stop watch dog
        self.SetBits16(self.PAD_LATCH_REG, 0x1, 1)  # open pads
        self.SetBits16(self.SYS_CTRL_REG, 0x0180, 0x3)  # SWD_DIO = P0_10
        self.SetWord16(self.HWR_CTRL_REG, 1)  # disable HW reset

        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CS_PIN, 0x300, 29)  # SPI_CS
        self.GPIO_SetActive(self.SPI_PORT, self.SPI_CS_PIN)
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CLK_PIN, 0x300, 28)  # SPI_CLK
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DO_PIN, 0x300, 27)  # SPI_D0
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DI_PIN, 0, 26)  # SPI_DI

        self.SetBits16(self.CLK_PER_REG, 0x400, 1)
        # Disable SPI / Reset FIFO in SPI Control Register
        self.SetWord16(self.SPI_CTRL_REG, 0x0020)  # fifo reset
        # Set SPI Word length
        self.spi_set_bitmode(self.SPI_MODE_8BIT)
        # Set SPI Mode (CPOL, CPHA)
        # spi_set_cp_mode(SPI_CP_MODE_0)
        self.SetBits16(self.SPI_CONFIG_REG, 0x0003, 3)  # mode 0
        # Set SPI Master/Slave mode
        self.SetBits16(self.SPI_CONFIG_REG, 0x80, 0)  # master mode

        # Set SPI FIFO threshold levels to 0
        self.SetWord16(self.SPI_FIFO_CONFIG_REG, 0)
        # Set SPI clock in async mode (mandatory)
        self.SetBits16(self.SPI_CLOCK_REG, 0x0080, 1)

        # Set SPI master clock speed
        # spi_set_speed(SPI_SPEED_MODE_2MHz)
        self.SetBits16(self.SPI_CLOCK_REG, 0x007F, 7)  # 2MHz
        # Set SPI clock edge capture data
        self.SetBits16(self.SPI_CTRL_REG, 0x0040, 0)

    def spi_access8(self, dataToSend):
        """Send data over the SPI interface.

        Args:
            dataToSend: Byte array
        """
        dataRead = 0

        # Clear Tx, Rx and DMA enable paths in Control Register
        self.SetBits16(self.SPI_CTRL_REG, 0x1F, 0)

        # Enable TX path
        self.SetBits16(self.SPI_CTRL_REG, 0x2, 1)
        # Enable RX path
        self.SetBits16(self.SPI_CTRL_REG, 0x4, 1)
        # Enable SPI
        self.SetBits16(self.SPI_CTRL_REG, 0x1, 1)

        # Write (low part of) dataToSend
        self.SetWord16(self.SPI_FIFO_WRITE_REG, dataToSend)

        # Wait while RX FIFO is empty
        while (self.link.rd_mem(16, self.SPI_FIFO_STATUS_REG, 1)[0] & 0x1000) != 0:
            pass

        dataRead = self.link.rd_mem(16, self.SPI_FIFO_READ_REG, 1)[0] & 0xFF

        # Wait until transaction is finished and SPI is not busy
        while (self.link.rd_mem(16, self.SPI_FIFO_STATUS_REG, 1)[0] & 0x8000) != 0:
            pass
        return dataRead

    def spi_set_bitmode(self, spi_wsz):
        """Set the word size."""
        if spi_wsz == self.SPI_MODE_16BIT:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7C, 15)
        elif spi_wsz == self.SPI_MODE_32BIT:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7C, 31)
        else:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7C, 7)

    def otp_set_mode(self, mode):
        """Move the OTPC in new mode."""
        # Change mode only if new mode is different than the old one
        otpmode = self.link.rd_mem(32, self.OTPC_MODE_REG, 1)[0]
        if otpmode != mode:
            self.link.wr_mem(32, self.OTPC_MODE_REG, mode)

        # Wait for mode change
        while (self.link.rd_mem(32, self.OTPC_STAT_REG, 1)[0] & 0x4) == 0:
            pass

    def otp_init(self):
        """Init the OTP controller."""
        # Enable OTPC clock
        clkreg = self.link.rd_mem(16, self.CLK_AMBA_REG, 1)[0]
        self.link.wr_mem(16, self.CLK_AMBA_REG, clkreg | 0x80)

        # Mode to standby
        self.otp_set_mode(self.OTPC_MODE_DSTBY)

        # Default timings
        self.link.wr_mem(32, self.OTPC_TIM1_REG, self.OTPC_TIM1_REG_RESET)
        self.link.wr_mem(32, self.OTPC_TIM2_REG, self.OTPC_TIM1_REG_RESET)

    def otp_blank_check(self):
        """Check if the program area of OTP is blank."""
        self.otp_init()
        self.otp_set_mode(self.OTPC_MODE_READ)
        otp_contents = self.link.rd_mem(32, self.OTP_START, self.OTP_CELL_NUM)
        otp_blank = True
        header_blank = True
        for entry in range(self.OTP_CELL_NUM - self.OTP_HEADER_CELL_NUM):
            if otp_contents[entry] != 0xFFFFFFFF:
                otp_blank = False
                break
        for entry in range(
            self.OTP_CELL_NUM - self.OTP_HEADER_CELL_NUM, self.OTP_CELL_NUM
        ):
            if otp_contents[entry] != 0xFFFFFFFF:
                header_blank = False
                break
        if header_blank is True:
            logging.error(
                "The OTP header is blank, this shouldn't be possible. Please ensure the connection to the chip is correct"
            )
        return otp_blank

    def otp_read_raw(self, address, length=1):
        """Check if the program area of OTP is blank."""
        if address < 0:
            logging.error("Address can't be negative")
            return 0
        if (
            address >= self.OTP_SIZE and address < self.OTP_START
        ) or address >= self.OTP_SIZE + self.OTP_START:
            logging.error("Address out of range")
            return 0
        if address < self.OTP_SIZE:
            address += self.OTP_START
        self.otp_init()
        self.otp_set_mode(self.OTPC_MODE_READ)

        return self.link.rd_mem(8, address, length)

    def release_reset(self):
        """On 531 the reset pin is shared with the default flash MOSI pin.

        The function restore the pin into reset mode
        """
        self.link.wr_mem(16, self.HWR_CTRL_REG, 0x0)
        self.link.wr_mem(16, self.P00_MODE_REG, self.P00_MODE_REG_RESET)

    def flash_program_image(self, fileData, parameters):
        """Program an image in the flash.

        Args:
            fileData: byte array
            address: access address
        """
        result = super().flash_program_image(fileData, parameters)
        self.release_reset()
        return result

    def flash_program_image_with_bootloader(self, parameters):
        """Program a secondary bootloader and an image in the flash.

        Args:
            parameters: dictionary of parameters
        """
        result = super().flash_program_image_with_bootloader(parameters)
        self.release_reset()
        return result

    def read_flash(self, address, length):
        """Read flash data.

        Args:
            address: 24 bits int
            length: access length
        """
        read_data = super().read_flash(address, length)
        self.release_reset()
        return read_data


class da14585(da1453x_da1458x):
    """Derived class for the da14585 devices."""

    SPI_PORT = 0
    SPI_CLK_PIN = 0
    SPI_CS_PIN = 3
    SPI_DI_PIN = 5
    SPI_DO_PIN = 6

    SPI_CTRL_REG1 = 0x50001208
    SPI_RX_TX_REG0 = 0x50001202
    SPI_CLEAR_INT = 0x50001206

    def __init__(self, device=None):
        """Initalizate the da14xxxx parent devices class."""
        da1453x_da1458x.__init__(self, b"DA14585")

    def spi_set_bitmode(self, spi_wsz):
        """Set the word size."""
        # force to 8 bits whatever the size is
        self.SetBits16(self.SPI_CTRL_REG, 0x1, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x180, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x1, 1)

    def spi_cs_low(self):
        """Set the flash CS low."""
        self.GPIO_SetInactive(self.SPI_PORT, self.SPI_CS_PIN)

    def spi_cs_high(self):
        """Set the flash CS high."""
        self.GPIO_SetActive(self.SPI_PORT, self.SPI_CS_PIN)

    def spi_access8(self, dataToSend):
        """Send data over the SPI interface.

        Args:
            dataToSend: Byte array
        """
        # Set FIFO Bidirectional mode
        self.SetBits16(self.SPI_CTRL_REG1, 0x3, 2)

        # Write (low part of) dataToSend
        self.SetWord16(self.SPI_RX_TX_REG0, dataToSend)

        # Polling to wait for spi transmission
        while (self.link.rd_mem(16, self.SPI_CTRL_REG, 1)[0] & 0x2000) == 0:
            pass

        # Clear pending flag
        self.SetWord16(self.SPI_CLEAR_INT, 0x1)

        # Return data read from spi slave
        return self.link.rd_mem(16, self.SPI_RX_TX_REG0, 1)[0]

    def flash_init(self):
        """Initialize flash controller and make sure the Flash device exits low power mode.

        Args:
            None
        """
        self.SetWord16(self.CLK_AMBA_REG, 0x00)  # set clocks (hclk and pclk ) 16MHz
        self.SetWord16(self.SET_FREEZE_REG, 0x8)  # stop watch dog
        self.SetBits16(self.SYS_CTRL_REG, 0x0180, 0x3)  # SWD_DIO = P0_10

        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CS_PIN, 0x300, 8)  # SPI_CS
        self.GPIO_SetActive(self.SPI_PORT, self.SPI_CS_PIN)
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CLK_PIN, 0x300, 7)  # SPI_CLK
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DO_PIN, 0x300, 6)  # SPI_D0
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DI_PIN, 0, 5)  # SPI_DI

        self.SetBits16(self.CLK_PER_REG, 0x800, 1)

        # Set SPI Word length
        self.spi_set_bitmode(self.SPI_MODE_8BIT)


class da1468x_da1469x_da1470x(da14xxx):
    """Base class for the 68x,69x family."""

    FLASH_READ_ARRAY_BASE = 0x36000000
    FLASH_ARRAY_BASE = 0x36000000

    QSPIC_CTRLBUS_REG = 0x00  # Control register 0
    QSPIC_CTRLMODE_REG = 0x04  # Control register 1
    QSPIC_RECVDATA_REG = 0x08  # Data register (TX and RX)
    QSPIC_BURSTCMDA_REG = 0x0C  # Status register
    QSPIC_BURSTCMDB_REG = 0x10  # Clock prescale register
    QSPIC_WRITEDATA_REG = 0x18  # write data registers in manual mode
    QSPIC_READDATA_REG = 0x1C  # read data registers in manual mode

    def __init__(self, device=None):
        """Initialize the QSPI controller and parent class."""
        da14xxx.__init__(self, device)

        self.QSPIC_CTRLBUS_REG += self.QPSPIC_BASE
        self.QSPIC_CTRLMODE_REG += self.QPSPIC_BASE
        self.QSPIC_RECVDATA_REG += self.QPSPIC_BASE
        self.QSPIC_BURSTCMDA_REG += self.QPSPIC_BASE
        self.QSPIC_BURSTCMDB_REG += self.QPSPIC_BASE
        self.QSPIC_WRITEDATA_REG += self.QPSPIC_BASE
        self.QSPIC_READDATA_REG += self.QPSPIC_BASE

        self.myaddress = 0x0

    def read_flash(self, address, length):
        """Read flash.

        Args:
            address: 24 bits int
            length: int
        """
        return self.link.rd_mem(8, self.FLASH_READ_ARRAY_BASE + address, length)

    def flash_hw_qspi_cs_enable(self):
        """Enable QSPI CS.

        Args:
            None
        """
        self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x8)

    def flash_hw_qspi_cs_disable(self):
        """Disable QSPI CS.

        Args:
            None
        """
        self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x10)

    def flash_set_automode(self, mode):
        """Set the device in automode.

        Args:
            mode: boolean
        """
        ctrlmode = self.link.rd_mem(32, self.QSPIC_CTRLMODE_REG, 1)[0]
        if mode:
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, ctrlmode | 0x1)
        else:
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, ctrlmode & ~(0x1))
        return True

    def flash_set_busmode(self, mode):
        """Set the QSPI controller bus mode.

        Args:
            mode : HW_QSPI_BUS_MODE type

        Returns:
            True: success
            False: error
        """
        if mode == HW_QSPI_BUS_MODE.SINGLE:
            # set single mode
            self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x1)
            # read the ctrlmode reg
            ctrlmode = self.link.rd_mem(32, self.QSPIC_CTRLMODE_REG, 1)[0]

            # writte the data line mode
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, ctrlmode | 0x3C)

        elif mode == HW_QSPI_BUS_MODE.DUAL:
            raise Exception("unsupported DUAL SPI mode")

        else:
            # set quad mode
            self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x4)

            # read the ctrlmode reg
            ctrlmode = self.link.rd_mem(32, self.QSPIC_CTRLMODE_REG, 1)[0]

            # writte the data line mode
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, ctrlmode & ~(0xC))

        return True

    def flash_hw_qspi_write8(self, data):
        """Write a byte on the qspi interface.

        Args:
            data: byte
        """
        self.link.wr_mem(8, self.QSPIC_WRITEDATA_REG, data)

    def flash_hw_qspi_read8(self):
        """Read a byte on the qspi interface.

        Args:
            None
        Return:
        """
        return self.link.rd_mem(8, self.QSPIC_READDATA_REG, 1)[0]

    def whileFlashBusy(self):
        """Block while the flash is busy.

        Args:
            None
        """
        wait_time = 0

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER)
        while True:

            status = self.flash_hw_qspi_read8()
            if not (status & 0x1):
                self.flash_hw_qspi_cs_disable()
                return True
            if wait_time > self.wait_timeout:
                return False

            time.sleep(self.polling_interval)
            wait_time += self.polling_interval

    def flash_erase(self):
        """Erase the flash content.

        Args:
            None
        """
        self.link.reset()

        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.SINGLE)

        self.flash_reset()

        # send flash erase
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.CHIP_ERASE)
        self.flash_hw_qspi_cs_disable()

        self.whileFlashBusy()  # wait for the operation to be over

        # set automode
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

        return True

    def flash_sector_erase(self, address):
        """Erase sector().

        Args:
            address: Address (int)
            data: bytes
        """
        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.SINGLE)

        # send flash erase
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.SECTOR_ERASE)

        for data in address.to_bytes(self.flash_address_size, "big"):
            self.flash_hw_qspi_write8(data)

        self.flash_hw_qspi_cs_disable()

        self.whileFlashBusy()

        # set automode
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

    def flash_page_program(self, address, data_array):
        """Program a page (up to 256 bytes).

        Args:
            address: Address (int)
            data: bytes
        """
        if not len(data_array):
            raise Exception("data is empty")

        if isinstance(data_array, bytes):
            print(type(data_array), type(bytes))
            raise Exception("data should be byte it is {}".format(type(data_array)))

        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.SINGLE)

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.PAGE_PROGRAM)

        for data in address.to_bytes(self.flash_address_size, "big"):
            self.flash_hw_qspi_write8(data)

        for data in data_array:
            self.flash_hw_qspi_write8(data)

        self.flash_hw_qspi_cs_disable()

        self.whileFlashBusy()

        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

    def flash_reset_continuous_mode(self, breakSize):
        """Reset the flash.

        Args:
            breakSize: HW_QSPI_BREAK_SEQ_SIZE
        """
        self.flash_hw_qspi_cs_enable()

        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.EXIT_CONTINUOUS_MODE)
        if breakSize == HW_QSPI_BREAK_SEQ_SIZE.SIZE_2B:
            self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.EXIT_CONTINUOUS_MODE)

        self.flash_hw_qspi_cs_disable()

    def flash_reset(self):
        """Reset the flash.

        Args:
            None
        """
        # reset both 1 and 2 break to be sure it's reset
        self.flash_reset_continuous_mode(HW_QSPI_BREAK_SEQ_SIZE.SIZE_1B)
        self.flash_reset_continuous_mode(HW_QSPI_BREAK_SEQ_SIZE.SIZE_2B)

        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)

        self.flash_hw_qspi_write8(0x66)
        self.flash_hw_qspi_write8(0x99)

        self.flash_set_busmode(HW_QSPI_BUS_MODE.SINGLE)

        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.RELEASE_POWER_DOWN)
        pass

    def flash_init(self):
        """Initiallize QSPI controller and make sure thef lash device exits low power mode.

        Args:
            None
        """
        self.flash_set_automode(False)

        self.flash_reset()

        self.flash_set_automode(True)

    def flash_probe(self):
        """Probe the flash device JEDEC identifier.

        Args:
            None

        Returns:
            Tuple (Manufacturer id, device type, device density)
        """
        # reset and halt the cpu
        self.link.reset()

        # init the flash
        self.flash_init()

        # disable automode
        self.flash_set_automode(False)

        # read JEADEC id
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.READ_JEDEC_ID)
        manufacturer = self.flash_hw_qspi_read8()
        deviceId = self.flash_hw_qspi_read8()
        density = self.flash_hw_qspi_read8()
        self.flash_hw_qspi_cs_disable()

        # set automode
        self.flash_set_automode(True)

        return (manufacturer, deviceId, density)

    def flash_configure_controller(self, flashid):
        """Set the controller in Continuous mode according flash configuration parameters.

        Notes:
            Requires the flash device to be successfully probed

        """
        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)

        # issue a write enable
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        # issue config sequence
        configCommand = flashid["flash_write_config_command"].split(" ")

        self.flash_hw_qspi_cs_enable()

        for cmd in configCommand[:-1]:  # the last one is a termation character
            self.flash_hw_qspi_write8(int(cmd[2:], 16))

        self.flash_hw_qspi_cs_disable()

        self.link.wr_mem(
            32,
            self.QSPIC_BURSTCMDA_REG,
            int(flashid["flash_burstcmda_reg_value"][2:], 16),
        )
        self.link.wr_mem(
            32,
            self.QSPIC_BURSTCMDB_REG,
            int(flashid["flash_burstcmdb_reg_value"][2:], 16),
        )

        if "flash_ctrlmode_reg_value" in flashid:
            self.link.wr_mem(
                32,
                self.QSPIC_CTRLMODE_REG,
                int(flashid["flash_ctrlmode_reg_value"][2:], 16),
            )

        self.link.rd_mem(32, self.QSPIC_BURSTCMDA_REG, 1)
        self.link.rd_mem(32, self.QSPIC_BURSTCMDB_REG, 1)
        self.link.rd_mem(32, self.QSPIC_CTRLMODE_REG, 1)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

    def flash_program_data(self, my_data_array, address=0x80000000):
        """Program raw data in the flash.

        Args:
            my_data_array: bytes array
            address: destination address
        """
        self.link.jl.JLINKARM_BeginDownload(c_uint32(0))
        self.link.jl.JLINKARM_WriteMem(
            self.FLASH_ARRAY_BASE + address, len(my_data_array), c_char_p(my_data_array)
        )
        bytes_flashed = self.link.jl.JLINKARM_EndDownload()
        if bytes_flashed < 0:
            logging.error(
                "Download failed with code: @{:x} {}".format(
                    self.FLASH_ARRAY_BASE, bytes_flashed
                )
            )
            sys.exit(bytes_flashed)
        return 1


class da1469x(da1468x_da1469x_da1470x):
    """Derived class for the da1469x devices."""

    OTPC_BASE = 0x30070000
    QPSPIC_BASE = 0x38000000
    PRODUCT_HEADER_SIZE = 0x1000
    IMG_IVT_OFFSET = 0x400
    CACHE_FLASH_REG = 0x100C0040

    OTPC_MODE_REG = 0x00  # Mode register
    OTPC_STAT_REG = 0x04  # Status register
    OTPC_PADDR_REG = 0x08  # The address of the word that will be programmed
    OTPC_PWORD_REG = 0x0C  # The 32-bit word that will be programmed
    OTPC_TIM1_REG = 0x10  # Various timing parameters of the OTP cell
    OTPC_TIM2_REG = 0x14  # Various timing parameters of the OTP cell

    OTPC_MODE_PDOWN = 0  # OTP cell and LDO are inactive
    OTPC_MODE_DSTBY = 1  # OTP cell is powered on LDO is inactive
    OTPC_MODE_STBY = 2  # OTP cell and LDO are powered on, chip select is deactivated
    OTPC_MODE_READ = 3  # OTP cell can be read
    OTPC_MODE_PROG = 4  # OTP cell can be programmed
    OTPC_MODE_PVFY = 5  # OTP cell can be read in PVFY margin read mode
    OTPC_MODE_RINI = 6  # OTP cell can be read in RINI margin read mode
    OTPC_TIM1_REG_RESET = 0x0999101F
    OTPC_TIM2_REG_RESET = 0xA4040409

    OTP_BASE = 0x10080000
    OTP_CFG_SCRIPT_OFFSET = 0x0C00
    OTP_CFG_SCRIPT_ADDR = OTP_BASE + OTP_CFG_SCRIPT_OFFSET
    OTP_CFG_SCRIPT_ENTRY_SIZE = 4
    OTP_CFG_SCRIPT_ENTRY_CNT_MAX = 256

    def __init__(self, name=b"DA1469x"):
        """Initalizate the da14xxxx parent devices class."""
        da1468x_da1469x_da1470x.__init__(self, name)

        self.OTPC_MODE_REG += self.OTPC_BASE
        self.OTPC_STAT_REG += self.OTPC_BASE
        self.OTPC_PADDR_REG += self.OTPC_BASE
        self.OTPC_PWORD_REG += self.OTPC_BASE
        self.OTPC_TIM1_REG += self.OTPC_BASE
        self.OTPC_TIM2_REG += self.OTPC_BASE

    def make_image_header(self, image):
        """Image header generation.

        Args:
            Image: byte array containing the application

        For more details about the product header, please refer the
        `DA1469x datasheet <https://www.dialog-semiconductor.com/sites/default/files/2020-12/da1469x_datasheet_3v2.pdf>`_
        Figure 13
        """
        buff = b""
        buff += struct.pack(">2c", b"Q", b"q")
        buff += struct.pack("<I", len(image))
        buff += struct.pack("<I", binascii.crc32(image))
        buff += bytes("ezFlashCLI", "utf-8")
        # pad the version string
        for i in range(6):
            buff += struct.pack("b", 0x0)
        # add the time stamp
        buff += struct.pack("<I", int(time.time()))
        buff += struct.pack("<I", self.IMG_IVT_OFFSET)
        buff += struct.pack("<H", 0x22AA)
        buff += struct.pack("<H", 0x0)
        buff += struct.pack("<H", 0x44AA)
        buff += struct.pack("<H", 0x0)

        return buff

    def scatterfile_product_header(
        self,
        flash_burstcmda_reg_value,
        flash_burstcmdb_reg_value,
        flash_write_config_command,
        active_fw_image_address=0x2000,
        update_fw_image_address=0x2000,
    ):
        """Calculate product header based on inputs.

        Args:
            flash_burstcmda_reg_value: 32 bits burst command
            flash_burstcmdb_reg_value: 32 bits burst command
            flash_write_config_command: flash configuration command
            active_fw_image_address: Active image address
            update_fw_image_address: Update image address

        Returns a text array that can be pasted in the linker script

        """
        cmd_len = len(flash_write_config_command.split(" "))

        headerarray = self.make_product_header(
            flash_burstcmda_reg_value,
            flash_burstcmdb_reg_value,
            flash_write_config_command,
            active_fw_image_address,
            update_fw_image_address,
        )

        crc = struct.unpack("H", headerarray[(22 + cmd_len) : (24 + cmd_len)])[0]

        outputArray = """
#if ( dg_configUSE_SEGGER_FLASH_LOADER == 1 )
        .prod_head :
        AT ( QSPI_FLASH_ADDRESS)
        {{
                __prod_head_start = .;
                SHORT(0x7050)                   // 'Pp' flag
                LONG(QSPI_FW_BASE_OFFSET)       // active image pointer
                LONG(QSPI_FW_BASE_OFFSET)       // update image pointer
                LONG({})                // busrtcmdA
                LONG({})                // busrtcmdB
                SHORT(0x11AA)                   // Flash config section
                SHORT(0x{:04x})                   // Flash config length
{}
                SHORT(0x{:04x})                   // CRC

                . =  __prod_head_start + 0x1000;
        }} > ROM = 0xFF

        .prod_head_backup :
        AT ( QSPI_FLASH_ADDRESS + 0x1000)
        {{
                __prod_head_backup_start = .;
                SHORT(0x7050)                   // 'Pp' flag
                LONG(QSPI_FW_BASE_OFFSET)       // active image pointer
                LONG(QSPI_FW_BASE_OFFSET)       // update image pointer
                LONG({})                // busrtcmdA
                LONG({})                // busrtcmdB
                SHORT(0x11AA)                   // Flash config section
                SHORT(0x{:04x})                     // Flash config length
{}
                SHORT(0x{:04x})                   // CRC


                . =  __prod_head_backup_start + 0x1000;

        }} > ROM = 0xFF

        .img_head :
        AT (QSPI_FW_BASE_ADDRESS)
        {{
                _img_head_start = .;
                SHORT(0x7151)                   // 'Pp' flag
                LONG(SIZEOF(.text))
                LONG(0x0)                       // crc, doesn't matter
                LONG(0x0)                       // version, doesn't matter
                LONG(0x0)                       // version, doesn't matter
                LONG(0x0)                       // version, doesn't matter
                LONG(0x0)                       // version, doesn't matter
                LONG(0x0)                       // timestamp, doesn't matter
                LONG(QSPI_FW_IVT_OFFSET)        // IVT pointer
                SHORT(0x22AA)                   // Security section type
                SHORT(0x0)                      //Security section length
                SHORT(0x44AA)                   // Device admin type
                SHORT(0x0)                      // Device admin length


                . = _img_head_start + 0x400;

        }} > ROM = 0xFF

#endif /* dg_configUSE_SEGGER_FLASH_LOADER */
        """
        outputArray = outputArray.format(
            flash_burstcmda_reg_value,
            flash_burstcmdb_reg_value,
            len(flash_write_config_command.split(" ")),
            self.add_flash_sequence(flash_write_config_command),
            crc,
            flash_burstcmda_reg_value,
            flash_burstcmdb_reg_value,
            len(flash_write_config_command.split(" ")),
            self.add_flash_sequence(flash_write_config_command),
            crc,
        )
        print(outputArray)
        return outputArray

    def add_flash_sequence(self, conf_seq):
        """Add flash sequence depending on the conf."""
        data = ""
        for databyte in conf_seq.split(" "):
            data += "                BYTE({})                      // Flash config sequence\n".format(
                databyte
            )

        return data

    def make_product_header(
        self,
        flash_burstcmda_reg_value,
        flash_burstcmdb_reg_value,
        flash_write_config_command,
        active_fw_image_address=0x2000,
        update_fw_image_address=0x2000,
    ):
        """Calculate product header based on inputs.

        Args:
            flash_burstcmda_reg_value: 32 bits burst command
            flash_burstcmdb_reg_value: 32 bits burst command
            flash_write_config_command: flash configuration command
            active_fw_image_address: Active image address
            update_fw_image_address: Update image address

        For more details about the product header, please refer the
        `DA1469x datasheet <https://www.dialog-semiconductor.com/sites/default/files/2020-12/da1469x_datasheet_3v2.pdf>`_
        Figure 13

        """
        configCommand = flash_write_config_command.split(" ")
        buff = b""
        buff += struct.pack(">2c", b"P", b"p")
        buff += struct.pack(
            "<2I", int(active_fw_image_address), int(update_fw_image_address)
        )
        buff += struct.pack(
            "<2I",
            int(flash_burstcmda_reg_value[2:], 16),
            int(flash_burstcmdb_reg_value[2:], 16),
        )
        buff += struct.pack(">H", 0xAA11)
        buff += struct.pack("H", len(configCommand))
        for cmd in configCommand:
            buff += struct.pack("<B", int(cmd, 16))
        buff += struct.pack("<H", binascii.crc_hqx(buff, 0xFFFF))
        buff += b"\xFF" * (self.PRODUCT_HEADER_SIZE - len(buff))
        return buff

    def read_product_header(self):
        """Read the product header."""
        dataArray = self.link.rd_mem(
            8, self.FLASH_READ_ARRAY_BASE, self.PRODUCT_HEADER_SIZE
        )

        product_header = b""
        for data in dataArray:
            product_header += struct.pack("<B", data)

        return product_header

    def check_address(self, address):
        """Check if an address is within the parameters for the cache.

        Args:
            address: Address to check
        """
        cache_flash_reg = self.link.rd_mem(32, self.CACHE_FLASH_REG, 1)
        flash_region_size = 0x2000000 >> (cache_flash_reg[0] & 0x7)
        if address < 0x2000 or address % flash_region_size > 0x3000:
            return False
        return True

    def flash_program_image(self, fileData, parameters):
        """Program and image in the flash.

        Args:
            fileData: Byte array
            flashid: tuple extracted from the flash database
        """
        if fileData[:2] == b"Pp":
            logging.info("[DA1469x] Program image")
            self.flash_program_data(fileData, 0x0)
        else:
            if fileData[:2] != b"Qq":
                logging.info("[DA1469x] Add image header")
                ih = self.make_image_header(fileData)
                ih += b"\xFF" * (_69x_DEFAULT_IMAGE_OFFSET - len(ih))
                fileData = ih + fileData

            logging.info("[DA1469x] Program bin")
            active_fw_image_address = _69x_DEFAULT_IMAGE_ADDRESS
            if parameters["active_fw_image_address"] is not None:
                if not self.check_address(parameters["active_fw_image_address"]):
                    logging.error(
                        "active_fw_image_address out of range, it should be bigger than 0x2000 and the Firmware partition needs to start at an address which is a CACHE_FLASH_REG[FLASH_REGION_SIZE] multiple plus an offset of zero to three sectors"
                    )
                    return 0
                active_fw_image_address = parameters["active_fw_image_address"]
            update_fw_image_address = active_fw_image_address
            logging.debug(
                "[DA1469x] active_fw_image_address " + str(active_fw_image_address)
            )
            logging.debug(
                "[DA1469x] update_fw_image_address " + str(update_fw_image_address)
            )
            self.flash_program_data(fileData, active_fw_image_address)

            logging.info("[DA1469x] Program product header")
            ph = self.make_product_header(
                parameters["flashid"]["flash_burstcmda_reg_value"],
                parameters["flashid"]["flash_burstcmdb_reg_value"],
                parameters["flashid"]["flash_write_config_command"],
                active_fw_image_address=active_fw_image_address,
                update_fw_image_address=update_fw_image_address,
            )
            self.flash_program_data(ph, 0x0)
            self.flash_program_data(ph, 0x1000)
        logging.info("[DA1469x] Program success")
        return 1

    def otp_init(self):
        """Init the OTP controller."""
        # Enable OTPC clock
        clkreg = self.link.rd_mem(16, self.CLK_AMBA_REG, 1)[0]
        self.link.wr_mem(16, self.CLK_AMBA_REG, clkreg | 0x200)

        # Mode to standby
        self.otp_set_mode(self.OTPC_MODE_DSTBY)

        # Default timings
        self.link.wr_mem(32, self.OTPC_TIM1_REG, self.OTPC_TIM1_REG_RESET)
        self.link.wr_mem(32, self.OTPC_TIM2_REG, self.OTPC_TIM2_REG_RESET)

    def otp_set_mode(self, mode):
        """Move the OTPC in new mode."""
        # Change mode only if new mode is different than the old one
        otpmode = self.link.rd_mem(32, self.OTPC_MODE_REG, 1)[0]
        if otpmode != mode:
            self.link.wr_mem(32, self.OTPC_MODE_REG, mode)

        # Wait for mode change
        while (self.link.rd_mem(32, self.OTPC_STAT_REG, 1)[0] & 0x4) == 0:
            pass

    def otp_verify_words(self, words, offset, mode):
        """Verify OTP words."""
        # Verify words
        self.otp_set_mode(mode)
        for word in words:
            read = self.link.rd_mem(
                self.OTP_CFG_SCRIPT_ENTRY_SIZE * 8, self.OTP_CFG_SCRIPT_ADDR + offset, 1
            )[0]
            if read != word:
                logging.error(
                    "OTP verify fail: mode {}, offset 0x{:x}, read 0x{:x}, written 0x{:x}".format(
                        mode, offset, read, word
                    )
                )
                return False
            offset += self.OTP_CFG_SCRIPT_ENTRY_SIZE
        return True

    def otp_write_words(self, words, offset):
        """Write OTP words."""
        # Convert offset in config script (in bytes) to offset in cells from start of OTP
        cell_offset = int(
            (self.OTP_CFG_SCRIPT_OFFSET + offset) / self.OTP_CFG_SCRIPT_ENTRY_SIZE
        )

        # Write words
        self.otp_set_mode(self.OTPC_MODE_PROG)
        for word in words:
            self.link.wr_mem(32, self.OTPC_PWORD_REG, word)
            self.link.wr_mem(32, self.OTPC_PADDR_REG, cell_offset)
            while (self.link.rd_mem(32, self.OTPC_STAT_REG, 1)[0] & 0x2) == 0:
                pass
            cell_offset += 1

        # Wait for programming
        while (self.link.rd_mem(32, self.OTPC_STAT_REG, 1)[0] & 0x1) == 0:
            pass

        # Verify
        if not self.otp_verify_words(words, offset, self.OTPC_MODE_PVFY):
            return False
        if not self.otp_verify_words(words, offset, self.OTPC_MODE_RINI):
            return False

        return True

    def otp_read(self, key):
        """Read the OTP and search for a key.

        Args:
            key: OTP entry to look for, value will be printed

        Returns:
            count: number of times key was found
            offset: OTP offset of first free entry, or negative for error
        """
        # Init OTP
        self.otp_init()
        self.otp_set_mode(self.OTPC_MODE_READ)

        # Read whole config script
        entries = self.link.rd_mem(
            self.OTP_CFG_SCRIPT_ENTRY_SIZE * 8,
            self.OTP_CFG_SCRIPT_ADDR,
            self.OTP_CFG_SCRIPT_ENTRY_CNT_MAX,
        )

        # Parse entries skipping start entry
        count = 0
        index = 1
        while index < self.OTP_CFG_SCRIPT_ENTRY_CNT_MAX:
            entry = entries[index]

            # Check for key
            if entry == key:
                if key != 0xFFFFFFFF:
                    logging.info(
                        "OTP key found at offset 0x{:x} with value 0x{:x}".format(
                            index * self.OTP_CFG_SCRIPT_ENTRY_SIZE, entries[index + 1]
                        )
                    )
                count += 1

            # Check for end of script
            if entry == 0xFFFFFFFF:
                if count == 0:
                    logging.info("OTP key not yet in script")
                logging.info(
                    "OTP write offset: 0x{:x}".format(
                        index * self.OTP_CFG_SCRIPT_ENTRY_SIZE
                    )
                )
                return count, (index * self.OTP_CFG_SCRIPT_ENTRY_SIZE)

            # Check for stop command
            if entry == 0x00000000:
                logging.info("OTP is locked")
                return count, -2

            logging.debug("OTP {}: {:x}".format(index, entry))

            # Decode entry and skip data values
            msb = (entry & 0xF0000000) >> 24
            if msb == 0x60:  # BOOTER
                index += 1
            elif msb == 0x70:  # SWD MODE
                index += 1
            elif msb == 0x80:  # UART STX
                index += 1
            elif msb == 0x90:  # SDK ENTRIES
                index += 1
                index += (entry & 0x0000FF00) >> 8
            else:  # REG ENTRIES OR XTAL TRIM
                index += 2

        logging.info("OTP is full")
        return count, -1

    def otp_write(self, key, values, force):
        """Add key and value to the OTP at the first available offset.

        Args:
            key: OTP key to add
            values: array of OTP values to add
            force: add key also if it exists

        Returns:
            result: zero if ok, negative for error
        """
        # Get existing count and write offset
        count, offset = self.otp_read(key)

        # Cannot write when locked or full
        if offset < 0:
            return offset

        # Only write existing keys when forced
        if (count > 0) and not force:
            logging.info(
                "OTP write skipped because key exists, use --force to override"
            )
            return 0

        # Write key with values
        logging.info("OTP write key 0x{:x} with values: {}".format(key, values))
        data = [key] + values
        if not self.otp_write_words(data, offset):
            logging.error("OTP write error")
            return -3

        return 0


class da1470x(da1469x):
    """Derived class for the da1470x devices."""

    QPSPIC_BASE = 0x36000000
    FLASH_READ_ARRAY_BASE = 0x38000000
    FLASH_ARRAY_BASE = 0x38000000

    def __init__(self):
        """Initalizate the da14xxxx parent devices class."""
        da1469x.__init__(self, b"DA1470x")

    def flash_hw_qspi_cs_enable(self):
        """Enable QSPI CS.

        Args:
            None
        """
        self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x10)

    def flash_hw_qspi_cs_disable(self):
        """Disable QSPI CS.

        Args:
            None
        """
        self.link.wr_mem(32, self.QSPIC_CTRLBUS_REG, 0x20)

    def flash_set_automode(self, mode):
        """Set the device in automode.

        Args:
            mode: boolean
        """
        # ctrlmode = self.link.rd_mem(32, self.QSPIC_CTRLMODE_REG, 1)[0]
        if mode:
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, 0xF80000BF)
        else:
            self.link.wr_mem(32, self.QSPIC_CTRLMODE_REG, 0xF80000BE)
        return True


class da1468x(da1468x_da1469x_da1470x):
    """Derived class for the DA1468x devices."""

    QPSPIC_BASE = 0x0C000000
    FLASH_READ_ARRAY_BASE = 0x08000000
    FLASH_ARRAY_BASE = 0x08000000

    def __init__(self, device=None):
        """Initalizate the da14xxxx parent devices class."""
        da1468x_da1469x_da1470x.__init__(self, device)

    def set_qspi_clk(self):
        """Set the QSPI clock.

        Args:
            None
        """
        self.link.wr_mem(16, self.CLK_AMBA_REG, 0x1000)

    def flash_probe(self):
        """Probe the flash device.

        Args:
            None
        """
        # Set the QSPIC clock on
        self.set_qspi_clk()
        return super().flash_probe()

    def flash_program_image(self, fileData, parameters):
        """Program and image in the flash.

        Args:
            fileData: Byte array
            flashid: unused
        """
        if fileData[:2] == b"qQ":
            logging.info("[DA1468x] Program image")
            data = fileData
        else:
            logging.info("[DA1468x] Program binary")
            data = (
                b"qQ\x00\x00\x80\x00"
                + struct.pack(">H", (len(fileData) - 8) & 0xFFFF)
                + fileData[: (0x200 - 8)]
                + fileData[0x200:]
            )

        self.flash_program_data(data, 0x0)
        logging.info("[DA1468x] Program success")
        return 1


class da14681(da1468x):
    """Derived class for the DA14681 devices."""

    def __init__(self, device=None):
        """Initalizate the da14xxxx parent devices class."""
        da1468x_da1469x_da1470x.__init__(self, b"DA14681")


class da14683(da1468x):
    """Derived class for the DA14683 devices."""

    def __init__(self, device=None):
        """Initalizate the da14xxxx parent devices class."""
        da1468x_da1469x_da1470x.__init__(self, b"DA14683")
