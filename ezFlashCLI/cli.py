#!/usr/bin/env python3
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


__version__ = "0.0.13"


import logging 
import sys
from pathlib import Path

from ezFlashCLI.ezFlash.pyjlink import *
from ezFlashCLI.ezFlash.smartbond.smartbondDevices import *

import argparse


class ezFlashCLI():
    
    flashid = None

    def __init__(self):

        # parse the command line arguments
        self.argument_parser()

        

        # load the flash database
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'flash_database.json')) as json_file:
            self.flash_db = json.load(json_file)

            json_file.close()
        

        # set the verbosity
        if self.args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            

        logging.info("{} v{}".format(self.__class__.__name__,__version__))
        logging.info("By using the program you accept the SEGGER J-link™ license")

        #list the jlink interfaces
        if self.args.version:
            logging.info("{}".format(__version__))
            sys.exit(0)

        #using JLINK for operations
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



            if len(self.devicelist) > 1 and not self.args.jlink and self.args.operation != 'list':
                logging.error("JLink interface must be selected using -j option")
                self.display_jlink_devices()
                sys.exit(1)

        #list the jlink interfaces
        if self.args.operation == 'list':
            self.display_jlink_devices()

        elif self.args.operation == 'probe':
            self.probeDevice()

            logging.info("Smartbond chip: {}".format(SMARTBOND_PRETTY_IDENTIFIER[self.deviceType]))



            self.probeFlash()
            logging.info('Flash information:')
            if  not self.flashid is None:
                logging.info("  - Device Id: {}".format(self.flashid['name']))
            else:
                logging.info("  - Device Id: {}".format("Not Found"))

            # # check the flash header
            # if self.flashid:
            #     print("  - Product header programmed: {}".format(self.flashProductHeaderIsCorrect()))


        elif self.args.operation == 'go':
            self.probeDevice()
            logging.info("Smartbond chip: {}".format(SMARTBOND_PRETTY_IDENTIFIER[self.deviceType]))
            self.go()
            
        elif self.args.operation == 'erase_flash':
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

        elif self.args.operation == 'read_flash':

            self.probeDevice()
            self.probeFlash()
            self.da.flash_configure_controller(self.flashid)
            data = self.da.read_flash(self.args.addr,self.args.length)
            current_address = self.args.addr
            line_width = 16
            while len(data):
                dataByes = ' '.join('{:02x}'.format(x) for x in data[:line_width])
                logging.info('{:08X}: {}'.format(current_address,dataByes))
                data = data[line_width:]
                current_address += line_width


        elif self.args.operation == 'write_flash':

            try:
                fp  = open(self.args.filename,'rb')
            except:
                logging.error("Failed to open {}".format(self.args.filename))
                sys.exit(1)


            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)

            self.da =  eval(self.deviceType)()
            self.da.connect(self.args.jlink)
            fileData = fp.read()
            logging.info('Program file size {}'.format(len(fileData)))
            fp.close()

            print("0x{:x}".format(self.args.addr, len(fileData)))
            if self.da.flash_program_data(fileData,self.args.addr):
                logging.info("Flash write success")
            else:
                logging.error("Flash write failed")
                sys.exit(1)

        elif self.args.operation ==  'image_flash':

            try:
                fp  = open(self.args.filename,'rb')
            except:
                logging.error("Failed to open {}".format(self.args.filename))
                sys.exit(1)

            self.probeDevice()
            self.probeFlash()
            if self.flashid is None:
                logging.info("Flash chip not found")
                sys.exit(1)

            self.da =  eval(self.deviceType)()
            self.da.connect(self.args.jlink)
            fileData = fp.read()
            fp.close()

            if self.da.flash_program_image(fileData,self.flashid):
                logging.info("Flash image success")
            else:
                logging.error("Flash image failed")
                sys.exit(1)

        elif self.args.operation == 'product_header_check':
            ''' Performs sanity check on the product header
                it will verify the content is consistent with the probed flash

                Args:
                    None
                    
                Returns:
                    True if the Header is consistent with the attached flash

            '''

            self.probeDevice()
            self.probeFlash()
            da =  eval(self.deviceType)()

            productHeaderCalculated = self.calculateProductHeader()

            self.da.connect(self.args.jlink)
            self.da.flash_configure_controller(self.flashid)
            productHeader = self.da.read_product_header()



            if productHeaderCalculated == productHeader:
                logging.info("Product header OK")
            else:
                logging.error("Product header mismatch")

        else:
            self.parser.print_help(sys.stderr)
        sys.exit(0)

    def go(self):
        self.link.connect(self.args.jlink)
        self.link.reset()
        self.link.go()

    def probeDevice(self):
        try:
            self.deviceType = SMARTBOND_IDENTIFIER[self.link.connect(self.args.jlink)]
            self.link.close()

        except Exception as inst:
            logging.error("Device not responding: {}".format(inst))
            sys.exit(1)
    
    def probeFlash(self):
        # look for attached flash
        try:
            self.da =  eval(self.deviceType)()
            self.da.connect(self.args.jlink)
            dev = self.da.flash_probe()
            self.flashid = self.da.get_flash(dev,self.flash_db)
            return self.flashid
        except Exception as inst:
            logging.error("No Flash detected {}".format(inst))

        return None
        

    def calculateProductHeader(self):
        return(self.da.make_product_header(self.flashid['flash_burstcmda_reg_value'], \
            self.flashid['flash_burstcmdb_reg_value'], \
            self.flashid['flash_write_config_command'] ))

    def display_jlink_devices(self):
        logging.info('JLink devices:')
        for device in self.devicelist:
            if device.SerialNumber != 0:
                logging.info("  - {}".format(device.SerialNumber))

    def argument_parser(self):
        """ Initializes the arguments passed from the command line 
        
        """    
        self.parser = argparse.ArgumentParser(description='Smartbond tool v%s - Dialog Smartbond devices flash management tool' % __version__,prog='ezFlashCLI')


        self.parser.add_argument('-c','--chip', 
                        help='Smartbond chip version',
                        choices=['auto','DA14531', 'DA14580', 'DA14585', 'DA14681',  'DA14683', 'DA1469x' ],
                        default=os.environ.get('SMARTBOND_CHIP', 'auto'))

        self.parser.add_argument('-p','--port', 
                        help='Serial port device',
                        default=os.environ.get('SMARTBOND_PORT', None))

        self.parser.add_argument('-j','--jlink', 
                        help='JLink device identifier',
                        default=os.environ.get('SMARTBOND_JLINK_ID', None))

        self.parser.add_argument("-v","--verbose", help="increase verbosity",action='store_true')
        self.parser.add_argument("--version", help="return version number",action='store_true')

        self.subparsers = self.parser.add_subparsers(dest='operation',help='Run  {command} -h for additional help')

        self.subparsers.add_parser('list',help="list JLink interfaces")
        self.subparsers.add_parser('probe',help='Perform Chip detection and its associated flash')

        self.subparsers.add_parser('go',help='Reset and start the CPU')
        self.subparsers.add_parser('erase_flash',help='Perform Chip Erase on SPI/QSPI flash')

        flash_parser = self.subparsers.add_parser('write_flash',help='Write binary file at specified address')

        flash_parser.add_argument('addr',type=lambda x: int(x,0), help='Address in the flash area')
        flash_parser.add_argument('filename', help='Binary file path')

        flash_parser = self.subparsers.add_parser('read_flash',help='read data at specified address and length')

        flash_parser.add_argument('addr',type=lambda x: int(x,0), help='Address in the flash area')
        flash_parser.add_argument('length',type=lambda x: int(x,0), help='number of bytes to read')

        flash_parser = self.subparsers.add_parser('image_flash',help='Write the flash binary')
        flash_parser.add_argument('filename', help='Binary file path')

        flash_parser = self.subparsers.add_parser('product_header_check',help='Read the product header and check')


        self.args = self.parser.parse_args()


if __name__ == "__main__":
    
    ezFlashCLI()
    
    pass
