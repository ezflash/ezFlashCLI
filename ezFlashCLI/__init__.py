"""Module for ezFlash cli."""
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
import subprocess
from importlib import metadata


def get_version_from_git():
    """Generate the version string from git describe."""
    # grab the version from git describe
    version = (
        subprocess.check_output(
            ["git", "describe", "--always", "--long", "--dirty", "--tags"]
        )
        .strip()
        .decode("utf-8")[1:]
    )
    # process the string to be PEP 440 compliant
    version = version.replace("-", ".dev", 1).replace("-", "+", 1).replace("-", ".", 1)

    return version


try:
    __version__ = metadata.version("ezFlashCLI")
except Exception:
    try:
        # try to get the version from git
        __version__ = get_version_from_git()
    except Exception:
        __version__ = "unkown-requires-git"
