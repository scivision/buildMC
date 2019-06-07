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
from pathlib import Path
import os
import sys
import shutil
import subprocess
from typing import Dict, List, Tuple, Union
from argparse import ArgumentParser

if sys.version_info < (3, 6):
    raise RuntimeError('buildMC requires Python >= 3.6')

MESON = shutil.which('meson')
NINJA = shutil.which('ninja')
CMAKE = shutil.which('cmake')
CTEST = shutil.which('ctest')


def main():
    p = ArgumentParser()
    p.add_argument('vendor', help='compiler vendor [clang, gnu, intel, msvc, pgi]', nargs='?', default='gnu')
    p.add_argument('-s', '--srcdir', help='path to source directory')
    p.add_argument('-b', '--builddir', help='path to build directory')
    p.add_argument('-wipe', help='wipe and rebuild from scratch', action='store_true')
    p.add_argument('-buildsys', help='default build system', default='cmake')
    p.add_argument('-args', help='preprocessor arguments', nargs='+', default=[])
    p.add_argument('-debug', help='debug (-O0) instead of release (-O3) build', action='store_true')
    p.add_argument('-test', help='run self-test / example', action='store_true')
    p.add_argument('-install', help='specify full install directory e.g. ~/libs_gcc/mylib')
    a = p.parse_args()

    params = {'build_system': a.buildsys.lower()}

    if not params['build_system'] in ('cmake', 'meson'):
        raise ValueError('buildMC only knows CMake and Meson')

    if a.srcdir:
        params['source_dir'] = Path(a.srcdir).expanduser().resolve()
        if not params['source_dir'].is_dir():
            raise NotADirectoryError(params['source_dir'])
    else:
        params['source_dir'] = Path().resolve()
        if not params['source_dir'].is_dir():
            raise SystemExit('Please specify a source directory.   buildmc -s mydirectory')

    if a.builddir:
        params['build_dir'] = Path(a.builddir).expanduser().resolve()
        if not params['build_dir'].is_dir():
            raise NotADirectoryError(params['build_dir'])
    else:
        params['build_dir'] = params['source_dir'] / 'build'
        if not params['build_dir'].is_dir():
            raise SystemExit('Please specify a build directory.   buildmc -b mydirectory')

    # TODO: make more programmatic
    params['msvc_cmake'] = 'Visual Studio 15 2017'

    if not params['source_dir'].is_dir():
        raise NotADirectoryError(params['source_dir'])

    if a.vendor == 'clang':
        compilers, args = clang_params()
    elif a.vendor in ('gnu', 'gcc'):
        compilers, args = gnu_params()
    elif a.vendor == 'intel':
        compilers, args = intel_params()
    elif a.vendor == 'msvc':
        compilers, args = msvc_params()
    elif a.vendor == 'pgi':
        compilers, args = pgi_params()
    else:
        raise ValueError(a.vendor)

    args += a.args
    if a.debug:
        args.append('-DCMAKE_BUILD_TYPE=Debug')

    do_build(params, compilers, args, wipe=a.wipe, dotest=a.test, install=a.install)


def do_build(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
             args: List[str], **kwargs):
    """
    attempts build with Meson or CMake
    """
    if params['build_system'] == 'meson' and MESON and NINJA:
        meson_config(params, compilers, args, **kwargs)
    elif params['build_system'] == 'cmake' and CMAKE:
        cmake_config(params, compilers, args, **kwargs)
    else:
        raise FileNotFoundError('Could not find CMake or Meson + Ninja')


def _needs_wipe(fn: Path, compilers: Dict[str, str], wipe: bool) -> bool:
    """
    This detection of regeneration needed is not perfect.
    """
    if not fn.is_file():
        return False

    if wipe:
        return True

    with fn.open() as f:
        for line in f:
            if line.startswith('CMAKE_C_COMPILER:FILEPATH'):
                cc = line.split('/')[-1].strip()  # must have strip() for junk in cache
                if cc != compilers['CC']:
                    print('regenerating due to C compiler change:', cc, '=>', compilers['CC'])
                    wipe = True
                    break
            elif line.startswith('CMAKE_GENERATOR:INTERNAL'):
                gen = line.split('=')[-1]
                if gen.startswith('Unix') and os.name == 'nt':
                    print('regenerating due to OS change: Unix => Windows')
                    wipe = True
                    break
                elif gen.startswith(('MinGW', 'Visual')) and os.name != 'nt':
                    print('regenerating due to OS change: Windows => Unix')
                    wipe = True
                    break
                elif gen.startswith('Visual') and compilers['CC'] != 'cl':
                    print('regenerating due to C compiler change: MSVC =>', compilers['CC'])
                    wipe = True
                    break

    return wipe


def cmake_config(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
                 args: List[str], **kwargs):
    """
    attempt to build using CMake >= 3
    """

    build_dir = Path(params['build_dir'])
    source_dir = Path(params['source_dir'])

    cmakelists = source_dir / 'CMakeLists.txt'
    if not cmakelists.is_file():
        raise FileNotFoundError(cmakelists)

    wopts: List[str]
    if compilers['CC'] == 'cl':
        wopts = ['-G', str(params['msvc_cmake']), '-A', 'x64']
    elif os.name == 'nt':
        wopts = ['-G', 'MinGW Makefiles', '-DCMAKE_SH=CMAKE_SH-NOTFOUND']
    else:
        wopts = []

    wopts += args

    if kwargs.get('install'):  # path specified
        wopts.append('-DCMAKE_INSTALL_PREFIX:PATH=' +
                     str(Path(kwargs['install']).expanduser()))

    cachefile = build_dir / 'CMakeCache.txt'

    if _needs_wipe(cachefile, compilers, kwargs.get('wipe')):
        cachefile.unlink()
        shutil.rmtree(build_dir/'CMakeFiles', ignore_errors=True)

    #  -S srcdir -B builddir require CMake >= 3.13
    cmd: List[str] = [CMAKE] + wopts + [str(source_dir)]
    ret = subprocess.run(cmd, cwd=build_dir, env=os.environ.update(compilers))
    if ret.returncode:
        raise SystemExit(ret.returncode)

    # --parallel requires CMake >= 3.12
    ret = subprocess.run([CMAKE, '--build', str(build_dir), '--parallel'])

    test_result(ret)

# %% test
    _cmake_test(params, compilers, kwargs.get('dotest'))
# %% install
    if kwargs.get('install'):
        subprocess.run([CMAKE, '--build', str(params['build_dir']), '--parallel', '--target', 'install'])
        if ret.returncode:
            raise SystemExit(ret.returncode)


def _cmake_test(params: Dict[str, Union[str, Path]], compilers: Dict[str, str], dotest: bool):
    if not dotest:
        return

    if not CTEST:
        raise FileNotFoundError('CTest not available')

    if compilers['CC'] == 'cl':
        ret = subprocess.run([CMAKE, '--build', str(params['build_dir']), '--target', 'RUN_TESTS'])
        if ret.returncode:
            raise SystemExit(ret.returncode)
    else:
        ret = subprocess.run([CTEST, '--parallel', '--output-on-failure'], cwd=params['build_dir'])
        if ret.returncode:
            raise SystemExit(ret.returncode)


def meson_config(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
                 args: List[str], **kwargs):
    """
    attempt to build with Meson + Ninja
    """
    build_dir = Path(params['build_dir'])
    source_dir = Path(params['source_dir'])

    meson_build = source_dir / 'meson.build'

    if not meson_build.is_file():
        raise FileNotFoundError(meson_build)

    build_ninja = build_dir / 'build.ninja'

    meson_setup = [MESON] + ['setup'] + args

    if kwargs.get('install'):
        meson_setup.append('--prefix '+str(Path(kwargs['install']).expanduser()))

    if kwargs.get('wipe') and build_ninja.is_file():
        meson_setup.append('--wipe')

    meson_setup += [str(params['build_dir']), str(source_dir)]

    if kwargs.get('wipe') or not build_ninja.is_file():
        ret = subprocess.run(meson_setup, env=os.environ.update(compilers))
        if ret.returncode:
            raise SystemExit(ret.returncode)

    ret = subprocess.run([NINJA, '-C', str(params['build_dir'])])

    test_result(ret)

    if kwargs.get('dotest'):
        if not ret.returncode:
            ret = subprocess.run([MESON, 'test', '-C', str(params['build_dir'])])  # type: ignore     # MyPy bug
            if ret.returncode:
                raise SystemExit(ret.returncode)

    if kwargs.get('install'):
        if not ret.returncode:
            ret = subprocess.run([MESON, 'install', '-C', str(params['build_dir'])])  # type: ignore     # MyPy bug
            if ret.returncode:
                raise SystemExit(ret.returncode)


def test_result(ret: subprocess.CompletedProcess):
    if not ret.returncode:
        print('\nBuild Complete!')
    else:
        raise SystemExit(ret.returncode)


# %% compilers
def clang_params() -> Tuple[Dict[str, str], List[str]]:
    """
    LLVM compilers e.g. Clang, Flang
    """
    compilers = {'CC': 'clang', 'CXX': 'clang++', 'FC': 'flang'}

    args: List[str] = []

    return compilers, args


def gnu_params() -> Tuple[Dict[str, str], List[str]]:
    """
    GNU compilers e.g. GCC, Gfortran
    """
    compilers = {'FC': 'gfortran', 'CC': 'gcc', 'CXX': 'g++'}

    args: List[str] = []

    return compilers, args


def intel_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Intel compilers
    """
    if not os.environ.get('MKLROOT'):
        raise EnvironmentError('must have set MKLROOT by running compilervars.bat or source compilervars.sh before this script.')

    # %% compiler variables
    compilers = {'FC': 'ifort'}

    if os.name == 'nt':
        compilers['CC'] = compilers['CXX'] = 'icl.exe'
    else:
        compilers['CC'] = 'icc'
        compilers['CXX'] = 'icpc'

    args: List[str] = []

    return compilers, args


def msvc_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Micro$oft Visual Studio

    Note in general MSVC doesn't have good modern C++ features,
    so don't be surprised if a C++11 or newer program doesn't compile.
    """
    if not shutil.which('cl'):
        raise EnvironmentError('Must have PATH set to include MSVC cl.exe compiler bin directory')

    compilers = {'CC': 'cl', 'CXX': 'cl'}

    args: List[str] = []

    return compilers, args


def pgi_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Nvidia PGI compilers

    pgc++ is not available on Windows at this time
    """
    if not shutil.which('pgcc') or not shutil.which('pgfortran'):
        raise EnvironmentError('Must have PATH set to include PGI compiler bin directory')

    # %% compiler variables
    compilers = {'FC': 'pgfortran', 'CC': 'pgcc'}
    if os.name != 'nt':
        compilers['CXX'] = 'pgc++'

    args: List[str] = []

    return compilers, args


if __name__ == '__main__':
    main()
