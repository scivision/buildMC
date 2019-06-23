from pathlib import Path
import subprocess
from typing import Any, Dict, List
import os
import shutil
import json
import pkg_resources
import logging

from .compilers import is_msvc, get_compiler
from . import config

MSVC = 'Visual Studio 15 2017'


class Cmake():

    def __init__(self, params: Dict[str, Any] = {}, args: List[str] = []):
        self.cmake_exe = shutil.which('cmake')
        if not self.cmake_exe:
            raise FileNotFoundError('CMake executable not found')

        self.get_cmake_version()

        source_dir = params.get('source_dir', Path.cwd())
        if not source_dir:
            source_dir = Path.cwd()
        self.source_dir = Path(source_dir).expanduser().resolve()

        config_fn = params.get('config_fn')
        if not config_fn:
            config_fn = self.source_dir / 'buildmc.ini'
        self.config_fn = config_fn

        build_dir = params.get('build_dir', self.source_dir / 'build')
        if not build_dir:
            build_dir = config.get_build_dir(self.config_fn)
        if not build_dir:
            build_dir = self.source_dir / 'build'
        self.build_dir = Path(build_dir).expanduser().resolve()

        self.install_dir = params.get('install_dir')

        self.do_test = params.get('do_test')

        if params.get('vendor'):
            self.vendor = params['vendor']
        else:
            self.vendor = config.get_compiler(self.config_fn)

        self.compiler, compiler_args = get_compiler(self.vendor)

        self.args = args
        self.args += compiler_args

    def get_cmake_version(self):
        ret = subprocess.check_output([self.cmake_exe, '--version'], universal_newlines=True)
        self.version = pkg_resources.parse_version(ret.split()[2])

    def config(self, wipe: bool = False):
        """
        attempt to build using CMake >= 3
        """

        cmakelists = self.source_dir / 'CMakeLists.txt'
        if not cmakelists.is_file():
            raise FileNotFoundError(cmakelists)

    # %% wipe
        if self.needs_wipe(wipe):
            Path(self.build_dir / 'CMakeCache.txt').unlink()
            shutil.rmtree(self.build_dir/'CMakeFiles', ignore_errors=True)

        self.generate()

        self.build()

        self.test()

        self.install()

    def needs_wipe(self, wipe: bool) -> bool:
        """
        requires CMake >= 3.14

        uses cmake-file-api

        https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html

        index file is largest in lexiographical order:
        https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html#v1-reply-index-file
        """
        if wipe:
            return True

        if not (self.build_dir / 'CMakeCache.txt').is_file():
            return False

        # do this only when asked to use API, to allow basic use with older CMake
        if self.version < pkg_resources.parse_version('3.14'):
            logging.debug('CMake >= 3.14 required for CMake-file-api')
            return False

        api_dir = self.build_dir / '.cmake/api/v1'
        query_dir = api_dir / 'query'
        query_dir.mkdir(parents=True, exist_ok=True)

        # request CMake Cache info
        (query_dir / 'cache-v2').touch()

        resp_dir = api_dir / 'reply'
        indices = sorted(resp_dir.glob('index-*.json'), reverse=True)
        if indices:
            index_fn = indices[0]
            if (self.source_dir / 'CMakeLists.txt').stat().st_mtime > index_fn.stat().st_mtime:
                logging.info('CMakeLists.txt modified after response index, regenerating')
                self.generate()
                index_fn = sorted(resp_dir.glob('index-*.json'), reverse=True)[0]
        else:
            logging.info('CMake run for first generation')
            self.generate()
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
        elif gen.startswith('Visual') and not is_msvc(self.compiler):
            logging.info(f'regenerating due to C compiler change: MSVC => {self.compiler["CC"]}')
            return True

        if self.check_compiler_cache(cache, 'CC', 'C'):
            return True
        if self.check_compiler_cache(cache, 'CXX', 'CXX'):
            return True
        if self.check_compiler_cache(cache, 'FC', 'Fortran'):
            return True

        return wipe

    def generate(self):
        """
        CMake Generate
        """

        wopts: List[str]
        if is_msvc(self.compiler):
            gen = self.get_msvc_generator()
            wopts = ['-G', gen, '-A', 'x64']
        elif os.name == 'nt':
            wopts = ['-G', 'MinGW Makefiles', '-DCMAKE_SH=CMAKE_SH-NOTFOUND']
        else:
            wopts = []

        wopts += self.args

        wopts += self.get_libargs()

        if self.install_dir:  # path specified
            wopts.append('-DCMAKE_INSTALL_PREFIX:PATH=' +
                         str(Path(self.install_dir).expanduser()))

        gen_cmd = [self.cmake_exe] + wopts

        if self.version >= pkg_resources.parse_version('3.13'):
            # Creates build_dir if not exist
            gen_cmd += ['-S', str(self.source_dir), '-B', str(self.build_dir)]
            ret = subprocess.run(gen_cmd, env=os.environ.update(self.compiler))
        else:  # build_dir must exist
            gen_cmd += [str(self.source_dir)]
            ret = subprocess.run(gen_cmd, cwd=self.build_dir, env=os.environ.update(self.compiler))

        if ret.returncode:
            raise SystemExit(' '.join(gen_cmd))

    def test(self):
        if not self.do_test:
            return

        if is_msvc(self.compiler):
            ret = subprocess.run([self.cmake_exe, '--build', str(self.build_dir), '--target', 'RUN_TESTS'])
            if ret.returncode:
                raise SystemExit(ret.returncode)
        else:
            ctest_exe = shutil.which('ctest')
            if not ctest_exe:
                raise FileNotFoundError('CTest not available')
            # ctest --parallel   CMake >= 3.0
            ret = subprocess.run([ctest_exe, '--parallel', '--output-on-failure'], cwd=self.build_dir)
            if ret.returncode:
                raise SystemExit(ret.returncode)

    def install(self):
        if not self.install_dir:
            return

        install_cmd = [self.cmake_exe, '--build', str(self.build_dir), '--target', 'install']

        if self.version >= pkg_resources.parse_version('3.12'):
            install_cmd.append('--parallel')

        ret = subprocess.run(install_cmd)

        if ret.returncode:
            raise SystemExit(ret.returncode)

    def build(self):
        """
        excecute the CMake build command, that compiles and links code.

        cmake --parallel   CMake >= 3.12
        """

        build_cmd = [self.cmake_exe, '--build', str(self.build_dir)]

        if self.version >= pkg_resources.parse_version('3.12'):
            build_cmd.append('--parallel')

        subprocess.check_call(build_cmd)

    @staticmethod
    def get_msvc_generator(gen: str) -> str:
        """
        1. see if user specified MSVC generator in params
        2. see if CMAKE_GENERATOR is set for Visual Studio
        3. fallback to MSVC constant
        """
        if not gen:
            if str(os.environ.get('CMAKE_GENERATOR')).startswith('Visual Studio'):
                gen = os.environ['CMAKE_GENERATOR']
            else:
                gen = MSVC

        return gen

    def check_compiler_cache(self, cache: Dict[str, str],
                             envvar: str, cmake_compiler_name: str) -> bool:
        if self.compiler.get(envvar):
            c = cache.get(f'CMAKE_{cmake_compiler_name}_COMPILER')
            if c and c != 'NOTFOUND':
                c = Path(c).stem
                if not c.startswith(self.compiler[envvar]):
                    logging.info(f'regenerating due to {cmake_compiler_name} '
                                 f'compiler change: {c} => {self.compiler[envvar]}')
                    return True

        return False

    def get_libargs(self) -> List[str]:
        libargs = []
        libs = config.get_library(self.config_fn)
        for lib, lib_dir in libs.items():
            if len(lib_dir) != 1:
                continue
            libargs.append(f'-D{lib.upper()}_ROOT={lib_dir[0]}')

        return libargs
