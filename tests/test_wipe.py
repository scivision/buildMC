#!/usr/bin/env python
"""
test detection of needing to wipe build directory
"""
from pathlib import Path
import pytest
import tempfile

from buildmc.cmake import Cmake
from buildmc.mesonbuild import Meson
from buildmc.compilers import get_compiler

R = Path(__file__).parent
first_cmake = True
first_meson = True

VENDORS = ['gcc', 'clang', 'pgi', 'intel', 'cl']


@pytest.fixture(scope="module")
def dir_gen():
    # persists until all tests in this file are done, then erases.
    td = tempfile.TemporaryDirectory()
    yield Path(td.name)
    td.cleanup()


def test_cmake_empty(tmp_path):
    params = {'build_dir': tmp_path}
    C = Cmake(params)
    assert not C.needs_wipe(False)
    assert C.needs_wipe(True)


@pytest.mark.parametrize('vendor', VENDORS)
def test_cmake_blank(vendor, dir_gen):
    global first_cmake

    try:
        compiler, _ = get_compiler(vendor)
    except EnvironmentError:
        pytest.skip(f'{vendor} not available')

    params = {'build_dir': dir_gen, 'source_dir': R, 'vendor': vendor}
    (params['build_dir'] / 'CMakeCache.txt').touch()

    C = Cmake(params)

    if first_cmake:
        assert not C.needs_wipe(False)
        first_cmake = False
    else:
        assert C.needs_wipe(False)


def test_meson_empty(tmp_path):
    build_dir = tmp_path
    params = {'build_dir': build_dir, 'source_dir': R}
    M = Meson(params)

    assert not M.needs_wipe(False)
    assert M.needs_wipe(True)


@pytest.mark.parametrize('vendor', VENDORS)
def test_meson_blank(vendor, dir_gen):
    global first_meson

    try:
        compiler, _ = get_compiler(vendor)
    except EnvironmentError:
        pytest.skip(f'{vendor} not available')

    params = {'build_dir': dir_gen, 'source_dir': R, 'vendor': vendor}
    M = Meson(params)

    if first_meson:
        assert not M.needs_wipe(False)
        M.config(False)
        first_meson = False
    else:
        assert M.needs_wipe(False)
        M.config(True)


if __name__ == '__main__':
    pytest.main([__file__])
