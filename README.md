# ezFlashCLI

[![Build Status](https://travis-ci.org/ezflash/ezFlashCLI.svg?branch=master)](https://travis-ci.org/ezflash/ezFlashCLI)
[![Documentation Status](https://readthedocs.org/projects/ezflashcli/badge/?version=latest)](https://ezflashcli.readthedocs.io/en/latest/?badge=latest)

Command line tools to flash Dialog Smartbond™ device family. 

The tool relies on Segger J-Link™ library to control the Smartbond SWD interface. The J-Link probe is available on all Smartbond development kits. 

For more details, please look at our [Documentation](https://ezflashcli.readthedocs.io/)

## Supported platforms

* macOS
* windows 10

## Supported devices

* DA14531
* DA1469x:
    * DA14691
    * DA14695
    * DA14697
    * DA14699

## Installation

```
> pip install ezFlashCLI
```
## Example

### erase Flash
```
> ezFlashCLI erase_flash
```

### Read Flash
```
> ezFlashCLI read_flash 0x0 128
```
### Program Flash
```
> ezFlashCLI write_image <path to bin file>
```   
The tool will automatically make the bin file bootable if needed



