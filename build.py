#!/usr/bin/env python
"""
buildMC makes building projects with CMake or Meson + Ninja even simpler.
It facilitates easy testing across operating systems and compiler vendors.
Michael Hirsch, Ph.D.

## Intel

The Intel compiler environment must be configured before running build.py:

* Windows: compilervars.bat intel64
* Linux / Mac: source compilervars.sh intel64

## compiler hints

Certain compilers are ABI compatible with each other. For these cases, a user
can specify a main compiler vendor.
Example:

    buildmc ~/my_project -v intel
"""
from pathlib import Path
from argparse import ArgumentParser
import logging
import buildmc


def main():
    p = ArgumentParser()
    p.add_argument('source_dir', help='path to source directory', nargs='?', default=Path.cwd())
    p.add_argument('-v', '--vendor', help='compiler vendor [clang, clang-cl, gnu, intel, msvc, pgi]')
    p.add_argument('-b', '--build_dir', help='path to build directory')
    p.add_argument('-wipe', help='wipe and rebuild from scratch', action='store_true')
    p.add_argument('-s', '--buildsys', help='default build system')
    p.add_argument('-cfg', help='path to buildmc.ini file')
    p.add_argument('-args', help='preprocessor arguments', nargs='+', default=[])
    p.add_argument('-debug', help='debug (-O0) instead of release (-O3) build', action='store_true')
    p.add_argument('-test', help='run project self-test, if available', action='store_true')
    p.add_argument('-install', help='specify full install directory e.g. ~/libs_gcc/mylib')
    p.add_argument('-msvc', help='desired MSVC')
    a = p.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    args = a.args
    if a.debug:
        args.append('-DCMAKE_BUILD_TYPE=Debug')

    params = {'source_dir': a.source_dir,
              'build_dir': a.build_dir,
              'vendor': a.vendor,
              'build_system': a.buildsys,
              'msvc_cmake': a.msvc,
              'install_dir': a.install,
              'do_test': a.test,
              'config_fn': a.cfg}

    buildmc.do_build(params, args, wipe=a.wipe)


if __name__ == '__main__':
    main()
