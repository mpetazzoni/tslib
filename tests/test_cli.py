import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

import tslib


def cli(*args, stdin='', env=None):
    # Exercise the same main function as the installed console entry point.
    return subprocess.run(
        [sys.executable, '-c', 'from tslib import main; main()', *args],
        input=stdin, text=True, capture_output=True, env=env, check=False,
    )


def test_explicit_timezone():
    result = cli('-t', 'Europe/Paris', '0')
    assert result.returncode == 0
    assert result.stdout.split('\t')[2] == '1970-01-01 01:00:00.000 CET+0100'


@pytest.mark.parametrize('zone', ['Not/A_Zone', '/etc/passwd', '', '../UTC'])
def test_invalid_timezone(zone):
    result = cli('-t', zone, '0')
    assert result.returncode == 2
    assert 'Unknown timezone:' in result.stderr
    assert 'Traceback' not in result.stderr


def test_help():
    result = cli('--help')
    assert result.returncode == 0
    assert 'default: OS local timezone' in result.stdout
    assert '--align' in result.stdout


def test_timestamp_only_and_stdin():
    result = cli('-n', '=1h', stdin='0\n1L\n')
    assert result.returncode == 0
    assert result.stdout.splitlines() == ['      3600000', '            0', '            1']


def test_inline_boundaries():
    result = cli('-i', '-t', 'UTC', stdin='a 1404424797009L b 123 11404424797009 14044247970099\n')
    assert result.returncode == 0
    assert result.stdout.startswith('a 2014-07-03 21:59:57.009 UTC+0000 (')
    assert result.stdout.endswith(') b 123 11404424797009 14044247970099\n')


@pytest.mark.parametrize('alignment, expected', [
    ('minute', 60000), ('hour', 3600000), ('day', 86400000),
])
@pytest.mark.parametrize('timestamp', ['0', '1'])
def test_alignment(alignment, expected, timestamp):
    result = cli('-n', '-a', alignment, timestamp)
    assert result.returncode == 0
    assert int(result.stdout) == expected


def test_no_input_on_terminal(capsys):
    now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    with patch.object(sys, 'argv', ['ts', '-n']), \
            patch.object(sys, 'stdin', Mock()), \
            patch.object(os, 'isatty', return_value=True), \
            patch.object(tslib, 'utc', return_value=now):
        tslib.main()
    assert int(capsys.readouterr().out) == 1577836800000


@pytest.mark.skipif(not hasattr(time, 'tzset'), reason='Requires POSIX TZ support')
@pytest.mark.parametrize('month, expected', [
    (1, '2015-01-01 04:00:00.000 PST-0800'),
    (7, '2015-07-01 05:00:00.000 PDT-0700'),
])
def test_os_local_default_uses_timestamp_dst(monkeypatch, month, expected):
    previous = os.environ.get('TZ')
    # A POSIX rule needs neither tzdata-legacy nor any named timezone files.
    monkeypatch.setenv('TZ', 'PST8PDT,M3.2.0,M11.1.0')
    time.tzset()
    try:
        date = datetime(2015, month, 1, 12, tzinfo=timezone.utc)
        assert tslib.render_date(date, None).split('\t')[2] == expected
        timestamp = int(date.timestamp() * 1000)
        result = cli(str(timestamp))
        assert result.returncode == 0
        assert result.stdout.split('\t')[2] == expected
    finally:
        if previous is None:
            monkeypatch.delenv('TZ')
        else:
            monkeypatch.setenv('TZ', previous)
        time.tzset()


def test_default_passes_none_without_named_zone_lookup(capsys):
    with patch.object(sys, 'argv', ['ts', '0']), \
            patch.object(sys, 'stdin', Mock()), \
            patch.object(os, 'isatty', return_value=True), \
            patch.object(tslib, 'ZoneInfo', side_effect=AssertionError('Named zone lookup')), \
            patch.object(tslib, 'render_date', return_value='local') as render:
        tslib.main()
    assert render.call_args.args[1] is None
    assert capsys.readouterr().out == 'local\n'
