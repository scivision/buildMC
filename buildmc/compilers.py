from typing import Dict, Tuple, List
import os
import shutil


def get_compiler(vendor: str) -> Tuple[Dict[str, str], List[str]]:

    if vendor == 'clang':
        compilers, args = clang_params()
    elif vendor in ('gnu', 'gcc'):
        compilers, args = gnu_params()
    elif vendor == 'intel':
        compilers, args = intel_params()
    elif vendor == 'msvc':
        compilers, args = msvc_params()
    elif vendor in ('clangcl', 'clang-cl'):
        compilers, args = clangcl_params()
    elif vendor == 'pgi':
        compilers, args = pgi_params()
    else:
        raise ValueError(vendor)

    return compilers, args


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
        compilers['CC'] = compilers['CXX'] = 'icl'
    else:
        compilers['CC'] = 'icc'
        compilers['CXX'] = 'icpc'

    args: List[str] = []

    return compilers, args


# %% Windows


def clangcl_params() -> Tuple[Dict[str, str], List[str]]:
    """
    LLVM compiler MSVC-like interface e.g. Clang, Flang
    """
    compilers = {'CC': 'clang-cl', 'CXX': 'clang-cl', 'FC': 'flang'}

    args: List[str] = []

    return compilers, args


def msvc_params() -> Tuple[Dict[str, str], List[str]]:
    """
    Micro$oft Visual Studio

    Note in general MSVC lacks modern C++ features common to other C++ compilers,
    so don't be surprised if a C++11 or newer program doesn't compile.
    """
    if not shutil.which('cl'):
        raise EnvironmentError('Must have PATH set to include MSVC cl.exe compiler bin directory')

    compilers = {'CC': 'cl', 'CXX': 'cl'}

    args: List[str] = []

    return compilers, args


def pgi_params(hints: Dict[str, str] = {}) -> Tuple[Dict[str, str], List[str]]:
    """
    Nvidia PGI compilers

    pgc++ is not available on Windows at this time
    """
    if not shutil.which('pgcc') or not shutil.which('pgfortran'):
        raise EnvironmentError('Must have PATH set to include PGI compiler bin directory')

    # %% compiler variables
    compilers = {'FC': 'pgfortran', 'CC': 'pgcc'}
    if os.name == 'nt':
        if hints.get('CXX'):
            compilers['CXX'] = hints['CXX']
        else:
            compilers['CXX'] = 'cl'
    else:
        compilers['CXX'] = 'pgc++'

    args: List[str] = []

    return compilers, args
