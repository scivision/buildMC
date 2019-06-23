#!/usr/bin/env python
import pytest
import shutil
from pathlib import Path

import buildmc
import buildmc.compilers as comp

R = Path(__file__).parent

VENDORS = ['gcc', 'clang', 'pgi', 'intel', 'cl']


@pytest.mark.timeout(1800)
@pytest.mark.parametrize('buildsys,vendor', [('cmake', v) for v in VENDORS] +
                                            [('meson', v) for v in VENDORS])
def test_builds(buildsys, vendor, tmp_path):

    if buildsys == 'cmake' and vendor == 'cl':
        pytest.xfail('FIXME: CMake 3.15-rc bug with MSVC and C?')
    if buildsys == 'meson' and vendor == 'pgi':
        pytest.xfail('FIXME: bug in Meson with PGI')

    try:
        compiler, _ = comp.get_compiler(vendor)
    except EnvironmentError:
        pytest.skip(f'{vendor} not available')

    params = {'source_dir': R,
              'build_dir': tmp_path,
              'vendor': vendor,
              'build_system': buildsys,
              }

    buildmc.do_build(params)

    assert shutil.which('minimal_c', path=str(params['build_dir']))

    params['do_test'] = True
    buildmc.do_build(params)


if __name__ == '__main__':
    pytest.main([__file__])
