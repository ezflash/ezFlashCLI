# ezFlashCLI

[![Build Status](https://travis-ci.org/ezflash/ezFlashCLI.svg?branch=main)](https://travis-ci.org/ezflash/ezFlashCLI)
[![Documentation Status](https://readthedocs.org/projects/ezflashcli/badge/?version=latest)](https://ezflashcli.readthedocs.io/en/latest/?badge=latest)

Command line tools to manage flash devices connected to the Dialog Smartbond™ device family.

The tool relies on Segger J-Link™ library to control the Smartbond SWD interface. The J-Link probe is available on all Smartbond development kits.

## Supported platforms

* macOS
* Windows 10
* Linux (tested on ubuntu 20.04LTS 64 bits)

## Supported devices

### DA145XX

* DA14531
* DA14585

Know flash devices:

* MX25R2035F

### DA1468X and DA1469X

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

* DA1470x:
  * DA14701
  * DA14705
  * DA14706
  * DA14708

Know flash devices:

* P25Q80H
* P25Q32LE
* EN25S16B
* EN25S20A
* W25Q128JW
* MX25U3235F
* W25Q80EW
* W25Q32JW
* IS25WP032
* GD25LE32
* GD25LE16
* AT25FF081A
* AT25SL321

## Installation

```
> pip install ezFlashCLI
```

**Windows**: It often happens during python installation that the Script folder is **not** added in the environment PATH. If ezFLashCLI is not found in your terminal, add *\<Python install dir\>/Scripts* to your path.

## Usage

### List JLink probes

```
> ezFlashCLI list

INFO:root:ezFlashCLI v1.0.x
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:JLink devices:
INFO:root:  - 483345692
INFO:root:  - 480698727
```

### Probe attached flash

```
> ezFlashCLI probe

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:Smartbond chip: DA14585/DA14586
INFO:root:Flash information:
INFO:root:  - Device Id: MX25R2035F
```

### Multiple devices

```
> ezFlashCLI list

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:JLink devices:
INFO:root:  - 483245871
INFO:root:  - 483124587

> ezFlashCLI -j 483245871 probe

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:Smartbond chip: DA1469x
INFO:root:Flash information:
INFO:root:  - Device Id: MX25U3235F

> ezFlashCLI -j 483245871 probe

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:Smartbond chip: DA14682/DA14683
INFO:root:Flash information:
INFO:root:  - Device Id: W25Q80EW
```

### erase Flash

```
> ezFlashCLI erase_flash

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:Flash erase success
```

### Read Flash

```
> ezFlashCLI read_flash 0x0 128

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:00000000: 50 70 00 20 00 00 00 20 00 00 eb 00 a5 a8 66 00
INFO:root:00000010: 00 00 aa 11 03 00 01 40 07 c8 4e ff ff ff ff ff
```

### Program Flash

```
> ezFlashCLI image_flash <path to bin file>

INFO:root:ezFlashCLI v1.0.X
INFO:root:By using the program you accept the SEGGER J-link™ license
INFO:root:[DA1469x] Program image
INFO:root:[DA1469x] Program success
```

The tool will automatically make the input file bootable if needed
