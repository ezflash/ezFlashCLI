import logging
import serial
import argparse
import sys

from ezFlashCLI.cli import __version__



BAUDRATE=115200
TIMEOUT=5

class da1469xSerialLoader(object):

    def __init__(self):
        
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

        self.sp = serial.Serial(self.args.port,BAUDRATE,timeout=TIMEOUT)

        self.load()

    def load(self):

        try:
            with open(self.args.application,'rb') as fp:

                data = fp.read()
                size = len(data)
        except:
            self.logger.error("Failed to read application")
            return(1)

        self.logger.debug('Loading App size {}'.format(size))

        crc = 0
        for d in data:
            crc ^= d


        if not self.get_stx():
            self.logger.debug("Press Reset")
            if not self.get_stx():
                self.logger.info("Failed to detect Smartbond device")
                return
        
        # self.sp.write(b'\x01') # send SOH
        if size< 2**16:
            self.sp.write(b'\x01' + size.to_bytes(2,byteorder='little'))
        else:
            self.sp.write(b'\x01\x00\x00' + size.to_bytes(3,byteorder='little'))

        if self.sp.read(1) != b'\x06':
            self.logger.error("Failed to get length ACK")
            return
        self.sp.write(data)

        read_crc = int.from_bytes(self.sp.read(1),byteorder='little')
        if read_crc != crc:
            self.logger.debug("Failed to get data ACK {} {}".format(read_crc,crc))
            return

        self.sp.write(b'\x06')
        self.logger.info("Loading success")



    def get_stx(self):
        if c:=self.sp.read(1) == b'\x02':
            return(True)

        return(False)



    def argument_parser(self):
        """ Initializes the arguments passed from the command line 
        
        """    


        # parser.add_argument('-c','--chip', 
        #                 help='Smartbond chip version',
        #                 choices=['auto','DA14531', 'DA14580', 'DA14585', 'DA14681',  'DA14683', 'DA1469x' ],
        #                 default=os.environ.get('SMARTBOND_CHIP', 'auto'))

        # parser.add_argument('-p','--port', 
        #                 help='Serial port device',
        #                 default=os.environ.get('SMARTBOND_PORT', None))

        # parser.add_argument('-j','--jlink', 
        #                 help='JLink device identifier',
        #                 default=os.environ.get('SMARTBOND_JLINK_ID', None))
        self.parser = argparse.ArgumentParser(description='Smartbond Serial loader v%s' % __version__,prog='ezSerialCLI')

        self.parser.add_argument('port',nargs='?',help='Serial port name',default=None)
        self.parser.add_argument('application',nargs='?',help='Application to load',default=None)

        self.parser.add_argument("-v","--verbose", help="increase verbosity",action='store_true')

        
        self.parser.add_argument("--version", help="return version number",action='store_true')


        self.args = self.parser.parse_args()



if __name__ == "__main__":

    
    da1469xSerialLoader()
    

