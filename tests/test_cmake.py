#!/usr/bin/env python
import pytest
import pkg_resources
import buildmc.cmake as cm


@pytest.mark.skipif(not cm.CMAKE, reason='CMake not present')
def test_version(tmp_path):
    with pytest.raises(FileNotFoundError):
        cm.get_cmake_version(tmp_path)

    with pytest.raises(FileNotFoundError):
        cm.get_cmake_version(tmp_path / 'foo')

    vers = cm.get_cmake_version(cm.CMAKE)
    assert vers >= pkg_resources.parse_version('3.0')

# def test_notexist_sourcefile(tmp_path):
    # with pytest.raises(FileNotFoundError):
    # buildmc.find_buildfile(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__])
