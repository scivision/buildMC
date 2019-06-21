#!/usr/bin/env python
import pytest
import subprocess
import buildmc


def test_notexist_sourcedir(tmp_path):
    badpath = tmp_path / 'abc123'
    with pytest.raises(NotADirectoryError):
        buildmc.find_buildfile(badpath)

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(['buildmc', '-s', str(badpath)])


def test_notexist_sourcefile(tmp_path):
    with pytest.raises(FileNotFoundError):
        buildmc.find_buildfile(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__])
