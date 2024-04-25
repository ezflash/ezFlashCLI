"""This file contains identifying information for all supported Smartbond devices."""


class smartbond_device:
    """This class contains identifying information for a Smartbond device."""

    def __init__(
        self,
        identifier,
        pretty_identifier,
        id,
        id_register,
        id_size,
        access_size,
        extra_info=[],
    ):
        """Initialize the device class.

        Args:
            identifier: device name (string)
            pretty_identifier: pretty device name (string)
            id: expected value of id register (string)
            id_register: register address (int)
            id_size: number of bytes to read from id register (int)
            access_size: id register access size (int)
            extra_info: extra register pair to check (list)
        """
        self.identifier = identifier
        self.pretty_identifier = pretty_identifier
        self.id = id
        self.id_register = id_register
        self.id_size = id_size
        self.access_size = access_size
        self.extra_info = extra_info


"""Identifier, Pretty_identifier, register contents, id register address, register size, access size, extra data"""
devices = [
    smartbond_device("da1469x", "DA1469x", "[50, 53, 50, 50]", 0x50040200, 4, 32),
    smartbond_device("da1469x", "DA1469x", "[50, 55, 54, 51]", 0x50040200, 4, 32),
    smartbond_device("da1469x", "DA1469x", "[51, 48, 56, 48]", 0x50040200, 4, 32),
    smartbond_device("da1470x", "DA1470x", "[50, 55, 57, 56]", 0x50040000, 4, 32),
    smartbond_device("da1470x", "DA1470x", "[51, 49, 48, 55]", 0x50040000, 4, 32),
    smartbond_device("da14592", "DA14592", "[50, 54, 51, 52, 2]", 0x50050200, 5, 32),
    smartbond_device("da14531", "DA14535", "[51, 0, 51, 0, 48]", 0x50003200, 5, 8),
    smartbond_device(
        "da14531_00",
        "DA14531-00",
        "[50, 0, 50, 0, 54]",
        0x50003200,
        5,
        8,
        ["[7, 33, 1, 112]", 0x07F04000, 4, 8],
    ),
    smartbond_device(
        "da14531_01",
        "DA14531-01",
        "[50, 0, 50, 0, 54]",
        0x50003200,
        5,
        8,
        ["[32, 70, 254, 247]", 0x07F04000, 4, 8],
    ),
    smartbond_device("da14531", "DA14531", "[50, 0, 50, 0, 54]", 0x50003200, 5, 8),
    smartbond_device("da14585", "DA14585", "[53, 56, 53, 1, 65]", 0x50003200, 5, 8),
    smartbond_device("da14585", "DA14585", "[53, 56, 53, 0, 65]", 0x50003200, 5, 8),
    smartbond_device("da14580", "DA14580", "[53, 56, 48, 1, 65]", 0x50003200, 5, 8),
    smartbond_device(
        "da14681", "DA14680/DA14681", "[54, 56, 48, 0, 65]", 0x50003200, 5, 8
    ),
    smartbond_device(
        "da14683", "DA14682/DA14683", "[54, 56, 48, 0, 66]", 0x50003200, 5, 8
    ),
]
