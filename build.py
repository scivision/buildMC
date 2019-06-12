#!/usr/bin/env python
"""
buildMC makes building projects with CMake or Meson + Ninja even simpler.
It facilitates easy testing across operating systems and compiler vendors.
Michael Hirsch, Ph.D.

## Intel

The Intel compiler environment must be configured before running build.py:

* Windows: compilervars.bat intel64
* Linux / Mac: source compilervars.sh intel64
"""
from argparse import ArgumentParser
import logging
import buildmc


def main():
    p = ArgumentParser()
    p.add_argument('vendor', help='compiler vendor [clang, gnu, intel, msvc, pgi]', nargs='?', default='gnu')
    p.add_argument('-s', '--srcdir', help='path to source directory')
    p.add_argument('-b', '--builddir', help='path to build directory')
    p.add_argument('-wipe', help='wipe and rebuild from scratch', action='store_true')
    p.add_argument('-buildsys', help='default build system', default='cmake')
    p.add_argument('-args', help='preprocessor arguments', nargs='+', default=[])
    p.add_argument('-debug', help='debug (-O0) instead of release (-O3) build', action='store_true')
    p.add_argument('-test', help='run project self-test, if available', action='store_true')
    p.add_argument('-install', help='specify full install directory e.g. ~/libs_gcc/mylib')
    p.add_argument('-msvc', help='desired MSVC', default='Visual Studio 15 2017')
    a = p.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    params = {'build_system': a.buildsys.lower(),
              'source_dir': a.srcdir,
              'build_dir': a.builddir,
              'vendor': a.vendor,
              'msvc_cmake': a.msvc,
              'install_dir': a.install}

    args = a.args
    if a.debug:
        args.append('-DCMAKE_BUILD_TYPE=Debug')

    buildmc.do_build(params, args, wipe=a.wipe, dotest=a.test)


if __name__ == '__main__':
    main()
