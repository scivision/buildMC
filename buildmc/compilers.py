from typing import Dict, Tuple, List, Union, Sequence
import os
import shutil

from . import config


def get_compiler(vendor: Sequence[str]) -> Tuple[Dict[str, str], List[str]]:

    if not vendor:
        vendor = ['gnu']
    if isinstance(vendor, str):
        vendor = [vendor]

    vs = set(vendor)

    if vs.intersection(('gnu', 'gcc')):
        compilers, args = gnu_params()
    elif vs.intersection(('clang', 'flang', 'llvm')):
        compilers, args = clang_params()
    elif vs.intersection(('intel', 'icl', 'icc')):
        compilers, args = intel_params()
    elif vs.intersection(('msvc', 'cl')):
        compilers, args = msvc_params()
    elif vs.intersection(('clangcl', 'clang-cl')):
        compilers, args = clangcl_params()
    elif vs.intersection(('pgi', 'pgcc')):
        compilers, args = pgi_params()
    else:
        raise ValueError(f'unknown compiler vendor {vendor}')

    return compilers, args


def clang_params() -> Tuple[Dict[str, str], List[str]]:
    """
    LLVM compilers e.g. Clang, Flang
    """
    compilers = {'CC': 'clang',
                 'CXX': 'clang++',
                 'FC': 'flang'}

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('Clang compiler not found')

    args: List[str] = []

    return compilers, args


def gnu_params() -> Tuple[Dict[str, str], List[str]]:
    """
    GNU compilers e.g. GCC, Gfortran
    """
    compilers = {'FC': 'gfortran',
                 'CC': 'gcc',
                 'CXX': 'g++'}

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('GCC compiler not found')

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
        compilers['CC'] = compilers['CXX'] = 'icl'
    else:
        compilers['CC'] = 'icc'
        compilers['CXX'] = 'icpc'

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('Intel compiler not found')

    args: List[str] = []

    return compilers, args


# %% Windows


def clangcl_params() -> Tuple[Dict[str, str], List[str]]:
    """
    LLVM compiler MSVC-like interface e.g. Clang
    """
    compilers = {'CC': 'clang-cl',
                 'CXX': 'clang-cl'}

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('Clang-CL compiler not found')

    args: List[str] = []

    return compilers, args


def msvc_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Micro$oft Visual Studio

    Note in general MSVC lacks modern C++ features common to other C++ compilers,
    so don't be surprised if a C++11 or newer program doesn't compile.

    An MSVC-compatible Fortran compiler may be specified.
    It's up to the user to be sure it's compatible (will error during build otherwise).
    """

    compilers = {'CC': 'cl',
                 'CXX': 'cl'}

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('Must have PATH set to include MSVC cl.exe compiler bin directory')

    hints = config.get_compiler_spec()

    if hints.get('FC'):
        compilers['FC'] = hints['FC']
        if not shutil.which(compilers['FC']):
            raise EnvironmentError('Fortran compiler {compilers["FC"]} not found')

    args: List[str] = []

    return compilers, args


def pgi_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Nvidia PGI compilers

    pgc++ is not available on Windows at this time
    """

    compilers = {'FC': 'pgfortran',
                 'CC': 'pgcc'}

    if os.name == 'nt':
        cspec = config.get_compiler_spec()
        if cspec.get('CXX'):
            compilers['CXX'] = cspec['CXX']
        else:
            compilers['CXX'] = 'cl'
    else:
        compilers['CXX'] = 'pgc++'

    compilers['CXX'] = compilers['CXX']

    if not shutil.which(compilers['CC']):
        raise EnvironmentError('Must have PATH set to include PGI compiler bin directory')

    args: List[str] = []

    return compilers, args


def is_msvc(cc: Union[str, Dict[str, str]]) -> bool:
    """
    cc: str
        Name of C compiler e.g. from str(compilers.get('CC'))
    """
    if isinstance(cc, dict):
        cc = cc.get('CC')

    cc = str(cc)

    return cc.startswith('cl') and not cc.startswith('clang')
