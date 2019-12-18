# ezFlashCLI

Command line tools to flash Dialog Smartbond™ device family. 

The tool relies on Segger J-Link™ library to control the Smartbond SWD interface. The J-Link probe is available on all Smartbond development kits. 

## Supported devices

* DA14531
* DA1469x:
    * DA14691
    * DA14695
    * DA14697
    * DA14699

## Installation

> pip install ezFlashCLI



## Example

### erase Flash
> ezFlashCLI erase_flash

### Read Flash
> ezFlashCLI read_flash 0x0 128

### Program Flash
> ezFlashCLI write_image <path to bin file>
   
The tool will automatically make it bootable if needed



