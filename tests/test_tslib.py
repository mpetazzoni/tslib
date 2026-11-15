from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo, reset_tzpath

import pytest

import tslib


@pytest.mark.parametrize('value, expected', [
    ('0', 0), (1, 1), ('1404424797009L', 1404424797009),
    ('=1h', 3600000), ('=1d', 86400000), ('=1w2d3h4m5s6', 788645006),
    ('=0', 0), ('=1', 1),
])
def test_absolute_timestamps(value, expected):
    assert tslib.parse_to_timestamp(value) == expected
    assert tslib.parse_input(value).tzinfo is timezone.utc


@pytest.mark.parametrize('value, offset', [
    ('+1', 1), ('-1', -1), ('1h', 3600000),
    ('-12w4d6m57s257', -7603617257), ('+0', 0),
])
def test_relative_deltas(value, offset):
    now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    with patch.object(tslib, 'utc', return_value=now):
        assert tslib.parse_input(value) == now + timedelta(milliseconds=offset)


@pytest.mark.parametrize('value', ['', 'L', None, 1.5, 'h', '1m1h', 'garbage'])
def test_invalid_input(value):
    with pytest.raises(ValueError):
        tslib.parse_input(value)


@pytest.mark.parametrize('value, expected', [
    (0, '0'), (1, '1'), (-1, '-1'), (1000, '1s'),
    (788645006, '1w2d3h4m5s6'), (-788645006, '-1w2d3h4m5s6'),
])
def test_render_delta(value, expected):
    assert tslib.render_delta(value) == expected
    assert tslib.parse_to_timestamp('=' + expected.lstrip('-')) == abs(value)


def test_utc_helpers():
    before = datetime.now(timezone.utc)
    now = tslib.utc()
    assert before <= now <= datetime.now(timezone.utc)
    assert now.tzinfo is timezone.utc
    naive = datetime(2020, 1, 1)
    assert tslib.date_from_utc(naive) == naive.replace(tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        tslib.date_from_utc(now)
    assert isinstance(tslib.utc_millisecond_timestamp(), int)


def test_render_date_defaults_to_utc():
    date = tslib.date_from_utc_ts(1)
    with patch.object(tslib, 'utc', return_value=date):
        assert tslib.render_date(date).split('\t') == [
            '            1', '1970-01-01 00:00:00.001 UTC+0000',
            '1970-01-01 00:00:00.001 UTC+0000', '0',
        ]


@pytest.mark.parametrize('name', ['America/Los_Angeles', 'US/Pacific'])
@pytest.mark.parametrize('month, expected', [
    (1, '2015-01-01 04:00:00.000 PST-0800'),
    (7, '2015-07-01 05:00:00.000 PDT-0700'),
])
def test_explicit_timezone_dst(name, month, expected):
    date = datetime(2015, month, 1, 12, tzinfo=timezone.utc)
    assert tslib.render_date(date, ZoneInfo(name)).split('\t')[2] == expected


def test_named_timezone_without_system_database():
    ZoneInfo.clear_cache()
    reset_tzpath([])
    try:
        zone = ZoneInfo('America/Los_Angeles')
        assert zone.key == 'America/Los_Angeles'
    finally:
        reset_tzpath()
        ZoneInfo.clear_cache()
