from typing import Dict,  List, Any
from pathlib import Path
import shutil
import subprocess
import os
import json
import logging


def meson_config(params: Dict[str, Any], compilers: Dict[str, str],
                 args: List[str], *, wipe: bool):
    """
    attempt to build with Meson + Ninja
    """

    meson_exe = shutil.which('meson')
    if not meson_exe:
        raise FileNotFoundError('Meson executable not found')

    ninja_exe = shutil.which('ninja')
    if not ninja_exe:
        raise FileNotFoundError('Ninja executable not found')

    build_dir = params['build_dir']
    source_dir = params['source_dir']

    meson_build = source_dir / 'meson.build'

    if not meson_build.is_file():
        raise FileNotFoundError(meson_build)

    build_ninja = build_dir / 'build.ninja'

    meson_setup = [meson_exe] + ['setup'] + args

    if params.get('install_dir'):
        meson_setup.append('--prefix '+str(Path(params['install_dir']).expanduser()))

    wipe = _needs_wipe(params, compilers, wipe, build_ninja)

    if wipe:
        meson_setup.append('--wipe')

    meson_setup += [str(params['build_dir']), str(source_dir)]

    if wipe or not build_ninja.is_file():
        ret = subprocess.run(meson_setup, env=os.environ.update(compilers))
        if ret.returncode:
            raise SystemExit(ret.returncode)

    ret = subprocess.run([ninja_exe, '-C', str(params['build_dir'])])

    test_result(ret)

    if params.get('do_test'):
        if not ret.returncode:
            ret = subprocess.run([meson_exe, 'test', '-C', str(params['build_dir'])])
            if ret.returncode:
                raise SystemExit(ret.returncode)

    if params.get('install_dir'):
        if not ret.returncode:
            ret = subprocess.run([meson_exe, 'install', '-C', str(params['build_dir'])])
            if ret.returncode:
                raise SystemExit(ret.returncode)


def _needs_wipe(params: Dict[str, Any],
                compilers: Dict[str, str],
                wipe: bool, build_ninja: Path) -> bool:
    """
    https://mesonbuild.com/IDE-integration.html
    """
    if not build_ninja.is_file():
        return False

    if wipe:
        return True

    api_dir = params['build_dir'] / 'meson-info'
    cache_fn = api_dir / 'intro-targets.json'
    cache = json.loads(cache_fn.read_text())

    if _check_compiler_cache(compilers, cache, 'CC'):
        return True

    return wipe


def _check_compiler_cache(compilers: Dict[str, str], cache: List[Dict[str, Any]], envvar: str) -> bool:
    if envvar == 'CC':
        lang = 'c'
    elif envvar == 'CXX':
        lang = 'cpp'
    elif envvar == 'FC':
        lang = 'fortran'
    else:  # FIXME: other languages
        return False

    c = _get_compiler(cache, lang)

    if c.startswith(str(compilers.get(envvar))):
        logging.info(f'C compiler changes from {c} => {compilers[envvar]}')
        return True

    return False


def _get_compiler(cache: List[Dict[str, Any]], language: str) -> str:
    for target in cache:
        for src in target['target_sources']:
            if src['language'] == 'fortran':
                compiler = src['compiler'][0]
                break

    return compiler


def test_result(ret: subprocess.CompletedProcess):
    if not ret.returncode:
        print('\nBuild Complete!')
    else:
        raise SystemExit(ret.returncode)
