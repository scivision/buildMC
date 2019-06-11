from pathlib import Path
import subprocess
from typing import Union, Dict, List
import os
import shutil
import json
from pkg_resources import parse_version
import logging

CMAKE = shutil.which('cmake')
CTEST = shutil.which('ctest')


def cmake_config(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
                 args: List[str], *,
                 wipe: bool, dotest: bool):
    """
    attempt to build using CMake >= 3
    """
    if not CMAKE:
        raise FileNotFoundError('CMake executable not found')

    ret = subprocess.check_output(['cmake', '--version'], universal_newlines=True)
    params['cmake_version'] = ret.split()[2]

    build_dir = Path(params['build_dir'])

    cmakelists = Path(params['source_dir']) / 'CMakeLists.txt'
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

    if params['install_dir']:  # path specified
        wopts.append('-DCMAKE_INSTALL_PREFIX:PATH=' +
                     str(Path(params['install_dir']).expanduser()))

    params['cmake_cache'] = build_dir / 'CMakeCache.txt'

    if _needs_wipe(params, compilers, wopts, wipe):
        Path(params['cmake_cache']).unlink()
        shutil.rmtree(build_dir/'CMakeFiles', ignore_errors=True)

    _cmake_generate(params, compilers, wopts)

    ret = subprocess.run([CMAKE, '--build', str(build_dir), '--parallel'])

    _test_result(ret)

# %% test
    _cmake_test(params, compilers, dotest)
# %% install
    if params['install_dir']:
        subprocess.run([CMAKE, '--build', str(params['build_dir']), '--parallel', '--target', 'install'])
        if ret.returncode:
            raise SystemExit(ret.returncode)


def _cmake_generate(params: Dict[str, Union[str, Path]],
                    compilers: Dict[str, str],
                    wopts: List[str] = []):

    if parse_version(str(params['cmake_version'])) < parse_version('3.13'):
        raise RuntimeError('CMake >= 3.14 required by buildmc')

    cmd: List[str] = [CMAKE] + wopts + ['-S', str(params['source_dir']),
                                        '-B', str(params['build_dir'])]
    ret = subprocess.run(cmd, env=os.environ.update(compilers))
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


def _needs_wipe(params: Dict[str, Union[str, Path]],
                compilers: Dict[str, str],
                wopts: List[str],
                wipe: bool) -> bool:
    """
    requires CMake >= 3.14

    this will replace _needs_wipe_legacy()   uses cmake-file-api

    https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html

    index file is largest in lexiographical order:
    https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html#v1-reply-index-file
    """
    if parse_version(str(params['cmake_version'])) < parse_version('3.14'):
        raise RuntimeError('CMake >= 3.14 required by buildmc')

    if wipe:
        return True

    if not Path(params['cmake_cache']).is_file():
        return False

    api_dir = Path(params['build_dir']) / '.cmake/api/v1'
    query_dir = api_dir / 'query'
    query_dir.mkdir(parents=True, exist_ok=True)

    # request CMake Cache info
    (query_dir / 'cache-v2').touch()

    resp_dir = api_dir / 'reply'
    indices = sorted(resp_dir.glob('index-*.json'), reverse=True)
    if indices:
        index_fn = indices[0]
    else:
        logging.info('CMake run for first generation')
        _cmake_generate(params, compilers, wopts)
        index_fn = sorted(resp_dir.glob('index-*.json'), reverse=True)[0]

    if (Path(params['source_dir']) / 'CMakeLists.txt').stat().st_mtime > index_fn.stat().st_mtime:
        logging.info('CMakeLists.txt modified after response index, regenerating')
        _cmake_generate(params, compilers, wopts)
        index_fn = sorted(resp_dir.glob('index-*.json'), reverse=True)[0]

    index = json.loads(index_fn.read_text())
    cache_fn = resp_dir / index['reply']['cache-v2']['jsonFile']

    cmakecache = json.loads(cache_fn.read_text())
    cache = {entry['name']: entry['value'] for entry in cmakecache['entries']}

    gen = cache['CMAKE_GENERATOR']
    if gen.startswith('Unix') and os.name == 'nt':
        logging.info('regenerating due to OS change: Unix => Windows')
        return True
    elif gen.startswith('MinGW') and os.name != 'nt':
        logging.info('regenerating due to OS change: Windows => Unix')
        return True
    elif gen.startswith('Visual') and compilers['CC'] != 'cl':
        logging.info(f'regenerating due to C compiler change: MSVC => {compilers["CC"]}')
        return True

    cc = cache.get('CMAKE_C_COMPILER')
    if cc:
        cc = Path(cc).stem
        if cc != compilers['CC']:
            logging.info(f'regenerating due to C compiler change: {cc} => {compilers["CC"]}')
            return True

    cxx = cache.get('CMAKE_CXX_COMPILER')
    if cxx:
        cxx = Path(cxx).stem
        if cxx != compilers['CXX']:
            logging.info(f'regenerating due to CXX compiler change: {cxx} => {compilers["CXX"]}')
            return True

    fc = cache.get('CMAKE_Fortran_COMPILER')
    if fc:
        fc = Path(fc).stem
        if fc != compilers['FC']:
            logging.info(f'regenerating due to Fortran compiler change: {fc} => {compilers["FC"]}')
            return True

    return wipe


def _test_result(ret: subprocess.CompletedProcess):
    if not ret.returncode:
        print('\nBuild Complete!')
    else:
        raise SystemExit(ret.returncode)
