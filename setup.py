"""Setup for the  ezFlash CLI packaging."""
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
import re

from setuptools import find_packages, setup

import ezFlashCLI

version = ezFlashCLI.get_version_from_git()

try:
    relStatus = os.environ["EZFLASH_RELEASE"]
except KeyError:
    relStatus = "development"

if not ("dirty" in version) and relStatus == "release":
    index = re.search(".dev", version).start()
    version = version[:index]


ezFlashCLI.write_version_file(version)

print("Building ezFlashCLI version", version)


with open("README.md") as readme_file:
    readme = readme_file.read()


requirements = []

test_requirements = [
    # TODO: put package test requirements here
    "pyserial",
]


setup(
    name="ezFlashCLI",
    version=version,
    description="Command line tool to manipulate microcontroller flash",
    long_description_content_type="text/markdown",
    long_description=readme,
    author="ezflash",
    author_email="info@ezflash.org",
    url="https://github.com/ezflash/ezFlashCLI.git",
    packages=find_packages(),
    package_dir={"ezFlashCLI": "ezFlashCLI"},
    include_package_data=True,
    install_requires=requirements,
    dependency_links=[],
    license="MIT license",
    zip_safe=False,
    keywords=["flash", "programmer"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "ezFlashCLI=ezFlashCLI.cli:main",
            "ezSerialCLI=ezFlashCLI.serialCLI:main",
        ],
    },
    tests_require=test_requirements,
)

print("Removing version.txt")
try:
    os.remove(ezFlashCLI.VERSION_FILE_PATH)
except Exception as e:
    print("Failed to remove version file", e)
    pass
