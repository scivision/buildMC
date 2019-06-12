from typing import Dict, Union, List
from pathlib import Path
import shutil
import subprocess
import os


def makebuild(params: Dict[str, Union[str, Path]], compilers: Dict[str, str],
              args: List[str], *,
              wipe: bool, dotest: bool):
    """
    TODO: this function is untested. Let us know if it's of interest
    """
    make_exe = shutil.which('make')
    if not make_exe and os.name == 'nt':
        make_exe = shutil.which('mingw32-make')

    if not make_exe:
        raise FileNotFoundError('GNU Make executable not found')

    build_dir = Path(params['build_dir'])
    source_dir = Path(params['source_dir'])

    makefile = source_dir / 'Makefile'

    if not makefile.is_file():
        raise FileNotFoundError(makefile)

    base_cmd = [make_exe, '-C', str(build_dir), '-f', str(makefile)]

    if wipe:
        ret = subprocess.run(base_cmd+['clean'])
        if ret.returncode:
            raise SystemExit(ret.returncode)

    ret = subprocess.run(base_cmd + args, env=os.environ.update(compilers))
    if ret.returncode:
        raise SystemExit(ret.returncode)

    test_result(ret)

    if dotest:
        if not ret.returncode:
            ret = subprocess.run(base_cmd + ['test'])
            if ret.returncode:
                raise SystemExit(ret.returncode)

    if params['install_dir']:
        if not ret.returncode:
            ret = subprocess.run(base_cmd + ['install', 'prefix='+str(params['install_dir'])])
            if ret.returncode:
                raise SystemExit(ret.returncode)


def test_result(ret: subprocess.CompletedProcess):
    if not ret.returncode:
        print('\nBuild Complete!')
    else:
        raise SystemExit(ret.returncode)
