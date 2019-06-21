#!/usr/bin/env python
import pytest
import shutil
from pathlib import Path

import buildmc

R = Path(__file__).parent


@pytest.mark.skipif(not shutil.which('cl'), reason='MSVC appears not to be loaded via vcvars64.bat')
def test_msvc(tmp_path):
    params = {'source_dir': R/'src',
              'build_dir': tmp_path,
              'vendor': 'msvc',
              }
    buildmc.do_build(params)

    params['test'] = True
    buildmc.do_build(params)


@pytest.mark.skipif(not shutil.which('gcc'), reason='GCC appears not available')
def test_gcc(tmp_path):
    params = {'source_dir': R/'src',
              'build_dir': tmp_path,
              'vendor': 'gcc',
              }
    buildmc.do_build(params)

    params['do_test'] = True
    buildmc.do_build(params)


if __name__ == '__main__':
    pytest.main([__file__])
