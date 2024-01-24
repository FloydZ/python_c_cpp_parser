#!/usr/bin/env python3
from MeasureSuiteCommandLine import __version__, __author__, __email__
from setuptools import setup


def read_text_file(path):
    import os
    with open(os.path.join(os.path.dirname(__file__), path)) as f:
        return f.read()


setup(
    name="MeasureSuiteCommandLine",
    version=__version__,
    description="TODO",
    long_description=read_text_file("README.md"),
    author=__author__,
    author_email=__email__,
    url="https://github.com/FloydZ/MeasureSuiteCommandLine",
    packages=["MeasureSuiteCommandLine"],
    keywords=["assembly", "assembler", "asm", "opcodes", "x86", "x86-64", "isa", "cpu"],
    install_requires=["setuptools"],
    requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Assembly",
	    "Programming Language :: Python",
	    "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Topic :: Software Development :: Assemblers",
        "Topic :: Software Development :: Documentation"
    ])
