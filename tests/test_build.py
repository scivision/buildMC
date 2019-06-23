#!/usr/bin/env python
import pytest
import pkg_resources
import subprocess

from buildmc.cmake import Cmake
from buildmc.mesonbuild import Meson


def test_version(tmp_path):
    try:
        C = Cmake()
    except FileNotFoundError:
        pytest.skip('CMake not present')

    vers = C.version
    assert vers >= pkg_resources.parse_version('3.0')


def test_not_gen(tmp_path):
    params = {'build_dir': tmp_path}
    C = Cmake(params)
    with pytest.raises(subprocess.CalledProcessError):
        C.build()

    M = Meson(params)
    with pytest.raises(subprocess.CalledProcessError):
        M.build_test()


if __name__ == '__main__':
    pytest.main([__file__])
