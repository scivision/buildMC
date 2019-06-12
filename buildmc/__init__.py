from pathlib import Path
from typing import Tuple, Dict, Union, List
from . import mesonbuild as meson
from . import cmake
from .compilers import get_compiler


def do_build(params: Dict[str, Union[str, Path]],
             args: List[str], *,
             wipe: bool, dotest: bool):
    """
    attempts build with Meson or CMake
    """
    if not params['build_system'] in ('cmake', 'meson'):
        raise ValueError('buildMC only knows CMake and Meson')

    compilers, compiler_args = get_compiler(str(params['vendor']))

    args += compiler_args

    params['source_dir'], params['build_dir'] = get_dirs(params['source_dir'], params['build_dir'])

    if params['build_system'] == 'meson':
        meson.meson_config(params, compilers, args, wipe=wipe, dotest=dotest)
    elif params['build_system'] == 'cmake':
        cmake.cmake_config(params, compilers, args, wipe=wipe, dotest=dotest)
    else:
        raise ValueError(params['build_system'])


def get_dirs(source_dir: Union[str, Path],
             build_dir: Union[str, Path]) -> Tuple[Path, Path]:

    if source_dir:
        source_dir = Path(source_dir).expanduser().resolve()
        if not source_dir.is_dir():
            raise NotADirectoryError(source_dir)
    else:
        source_dir = Path().cwd()
        if not source_dir.is_dir():
            raise SystemExit('Please specify a source directory.   buildmc -s mydirectory')

    if build_dir:
        build_dir = Path(build_dir).expanduser().resolve()
        if not build_dir.is_dir():
            raise NotADirectoryError(build_dir)
    else:
        build_dir = source_dir.parent / 'build'
        if not build_dir.is_dir():
            raise SystemExit('Please specify a build directory.   buildmc -b mydirectory')

    return source_dir, build_dir
