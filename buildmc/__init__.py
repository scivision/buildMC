from pathlib import Path
from typing import Dict, Any, List

from .cmake import Cmake
from .mesonbuild import Meson


def do_build(params: Dict[str, Any],
             args: List[str] = [],
             wipe: bool = False):
    """
    attempts build with Meson or CMake
    """
    build_system = get_buildsystem(params['build_system'], params['source_dir'])

    if build_system == 'meson':
        M = Meson(params)
        M.config(wipe)
    elif build_system == 'cmake':
        C = Cmake(params)
        C.config(wipe)
    else:
        raise ValueError(f'I do not know about build_system {build_system}')


def find_buildfile(source_dir: Path) -> str:

    if source_dir:
        source_dir = Path(source_dir).expanduser()
    else:
        source_dir = Path.cwd()

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
        bsys = find_buildfile(source_dir)
    elif isinstance(build_system, str):
        bsys = build_system
    elif isinstance(build_system, Path):
        bsys = build_system.stem
    else:
        raise TypeError(build_system)

    return bsys
