#!/usr/bin/env python
import pytest
from pathlib import Path
import pkg_resources as pr

import buildmc.config as cfg
from buildmc.cmake import Cmake

R = Path(__file__).parent


def test_nofile(tmp_path):
    assert not cfg.get_library(tmp_path)


def test_read_libs(tmp_path):

    assert cfg.get_library(tmp_path) == {}

    libs = cfg.get_library(R)

    assert pr.parse_version(libs['python'][1]) >= pr.parse_version('3.6')
    assert '~/nonexistent' in libs['lapack']


def test_read_compiler(tmp_path):

    assert cfg.get_compiler(tmp_path) == []

    compilers = cfg.get_compiler(R)
    assert isinstance(compilers, list)

    assert 'gcc' in compilers
    assert 'intel' in compilers


def test_cmake_libargs():
    C = Cmake({'source_dir': R})
    libargs = C.get_libargs()

    assert libargs[0] == '-DLAPACK_ROOT=~/nonexistent'


def test_complier_spec(tmp_path):

    assert cfg.get_compiler_spec(tmp_path) == {}

    cspecs = cfg.get_compiler_spec()
    assert 'FC' in cspecs


if __name__ == '__main__':
    pytest.main([__file__])
