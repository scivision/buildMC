from pathlib import Path
from typing import Tuple, Dict, Any, List
from . import mesonbuild as meson
from . import cmake
from .compilers import get_compiler
from . import gnumake


def do_build(params: Dict[str, Any],
             args: List[str] = [], *,
             hints: Dict[str, str] = {},
             wipe: bool = False):
    """
    attempts build with Meson or CMake
    """
    compilers, compiler_args = get_compiler(str(params['vendor']), hints)

    args += compiler_args

    params['source_dir'], params['build_dir'] = get_dirs(params['source_dir'], params['build_dir'])

    build_system = get_buildsystem(params.get('build_system'), params['source_dir'])

    if build_system == 'meson':
        meson.meson_config(params, compilers, args, wipe=wipe)
    elif build_system == 'cmake':
        cmake.cmake_config(params, compilers, args, wipe=wipe)
    elif build_system == 'gnumake':
        gnumake.makebuild(params, compilers, args, wipe=wipe)
    else:
        raise ValueError(build_system)


def get_dirs(source_dir: Path, build_dir: Path) -> Tuple[Path, Path]:

    source_dir = Path(source_dir).expanduser().resolve() if source_dir else Path().cwd()

    find_buildfile(source_dir)

    if build_dir:
        build_dir = Path(build_dir).expanduser().resolve()
        if not build_dir.is_dir():
            raise NotADirectoryError(build_dir)
    else:
        build_dir = source_dir / 'build'
        if not build_dir.is_dir():
            raise SystemExit('Please specify a build directory.   buildmc -b mydirectory')

    return source_dir, build_dir


def find_buildfile(source_dir: Path) -> str:

    source_dir = Path(source_dir).expanduser()

    if not source_dir.is_dir():
        raise NotADirectoryError(source_dir)

    if (source_dir / 'CMakeLists.txt').is_file():
        return 'cmake'
    elif (source_dir / 'meson.build').is_file():
        return 'meson'

    raise FileNotFoundError(f'could not find build system file (CMakeLists.txt or meson.build) in {source_dir}')


def get_buildsystem(build_system: Path, source_dir: Path) -> str:
    """
    if user didn't pick a build system, try to figure out which is appropriate for the project
    """

    if not build_system:
        return find_buildfile(source_dir)
    elif isinstance(build_system, str):
        return build_system
    elif isinstance(build_system, Path):
        return build_system.stem

    raise TypeError(build_system)
