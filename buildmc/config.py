from configparser import ConfigParser
from typing import Dict, List
from pathlib import Path
import logging


def get_build_dir(cfgfn: Path = None) -> str:
    cfgfn = get_cfg_path(cfgfn)

    if not cfgfn.is_file():
        logging.debug(f'{cfgfn} not found')
        return None

    C = ConfigParser()
    C.read(cfgfn)

    return C.get('buildmc', 'build_dir')


def get_library(cfgfn: Path = None) -> Dict[str, List[str]]:

    cfgfn = get_cfg_path(cfgfn)

    if not cfgfn.is_file():
        logging.info(f'{cfgfn} not found, using default config')
        return {}

    C = ConfigParser()
    C.read(cfgfn)

    libs = {}
    for l in C.get('buildmc', 'library').split('\n'):
        if not l:
            continue
        lspec = l.split(' ')
        libs[lspec[0]] = lspec[1:]

    return libs


def get_compiler(cfgfn: Path = None) -> List[str]:

    cfgfn = get_cfg_path(cfgfn)

    if not cfgfn.is_file():
        logging.info(f'{cfgfn} not found, using default config')
        return []

    C = ConfigParser()
    C.read(cfgfn)

    cc = []
    for l in C.get('buildmc', 'compiler').split('\n'):
        if not l:
            continue
        lspec = l.split(' ')
        cc.append(lspec[0])

    return cc


def get_compiler_spec(cfgfn: Path = None) -> Dict[str, str]:

    cfgfn = get_cfg_path(cfgfn)

    if not cfgfn.is_file():
        logging.debug(f'{cfgfn} not found')
        return {}

    C = ConfigParser()
    C.read(cfgfn)

    cspecs = {}
    for k in ('CC', 'CXX', 'FC'):
        cspecs[k] = C.get('compiler_spec', k)

    return cspecs


def get_cfg_path(cfgfn: Path) -> Path:
    name = 'buildmc.ini'

    if cfgfn is None:
        cfgfn = Path.cwd() / name

    cfgfn = Path(cfgfn).expanduser()

    if cfgfn.is_dir():
        cfgfn = cfgfn / name

    return cfgfn
