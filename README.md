[![DOI](https://zenodo.org/badge/190810341.svg)](https://zenodo.org/badge/latestdoi/190810341)

[![Build Status](https://travis-ci.com/scivision/buildMC.svg?branch=master)](https://travis-ci.com/scivision/buildMC)
[![Build status](https://ci.appveyor.com/api/projects/status/od39fe9u8u8jqh4j?svg=true)](https://ci.appveyor.com/project/scivision/buildmc)
[![pypi versions](https://img.shields.io/pypi/pyversions/buildmc.svg)](https://pypi.python.org/pypi/buildmc)
[![PyPi Download stats](http://pepy.tech/badge/buildmc)](http://pepy.tech/project/buildmc)

# buildMC

A pure Python program that makes building a large, complicated project using CMake or Meson just a single, simple command.
JSON from the build system API gives robust and fast build system status / interaction.

## Install

Prereqs:

* Python &ge; 3.6
* build system: any _one_ of:
  * CMake &ge; 3.0 + GNU Make
  * [Meson](https://www.mesonbuild.com) + Ninja
* compilers necessary for the project code

```sh
pip install buildmc
```

or to use latest development code
```sh
git clone https://github.com/scivision/buildmc

cd buildmc

pip install -e .
```


## Usage

buildMC makes switching between compilers trivial.
Also, building on native Windows and Windows Subsystem for Linux is detected and handled--the CMake or Meson cache is wiped to allow clean rebuild when switching without fuss.


### Examples

Say you want to ensure a project builds with each of Visual Studio, GNU/GCC, Intel and Clang.
This can be easily done by typing in the top-level of the project directory:

```sh
buildmc msvc

buildmc gnu

buildmc intel

buildmc clang
```

Each command independently builds and runs the user-configured tests via the selected build system.
When switching between Windows and Linux (using WSL from Windows) buildMC detects the OS switch and wipes the build cache and rebuilds as needed.


## Notes

### CMake

An easy way to upgrade to the latest CMake on Linux or Windows is via [CMakeUtils](https://github.com/scivision/cmake-utils):
```sh
pip install cmakeutils

cmake_setup
```