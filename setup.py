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


from setuptools import setup,find_packages
import getpass

from ezFlashCLI.cli import __version__

with open('README.md') as readme_file:
    readme = readme_file.read()


requirements = [

]

test_requirements = [
    # TODO: put package test requirements here
]


setup(
    name='ezFlashCLI',
    version=__version__,
    description="Command line tool to manipulate microcontroller flash",
    long_description_content_type='text/markdown',
    long_description=readme,
    author="ezflash",
    author_email='info@ezflash.org',
    url='https://github.com/ezflash/ezFlashCLI.git',
    packages=find_packages(),
    package_dir={'ezFlashCLI': 'ezFlashCLI'},
    include_package_data=True,
    install_requires=requirements,
    dependency_links=[],
    license="MIT license",
    zip_safe=False,
    keywords=['flash','programmer'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    scripts=['Scripts/ezFlashCLI'],

    tests_require=test_requirements
)