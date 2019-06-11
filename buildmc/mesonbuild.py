from typing import Dict, Union, List
from pathlib import Path
import shutil
import subprocess
import os
import json
import logging
import itertools

MESON = shutil.which('meson')
NINJA = shutil.which('ninja')


def meson_config(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
                 args: List[str], *,
                 wipe: bool, dotest: bool):
    """
    attempt to build with Meson + Ninja
    """

    if not MESON:
        raise FileNotFoundError('Meson executable not found')

    if not NINJA:
        raise FileNotFoundError('Ninja executable not found')

    build_dir = Path(params['build_dir'])
    source_dir = Path(params['source_dir'])

    meson_build = source_dir / 'meson.build'

    if not meson_build.is_file():
        raise FileNotFoundError(meson_build)

    build_ninja = build_dir / 'build.ninja'

    meson_setup = [MESON] + ['setup'] + args

    if params['install_dir']:
        meson_setup.append('--prefix '+str(Path(params['install_dir']).expanduser()))

    wipe = _needs_wipe(params, compilers, wipe, build_ninja)

    if wipe:
        meson_setup.append('--wipe')

    meson_setup += [str(params['build_dir']), str(source_dir)]

    if wipe or not build_ninja.is_file():
        ret = subprocess.run(meson_setup, env=os.environ.update(compilers))
        if ret.returncode:
            raise SystemExit(ret.returncode)

    ret = subprocess.run([NINJA, '-C', str(params['build_dir'])])

    test_result(ret)

    if dotest:
        if not ret.returncode:
            ret = subprocess.run([MESON, 'test', '-C', str(params['build_dir'])])  # type: ignore     # MyPy bug
            if ret.returncode:
                raise SystemExit(ret.returncode)

    if params['install_dir']:
        if not ret.returncode:
            ret = subprocess.run([MESON, 'install', '-C', str(params['build_dir'])])  # type: ignore     # MyPy bug
            if ret.returncode:
                raise SystemExit(ret.returncode)


def _needs_wipe(params: Dict[str, Union[str, Path]],
                compilers: Dict[str, str],
                wipe: bool, build_ninja: Path) -> bool:
    """
    https://mesonbuild.com/IDE-integration.html
    """
    if not build_ninja.is_file():
        return False

    if wipe:
        return True

    api_dir = Path(params['build_dir']) / 'meson-info'
    cache_fn = api_dir / 'intro-targets.json'
    cache = json.loads(cache_fn.read_text())

    ccs = {target['name']: [src['compiler'] for src in target['target_sources'] if src['language'] == 'c'] for target in cache}
    cc = next(itertools.chain.from_iterable(*ccs.values()))

    if compilers['CC'] != cc:
        logging.info(f'C compiler changes from {cc} => {compilers["CC"]}')
        return True

    ccs = {target['name']: [src['compiler'] for src in target['target_sources'] if src['language'] == 'cpp'] for target in cache}
    cc = next(itertools.chain.from_iterable(*ccs.values()))

    if compilers['CXX'] != cc:
        logging.info(f'CXX compiler changes from {cc} => {compilers["CXX"]}')
        return True

    ccs = {target['name']: [src['compiler']
                            for src in target['target_sources'] if src['language'] == 'fortran'] for target in cache}
    cc = next(itertools.chain.from_iterable(*ccs.values()))

    if compilers['FC'] != cc:
        logging.info(f'Fortran compiler changes from {cc} => {compilers["FC"]}')
        return True

    return wipe


def test_result(ret: subprocess.CompletedProcess):
    if not ret.returncode:
        print('\nBuild Complete!')
    else:
        raise SystemExit(ret.returncode)