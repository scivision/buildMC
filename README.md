# buildMC

A pure Python program that makes building a large, complicated project using CMake or Meson just a single, simple command.

## Install

Prereqs:

* Python &ge; 3.6
* CMake &ge; 3.12 _or_ Meson+Ninja

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

Each command independently builds and runs the user-configured tests using CMake or Meson.
When switching between Windows and Linux (using WSL from Windows) buildMC detects the OS switch and wipes the build cache and rebuilds as needed.

