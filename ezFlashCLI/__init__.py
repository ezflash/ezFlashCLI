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

import os
import subprocess

try:
    from importlib import metadata
except ImportError:
    # importlib.metadata was added in python 3.8
    metadata = None


def _in_git_clone():
    """Check for the .git that the git command below would pick up.

    git searches upwards from the working directory, and .git is a file
    instead of a directory in worktrees and submodules.
    """
    path = os.getcwd()
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return True
        parent = os.path.dirname(path)
        if parent == path:
            return False
        path = parent


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
    if metadata is None:
        raise LookupError("importlib.metadata is not available")
    __version__ = metadata.version("ezFlashCLI")
except Exception:
    try:
        # only try git when running from a checkout, not from a deployed copy
        if not _in_git_clone():
            raise LookupError("not running from a git clone")
        # try to get the version from git
        __version__ = get_version_from_git()
    except Exception:
        __version__ = "1.0.1"
