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


import sys,os


# probably need to do that only when frozen
# sys.path.insert(0,os.path.join(os.path.dirname(__file__)))

from ..pyjlink import *

import json
import logging
import time
import binascii
import struct

SPI_FLASH_PAGE_SIZE   = 256
SPI_FLASH_SECTOR_SIZE = 4096
_69x_DEFAULT_IMAGE_ADDRESS = 0x2000
_69x_DEFAULT_IMAGE_OFFSET  = 0x400

class HW_QSPI_BREAK_SEQ_SIZE(IntEnum):
        SIZE_1B = 0,
        SIZE_2B = 1 

class HW_QSPI_BUS_MODE(IntEnum):
        SINGLE = 0,   # Bus mode in single mode
        DUAL   = 1,   # Bus mode in dual mode
        QUAD   = 2    # Bus mode in quad mode


class HW_QSPI_COMMON_CMD(IntEnum):
    WRITE_STATUS_REGISTER =      0x01,
    PAGE_PROGRAM          =      0x02,
    READ_DATA             =      0x03,
    WRITE_DISABLE         =      0x04,
    READ_STATUS_REGISTER  =      0x05,
    WRITE_ENABLE          =      0x06,
    SECTOR_ERASE          =      0x20,
    QUAD_PAGE_PROGRAM     =      0x32,
    QPI_PAGE_PROGRAM      =      0x02,
    BLOCK_ERASE           =      0x52,
    CHIP_ERASE            =      0xC7,
    FAST_READ_QUAD        =      0xEB,
    READ_JEDEC_ID         =      0x9F,
    EXIT_CONTINUOUS_MODE  =      0xFF,
    RELEASE_POWER_DOWN    =      0xAB,
    ENTER_POWER_DOWN      =      0xB9,
    FAST_READ_QUAD_4B     =      0xEC,
    SECTOR_ERASE_4B       =      0x21,
    QUAD_PAGE_PROGRAM_4B  =      0x34,
    ENTER_QPI_MODE        =      0x38,    # Requires single mode for the command entry!
    EXIT_QPI_MODE         =      0xFF     # Requires quad mode for the command entry!


SMARTBOND_IDENTIFIER = {
    "[50, 53, 50, 50]"    : "da1469x",
    "[54, 56, 48, 0, 65]" : "da14681",
    "[54, 56, 48, 0, 66]" : "da14683",
    "[53, 56, 53, 1, 65]" : "da14585",
    "[53, 56, 48, 1, 65]" : "da14580",
    "[50, 0, 50, 0, 54]"  : "da14531"
}


SMARTBOND_PRETTY_IDENTIFIER = {
    "da1469x" : "DA1469x",
    "da14681" : "DA14680/DA14681",
    "da14683" : "DA14682/DA14683",
    "da14585" : "DA14585/DA14586",
    "da14580" : "DA14580",
    "da14531" : "DA14531"
}


class da14xxx():
    """ Handler for the Smartbond devices Flash memory

    """
    CLK_AMBA_REG        = 0x50000000

    def __init__(self,device=None):

        self.flash_address_size = 3
        self.polling_interval = 0.01
        self.wait_timeout = 30

        self.link = pyjlink()
        if device:
            logging.debug("Set device to {}".format(device))
            self.link.Device = device
        self.link.init()

    def connect(self,id):

        id = self.link.connect(id)

        if not len(id):
            raise Exception('Device not found')
        return id



    def get_flash(self,flashId,flash_db):
        """ Get the flash device id and return its name

            Args:
                flashId: manufacturer,deviceid,device denisity
                i.e: 0xC22536 for P25Q80H

            Returns:
                Flash configuration

        """

        for flash in flash_db['flash_configurations']:

            if flashId == (int(flash['flash_manufacturer'],16),int(flash['flash_device_type'],16),int(flash['flash_density'],16)):
                return flash

        return None


    def flash_configure_controller(self,flashid):
        """ set the controller in Continuous mode according 
           flash configuration parmaters

            Notes:
                Requires the flash device to be successfully probed
                
        """
        pass


class da1453x_da1458x(da14xxx):

    FLASH_ARRAY_BASE    = 0x16000000


    SET_FREEZE_REG      = 0x50003300
    PAD_LATCH_REG       = 0x5000030C
    SYS_CTRL_REG        = 0x50000012
    HWR_CTRL_REG        = 0x50000300
    CLK_PER_REG         = 0x50000004

    SPI_CTRL_REG        = 0x50001200
    SPI_CONFIG_REG      = 0x50001204
    SPI_CLOCK_REG       = 0x50001208
    SPI_FIFO_CONFIG_REG = 0x5000120C
    SPI_FIFO_STATUS_REG = 0x50001218
    SPI_FIFO_READ_REG   = 0x5000121C
    SPI_FIFO_WRITE_REG  = 0x50001220
    SPI_CS_CONFIG_REG   = 0x50001224

    P0_DATA_REG         = 0x50003000
    P00_MODE_REG        = 0x50003006
    P00_MODE_REG_RESET  = 0x00000200
    

    OUTPUT              = 0x300
    INPUT               = 0
    # Word Size 8 bits
    SPI_MODE_8BIT       = 0
    # Word Size 16 bits
    SPI_MODE_16BIT      = 1
    # Word Size 32 bits
    SPI_MODE_32BIT      = 2

    def __init__(self, device=None):
        da14xxx.__init__(self,device)

    def shift16(self,a):
        shift = 0
        while not (a & 0x1):
           shift += 1
           a = (a >> 1) 
        return shift

    def SetWord16(self,addr,data):
        self.link.wr_mem(16,addr,data)

    def SetBits16(self, addr, bitfield_mask,data):
        reg = self.link.rd_mem(16,addr,1)[0]
        reg = (reg & (~ bitfield_mask)) & 0xFFFF
        wr_data = reg  | (data << (self.shift16(bitfield_mask)))
        self.link.wr_mem(16,addr,wr_data)

    def GPIO_SetPinFunction(self,port,pin,mode,function) :
        
        data_reg = self.P0_DATA_REG + (port << 5)
        mode_reg = data_reg + 0x6 + (pin << 1)
        self.link.wr_mem(16,mode_reg,mode| function)
   
    def GPIO_SetActive(self, port, pin):
        data_reg = self.P0_DATA_REG + (port << 5)
        set_data_reg = data_reg + 2
        self.link.wr_mem(16,set_data_reg, 1 << pin)
    

    def GPIO_SetInactive(self, port, pin):
        data_reg = self.P0_DATA_REG + (port << 5)
        set_data_reg = data_reg + 4
        self.link.wr_mem(16,set_data_reg, 1 << pin)

    def read_flash(self, address, length):
        read_data = []

        self.flash_init()

        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_DATA)
        self.spi_access8(address & 0xFF)
        self.spi_access8((address >> 8) & 0xFF)
        self.spi_access8((address >> 16) & 0xFF)
        while length :
            read_data.append(self.spi_access8(0xFF))
            length -= 1
            
        self.spi_cs_high()

        return(read_data)

    def flash_probe(self):
        """ Probe the flash device

            Args:
                None
        """

        #reset and halt the cpu
        self.link.reset()

        #init the flash
        self.flash_init()

        # read JEADEC id
        self.spi_set_bitmode(self.SPI_MODE_8BIT)
        self.spi_cs_low()
        self.spi_access8(HW_QSPI_COMMON_CMD.READ_JEDEC_ID)
        manufacturer =  self.spi_access8(0xFF)
        deviceId = self.spi_access8(0xFF)
        density = self.spi_access8(0xFF)
        self.spi_cs_high()

        return (manufacturer,deviceId,density)


    def flash_erase(self):
        """ execute chip erase

            Args:
                None
        """

        #reset and halt the cpu
        self.link.reset()

        #init the flash
        self.flash_init()

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



    def flash_program_image(self,fileData,address=0x0):
        """ Program image in the flash

            Args:
                fileData: file data
                addresss: start address to program
        """

        if fileData[0] != 0x70 or fileData[1] != 0x50:
            print("Not a bootable image")
            if fileData[3] != 0x7 :
                print("This is not a binary with stack pointer at the beginning",fileData[3] )
                return 0
            else:
                print("append booting data")
                header = b'\x70\x50\x00\x00\x00\x00' + struct.pack('>H',len(fileData))

                data = header + fileData
        else :
            # bootable image
            data = fileData

        self.link.jl.JLINKARM_BeginDownload(c_uint32(0))
        self.link.jl.JLINKARM_WriteMem(self.FLASH_ARRAY_BASE,len(data),c_char_p(data))
        bytes_flashed = self.link.jl.JLINKARM_EndDownload()
        if bytes_flashed < 0:
            logging.error("Download failed with code: @address {}, {}".format(address,bytes_flashed))
            return 0

        #reset and halt the cpu
        self.link.reset()

        return 1

class da14531(da1453x_da1458x):
    
    SPI_PORT            = 0
    SPI_CLK_PIN         = 4
    SPI_CS_PIN          = 1
    SPI_DI_PIN          = 3
    SPI_DO_PIN          = 0


    def __init__(self):
        da1453x_da1458x.__init__(self,b"DA14531")



    def spi_cs_low(self):
        self.SetBits16(self.SPI_CTRL_REG, 0x20, 0) # release reset fifo
        self.SetWord16(self.SPI_CS_CONFIG_REG, 1)


    def spi_cs_high(self):
        self.SetWord16(self.SPI_CS_CONFIG_REG, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x20, 1)  # reset fifo

    def flash_init(self):
        """ Initialize flash controller and make sure the
            Flash device exits low power mode

            Args:
                None
        """
        self.SetWord16(self.CLK_AMBA_REG, 0x00)             # set clocks (hclk and pclk ) 16MHz
        self.SetWord16(self.SET_FREEZE_REG, 0x8)            # stop watch dog
        self.SetBits16(self.PAD_LATCH_REG,    0x1, 1)       # open pads
        self.SetBits16(self.SYS_CTRL_REG, 0x0180, 0x3)      # SWD_DIO = P0_10
        self.SetWord16(self.HWR_CTRL_REG, 1)                # disable HW reset

        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CS_PIN, 0x300, 29) # SPI_CS
        self.GPIO_SetActive(self.SPI_PORT, self.SPI_CS_PIN)
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CLK_PIN, 0x300, 28) # SPI_CLK
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DO_PIN, 0x300, 27) # SPI_D0
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DI_PIN, 0, 26) # SPI_DI

        self.SetBits16(self.CLK_PER_REG, 0x400, 1)
        # Disable SPI / Reset FIFO in SPI Control Register
        self.SetWord16(self.SPI_CTRL_REG, 0x0020) # fifo reset
        # Set SPI Word length
        self.spi_set_bitmode(self.SPI_MODE_8BIT)
        # Set SPI Mode (CPOL, CPHA)
        #spi_set_cp_mode(SPI_CP_MODE_0)
        self.SetBits16(self.SPI_CONFIG_REG, 0x0003, 0) # mode 0
        # Set SPI Master/Slave mode
        self.SetBits16(self.SPI_CONFIG_REG, 0x80, 0) # master mode

        # Set SPI FIFO threshold levels to 0
        self.SetWord16(self.SPI_FIFO_CONFIG_REG, 0)
        # Set SPI clock in async mode (mandatory)
        self.SetBits16(self.SPI_CLOCK_REG, 0x0080, 1)

        # Set SPI master clock speed
        #spi_set_speed(SPI_SPEED_MODE_2MHz)
        self.SetBits16(self.SPI_CLOCK_REG, 0x007F, 7)    # 2MHz
        # Set SPI clock edge capture data
        self.SetBits16(self.SPI_CTRL_REG, 0x0040, 0)  

    def spi_access8(self,dataToSend):
   
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
        while ((self.link.rd_mem(16,self.SPI_FIFO_STATUS_REG,1)[0] & 0x1000) != 0):
            pass

        dataRead = self.link.rd_mem(16,self.SPI_FIFO_READ_REG,1)[0] & 0xFF

        # Wait until transaction is finished and SPI is not busy
        while ((self.link.rd_mem(16,self.SPI_FIFO_STATUS_REG,1)[0] & 0x8000) != 0):
            pass
        return dataRead
    

    def spi_set_bitmode(self, spi_wsz):


        if spi_wsz == self.SPI_MODE_16BIT:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7c, 15)
        elif spi_wsz == self.SPI_MODE_32BIT:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7c, 31)
        else:
            self.SetBits16(self.SPI_CONFIG_REG, 0x7c, 7)




    def release_reset(self):
        """ 
            On 531 the reset pin is shared with the default flash MOSI pin.
            The function restore the pin into reset mode

        """
        self.link.wr_mem(16,self.HWR_CTRL_REG,0x0)
        self.link.wr_mem(16,self.P00_MODE_REG,self.P00_MODE_REG_RESET)


    def flash_program_image(self,fileData,address=0x0):
        result = super().flash_program_image(fileData,address)
        self.release_reset()
        return(result)

    def read_flash(self, address, length):
        read_data = super().read_flash(address, length)
        self.release_reset()
        return(read_data)



class da14585(da1453x_da1458x):

    SPI_PORT            = 0
    SPI_CLK_PIN         = 0
    SPI_CS_PIN          = 3
    SPI_DI_PIN          = 5
    SPI_DO_PIN          = 6

    SPI_CTRL_REG1       = 0x50001208
    SPI_RX_TX_REG0      = 0x50001202
    SPI_CLEAR_INT       = 0x50001206


    def __init__(self,device=None):
        da1453x_da1458x.__init__(self, b'DA14585')

    def spi_set_bitmode(self, spi_wsz):

        # force to 8 bits whatever the size is 
        self.SetBits16(self.SPI_CTRL_REG, 0x1, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x180, 0)
        self.SetBits16(self.SPI_CTRL_REG, 0x1, 1)

    def spi_cs_low(self):
        self.GPIO_SetInactive(self.SPI_PORT,self.SPI_CS_PIN)


    def spi_cs_high(self):
        self.GPIO_SetActive(self.SPI_PORT,self.SPI_CS_PIN)


    def spi_access8(self, dataToSend):

        # Set FIFO Bidirectional mode
        self.SetBits16(self.SPI_CTRL_REG1, 0x3, 2)

        # Write (low part of) dataToSend
        self.SetWord16(self.SPI_RX_TX_REG0, dataToSend)

        # Polling to wait for spi transmission
        while ((self.link.rd_mem(16,self.SPI_CTRL_REG,1)[0] & 0x2000) == 0):
            pass

        # Clear pending flag
        self.SetWord16(self.SPI_CLEAR_INT, 0x1)

        # Return data read from spi slave
        return self.link.rd_mem(16,self.SPI_RX_TX_REG0,1)[0]

    def flash_init(self):
        """ Initialize flash controller and make sure the
            Flash device exits low power mode

            Args:
                None
        """
        self.SetWord16(self.CLK_AMBA_REG, 0x00)             # set clocks (hclk and pclk ) 16MHz
        self.SetWord16(self.SET_FREEZE_REG, 0x8)            # stop watch dog
        self.SetBits16(self.SYS_CTRL_REG, 0x0180, 0x3)      # SWD_DIO = P0_10

        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CS_PIN, 0x300, 8) # SPI_CS
        self.GPIO_SetActive(self.SPI_PORT, self.SPI_CS_PIN)
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_CLK_PIN, 0x300, 7) # SPI_CLK
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DO_PIN, 0x300, 6) # SPI_D0
        self.GPIO_SetPinFunction(self.SPI_PORT, self.SPI_DI_PIN, 0, 5) # SPI_DI

        self.SetBits16(self.CLK_PER_REG, 0x800, 1)

        # Set SPI Word length
        self.spi_set_bitmode(self.SPI_MODE_8BIT)


class da1468x_da1469x(da14xxx):
    """
        Base class for the 68x,69x family
    """
    FLASH_READ_ARRAY_BASE    = 0x36000000
    FLASH_ARRAY_BASE         = 0x36000000

    QSPIC_CTRLBUS_REG   = 0x00  # Control register 0
    QSPIC_CTRLMODE_REG  = 0x04  # Control register 1
    QSPIC_RECVDATA_REG  = 0x08  # Data register (TX and RX)
    QSPIC_BURSTCMDA_REG = 0x0C  # Status register
    QSPIC_BURSTCMDB_REG = 0x10  # Clock prescale register
    QSPIC_WRITEDATA_REG = 0x18  # write data registers in manual mode
    QSPIC_READDATA_REG  = 0x1C  # read data registers in manual mode
    
    def __init__(self,device=None):

        da14xxx.__init__(self,device)

        self.QSPIC_CTRLBUS_REG   += self.QPSPIC_BASE
        self.QSPIC_CTRLMODE_REG  += self.QPSPIC_BASE
        self.QSPIC_RECVDATA_REG  += self.QPSPIC_BASE
        self.QSPIC_BURSTCMDA_REG += self.QPSPIC_BASE
        self.QSPIC_BURSTCMDB_REG += self.QPSPIC_BASE
        self.QSPIC_WRITEDATA_REG += self.QPSPIC_BASE
        self.QSPIC_READDATA_REG  += self.QPSPIC_BASE


        self.myaddress = 0x0

    def read_flash(self, address, length):
        return(self.link.rd_mem(8,self.FLASH_READ_ARRAY_BASE + address, length))

    def flash_hw_qspi_cs_enable(self):
        """ Enable QSPI CS
            Args:
                None
        """
        self.link.wr_mem(32,self.QSPIC_CTRLBUS_REG, 0x8)

    def flash_hw_qspi_cs_disable(self):
        """ Disable QSPI CS
            Args:
                None
        """
        self.link.wr_mem(32,self.QSPIC_CTRLBUS_REG, 0x10)




    def flash_set_automode(self,mode):
        """ Set the device in automode
            Args:
                mode: boolean
        """

        ctrlmode = self.link.rd_mem(32,self.QSPIC_CTRLMODE_REG,1)[0]
        if mode : 
            self.link.wr_mem(32,self.QSPIC_CTRLMODE_REG,ctrlmode | 0x1)
        else :
            self.link.wr_mem(32,self.QSPIC_CTRLMODE_REG,ctrlmode & ~(0x1))
        return True



    def flash_set_busmode(self,mode) :
        """ Set the QSPI controller bus mode
            Args:
                mode : HW_QSPI_BUS_MODE type

            Returns:
                True: success
                False: error
        """

        if mode == HW_QSPI_BUS_MODE.SINGLE:
            # set single mode
            self.link.wr_mem(32,self.QSPIC_CTRLBUS_REG,0x1)
            # read the ctrlmode reg
            ctrlmode = self.link.rd_mem(32,self.QSPIC_CTRLMODE_REG,1)[0]

            # writte the data line mode
            self.link.wr_mem(32,self.QSPIC_CTRLMODE_REG,ctrlmode | 0x3C)


        elif mode == HW_QSPI_BUS_MODE.DUAL:
            raise Exception("unsupported DUAL SPI mode")

        else :
            # set quad mode
            self.link.wr_mem(32,self.QSPIC_CTRLBUS_REG,0x4)

            # read the ctrlmode reg
            ctrlmode = self.link.rd_mem(32,self.QSPIC_CTRLMODE_REG,1)[0]

            # writte the data line mode
            self.link.wr_mem(32,self.QSPIC_CTRLMODE_REG, ctrlmode & ~(0xC))

        return True

    def flash_hw_qspi_write8(self,data):
        """ write a byte on the qspi interface
            Args:
                data: byte
        """
        self.link.wr_mem(8,self.QSPIC_WRITEDATA_REG,data)

    def flash_hw_qspi_read8(self):
        """ Read a byte on the qspi interface
            Args:
                None
            Return:

        """
        return(self.link.rd_mem(8,self.QSPIC_READDATA_REG,1)[0])



    def whileFlashBusy(self):
        """ Block while the flash is busy
            Args:
                None
        """
        wait_time = 0

        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.READ_STATUS_REGISTER)
        while True:

            status = self.flash_hw_qspi_read8()
            if not (status & 0x1) :
                self.flash_hw_qspi_cs_disable()
                return True
            if wait_time > self.wait_timeout:
                return False

            time.sleep(self.polling_interval)
            wait_time += self.polling_interval


    def flash_erase(self) :
        """ erase the flash content
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

        self.whileFlashBusy() # wait for the operation to be over


        # set automode
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)
       

        return True

    def flash_sector_erase(self,address):
        """ Erase sector()

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

        for data in address.to_bytes(self.flash_address_size,'big'):
            self.flash_hw_qspi_write8(data)

        self.flash_hw_qspi_cs_disable()

        self.whileFlashBusy()

        # set automode
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)
       

    def flash_page_program(self,address,data_array):
        """ Program a page (up to 256 bytes)

            Args:
                address: Address (int)
                data: bytes
        """
        if not len(data_array):
            raise Exception('data is empty')
        
        if type(data_array) != type(bytes()):
            print(type(data),type(bytes))
            raise Exception('data should be byte it is'.format( type(data)))

        
        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.SINGLE)

        
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        
        
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.PAGE_PROGRAM)
        
        for data in address.to_bytes(self.flash_address_size,'big'):
            self.flash_hw_qspi_write8(data)
        

        for data in data_array:
            self.flash_hw_qspi_write8(data)
        
        self.flash_hw_qspi_cs_disable()
        
        self.whileFlashBusy()

        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

        


    def flash_reset_continuous_mode(self,breakSize) :
        """ Reset the flash 
            Args:
                breakSize: HW_QSPI_BREAK_SEQ_SIZE
        """
        self.flash_hw_qspi_cs_enable()

        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.EXIT_CONTINUOUS_MODE)
        if breakSize == HW_QSPI_BREAK_SEQ_SIZE.SIZE_2B:
            self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.EXIT_CONTINUOUS_MODE)
        
        self.flash_hw_qspi_cs_disable()


    def flash_reset(self) :
        """ Reset the flash 
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
        """ Initiallize QSPI controller and make sure the
            
            Flash device exits low power mode

            Args:
                None
        """

        self.flash_set_automode(False)

        self.flash_reset()

        self.flash_set_automode(True)

    def flash_probe(self):
        """ Probe the flash device JEDEC identifier

            Args:
                None

            Returns:
                Tuple (Manufacturer id, devive type, device density)
        """

        #reset and halt the cpu
        self.link.reset()

        #init the flash
        self.flash_init()

        #disable automode
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

        return (manufacturer,deviceId,density)

    def flash_configure_controller(self,flashid):
        """ set the controller in Continuous mode according 
           flash configuration parmaters

            Notes:
                Requires the flash device to be successfully probed
                
        """
        self.flash_set_automode(False)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)

        # issue a write enable
        self.flash_hw_qspi_cs_enable()
        self.flash_hw_qspi_write8(HW_QSPI_COMMON_CMD.WRITE_ENABLE)
        self.flash_hw_qspi_cs_disable()

        #issue config sequence
        configCommand = flashid['flash_write_config_command'].split(' ')

        self.flash_hw_qspi_cs_enable()

        for cmd in configCommand[:-1]: # the last one is a termation character
            self.flash_hw_qspi_write8(int(cmd[2:],16))

        self.flash_hw_qspi_cs_disable()

        self.link.wr_mem(32,self.QSPIC_BURSTCMDA_REG,int(flashid['flash_burstcmda_reg_value'][2:],16))
        self.link.wr_mem(32,self.QSPIC_BURSTCMDB_REG,int(flashid['flash_burstcmdb_reg_value'][2:],16))
        
        self.link.rd_mem(32,self.QSPIC_BURSTCMDA_REG,1)
        self.link.rd_mem(32,self.QSPIC_BURSTCMDB_REG,1)
        self.flash_set_busmode(HW_QSPI_BUS_MODE.QUAD)
        self.flash_set_automode(True)

    def flash_program_data(self,my_data_array,address= 0x80000000):
        self.link.jl.JLINKARM_BeginDownload(c_uint32(0))
        self.link.jl.JLINKARM_WriteMem(self.FLASH_ARRAY_BASE + address,len(my_data_array),c_char_p(my_data_array))
        bytes_flashed = self.link.jl.JLINKARM_EndDownload()
        if bytes_flashed < 0:
            logging.error("Download failed with code: @{:x} {}".format(self.FLASH_ARRAY_BASE,bytes_flashed))
            sys.exit(bytes_flashed)
        return 1

class da1469x(da1468x_da1469x):
    QPSPIC_BASE         = 0x38000000
    PRODUCT_HEADER_SIZE = 0x1000
    IMG_IVT_OFFSET      = 0x400

    def __init__(self,):
        da1468x_da1469x.__init__(self,b'DA1469x')

    
    def make_image_header(self):
        buff = b''
        buff += struct.pack(">2c", b'Q', b'q')
        for i in range(7):
            buff += struct.pack("<I", 0x0)
        buff += struct.pack("<I", self.IMG_IVT_OFFSET)
        buff += struct.pack("<H",0x22AA)
        buff += struct.pack("<H", 0x0)
        buff += struct.pack("<H",0x44AA)
        buff += struct.pack("<H", 0x0)
    
        return(buff)

    def make_product_header(self, \
                            flash_burstcmda_reg_value, \
                            flash_burstcmdb_reg_value, \
                            flash_write_config_command, \
                            active_fw_image_address = 0x2000, \
                            update_fw_image_address = 0x2000):

        configCommand = flash_write_config_command.split(' ')
        buff = b''
        buff += struct.pack(">2c", b'P', b'p')
        buff += struct.pack("<2I", int(active_fw_image_address), int(update_fw_image_address))
        buff += struct.pack("<2I", int(flash_burstcmda_reg_value[2:],16),int(flash_burstcmdb_reg_value[2:],16))
        buff += struct.pack(">H", 0xAA11)
        buff += struct.pack("H", len(configCommand))
        for cmd in configCommand: 
            buff += struct.pack('<B', int(cmd, 16))
        buff += struct.pack("<H", binascii.crc_hqx(buff, 0xFFFF))
        buff += b'\xFF' * (self.PRODUCT_HEADER_SIZE - len(buff))
        return buff

    def read_product_header(self):
        dataArray = self.link.rd_mem(8,self.FLASH_READ_ARRAY_BASE,self.PRODUCT_HEADER_SIZE)

        product_header = b''
        for data in dataArray:
            product_header += struct.pack('<B',data)

        return(product_header)

    def flash_program_image(self,fileData,flashid):
        if fileData[:2] == b"Pp":
            logging.info("[DA1469x] Program image")   
            self.flash_program_data(fileData,0x0)
        else:
            if fileData[:2] != b"Qq":
                logging.info("[DA1469x] Add image header")
                ih = self.make_image_header()
                ih += b'\xFF'*(_69x_DEFAULT_IMAGE_OFFSET - len(ih))
                fileData = ih + fileData

            logging.info("[DA1469x] Program bin")    
            self.flash_program_data(fileData,_69x_DEFAULT_IMAGE_ADDRESS)

            logging.info("[DA1469x] Program product header")    
            ph = self.make_product_header(flashid['flash_burstcmda_reg_value'], \
                flashid['flash_burstcmdb_reg_value'], \
                flashid['flash_write_config_command'],
                active_fw_image_address=_69x_DEFAULT_IMAGE_ADDRESS,
                update_fw_image_address=_69x_DEFAULT_IMAGE_ADDRESS)
            self.flash_program_data(ph,0x0)
            self.flash_program_data(ph,0x1000)
        logging.info("[DA1469x] Program success")    
        return 1


class da1468x(da1468x_da1469x):
    QPSPIC_BASE              = 0x0c000000
    FLASH_READ_ARRAY_BASE    = 0x08000000
    FLASH_ARRAY_BASE         = 0x00000000


    def __init__(self,device=None):
        da1468x_da1469x.__init__(self,device)

    def set_qspi_clk(self):
        self.link.wr_mem(16,self.CLK_AMBA_REG,0x1000)


    def flash_probe(self):
        """ Probe the flash device

            Args:
                None
        """
        # Set the QSPIC clock on
        self.set_qspi_clk()
        return(super().flash_probe())
 
    def flash_program_image(self,fileData,flashid):
        if fileData[:2] == b"qQ":
            logging.info("[DA1468x] Program image")   
        else:
            logging.info("[DA1468x] Program binary")   
            data = b"qQ\x00\x00\x00\x00\x00\x00" + fileData[:192] + fileData[200:]

        self.flash_program_data(data,0x0)
        logging.info("[DA1468x] Program success")
        return 1

class da14681(da1468x):
    def __init__(self,device=None):
        da1468x_da1469x.__init__(self, b'DA14681')
class da14683(da1468x):
    def __init__(self,device=None):
        da1468x_da1469x.__init__(self, b'DA14683')
       
