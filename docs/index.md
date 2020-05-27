# ezFlashCLI

[![Build Status](https://travis-ci.org/ezflash/ezFlashCLI.svg?branch=master)](https://travis-ci.org/ezflash/ezFlashCLI)
[![Documentation Status](https://readthedocs.org/projects/ezflashcli/badge/?version=latest)](https://ezflashcli.readthedocs.io/en/latest/?badge=latest)

Command line tools to manage flash devices connected to the Dialog Smartbond™ device family.

The tool relies on Segger J-Link™ library to control the Smartbond SWD interface. The J-Link probe is available on all Smartbond development kits.

## Supported platforms

* macOS
* windows 10

## Supported devices

* DA14531

* DA1468x:
  * DA14680
  * DA14681
  * DA14682
  * DA14683

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
> ezFlashCLI image_flash <path to bin file>
```

The tool will automatically make the bin file bootable if needed
