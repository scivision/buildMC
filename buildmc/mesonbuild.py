from typing import Dict,  List, Any
from pathlib import Path
import shutil
import subprocess
import os
import json
import logging

from .compilers import get_compiler

LANGS = ['c', 'cpp', 'fortran']


class Meson():

    def __init__(self, params: Dict[str, Any] = {}, args: List[str] = []):

        self.meson_exe = shutil.which('meson')
        if not self.meson_exe:
            raise ImportError('Meson executable not found')

        self.ninja_exe = shutil.which('ninja')
        if not self.ninja_exe:
            raise ImportError('Ninja executable not found')

        source_dir = params.get('source_dir', Path.cwd())
        if not source_dir:
            source_dir = Path.cwd()
        self.source_dir = Path(source_dir).expanduser().resolve()

        build_dir = params.get('build_dir', self.source_dir / 'build')
        if not build_dir:
            build_dir = self.source_dir / 'build'
        self.build_dir = Path(build_dir).expanduser().resolve()

        self.install_dir = params.get('install_dir')

        self.do_test = params.get('do_test')

        self.vendor = params.get('vendor')

        self.compiler, compiler_args = get_compiler(self.vendor)

        self.args = args
        self.args += compiler_args

    def config(self, wipe: bool):
        """
        attempt to build with Meson + Ninja
        """

        meson_build = self.source_dir / 'meson.build'

        if not meson_build.is_file():
            raise FileNotFoundError(meson_build)

        meson_setup = [self.meson_exe] + ['setup'] + self.args

        if self.install_dir:
            meson_setup.append('--prefix '+str(Path(self.install_dir).expanduser()))

        wipe = self.needs_wipe(wipe)
        if wipe:
            meson_setup.append('--wipe')

        meson_setup += [str(self.build_dir), str(self.source_dir)]

        if wipe or not (self.build_dir / 'build.ninja').is_file():
            subprocess.check_call(meson_setup, env=os.environ.update(self.compiler))

        self.build_test()

        if self.install_dir:
            subprocess.check_call([self.meson_exe, 'install', '-C', str(self.build_dir)])

    def build_test(self):

        if self.do_test:  # build and test
            subprocess.check_call([self.meson_exe, 'test', '-C', str(self.build_dir)])
        else:  # build only
            subprocess.check_call([self.ninja_exe, '-C', str(self.build_dir)])

    def needs_wipe(self, wipe: bool) -> bool:
        """
        https://mesonbuild.com/IDE-integration.html
        """

        if ((self.build_dir / 'meson-private/coredata.dat').is_file() and
                not (self.build_dir / 'build.ninja').is_file()):
            return True

        if wipe:
            return True

        cache_fn = self.build_dir / 'meson-info' / 'intro-targets.json'
        if not cache_fn.is_file():
            return False
        cache = json.loads(cache_fn.read_text())

        if self.check_compiler_cache(cache):
            return True

        return wipe

    def check_compiler_cache(self, cache: List[Dict[str, Any]]) -> bool:
        compilers = self.get_compiler_cache(cache)

        if set(compilers).intersection(self.compiler.values()):
            return False

        logging.info(f'Compiler changes from {compilers} => {self.compiler}')
        return True

    @staticmethod
    def get_compiler_cache(cache: List[Dict[str, Any]]) -> List[str]:
        compilers: List[str] = []

        for target in cache:
            for src in target['target_sources']:
                if src['language'] in LANGS:
                    compilers += src['compiler']

        return compilers
