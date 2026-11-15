Timestamp library and utility
=============================

``tslib`` is a timestamp processing toolkit and library, written in
Python. It is very helpful when dealing with the millisecond-precision
timestamps that we encounter all the time in computer systems, and to
work with human-readable time deltas away from "now".

Installation
------------

You can install ``tslib`` directly from PyPI with the following command:

::

    $ pip install tslib

If you're installing from a clone of this repository, use:

::

    $ git clone https://github.com/mpetazzoni/tslib
    $ cd tslib/
    $ pip install -e .

``tslib`` requires Python 3.11 or newer. Named timezones use Python's
``zoneinfo`` module and the system IANA timezone database, with the
automatically installed ``tzdata`` package as a fallback. Neither ``pytz``
nor ``six`` is required.

You're now ready to use ``ts``, which should be directly available in
your ``$PATH``.

Usage
-----

::

    $ ts -h
    usage: ts [-h] [-t TZ] [-n] [-i] [-a {minute,hour,day}]

    Human readable timestamps

    options:
      -h, --help            show this help message and exit
      -t, --timezone TZ     Use IANA timezone TZ (default: OS local timezone)
      -n, --timestamp-only  Only output the resulting millisecond timestamp(s)
      -i, --inline          Apply timestamp replacements inline of the incoming
                            text
      -a, --align {minute,hour,day}
                            Align the timestamp

``ts`` transforms milliseconds timestamps and human-readable deltas into
fully qualified date and time printouts, containing:

-  the UTC timestamp (since Epoch)
-  the UTC time represented by the timestamp
-  the local time represented by the timestamp
-  the human-readable delta of this timestamp against current time

The output is tab-delimited and can easily be re-segmented by piping
into ``column -t -s "\t"``.

Arguments can be passed as command-line arguments, or piped into ``ts``
via STDIN. If no input comes from either of these sources, ``ts`` will
simply output the current time:

::

    $ ts -t America/Los_Angeles
    1423599084206 2015-02-10 20:11:24.206 UTC+0000  2015-02-10 12:11:24.206 PST-0800  0

Inline mode
-----------

``ts`` can operate in inline-replacement mode, for timestamps only. In
this mode, you can pipe in any text and ``ts`` will output it back to
you with all timestamps replaced with a human-readable date and time and
human-readable delta representation.

Given the inherent difficulty of accurately matching timestamps, the
matching is limited to 13-digits millisecond precision timestamps (that
may be immediately followed by a ``L``). Numbers smaller, or larger than
13 digits are not matched, and are left alone; meaning no 13-digit
section of them is matched and replaced.

::

    $ echo B_b-3PAAYAA B_cJXlvAYAA B_cJXl6AcAA \
        | xargs sfc mb g -p TSVH -f sf_checkpointTimestampMs -f sf_updatedOnMs \
        | ts -i -t America/Los_Angeles \
        | column -t -s "    "
    sf_id        sf_checkpointTimestampMs                              sf_updatedOnMs
    B_b-3PAAYAA  2015-03-06 13:38:58.851 PST-0800 (-2w5h18m6s210)      2015-03-06 13:38:58.852 PST-0800 (-2w5h18m6s209)
    B_cJXlvAYAA  2015-03-08 09:04:36.218 PDT-0700 (-1w5d10h52m28s843)  2015-03-08 09:04:36.218 PDT-0700 (-1w5d10h52m28s844)
    B_cJXl6AcAA  2015-03-08 09:04:34.252 PDT-0700 (-1w5d10h52m30s810)  2015-03-08 09:04:34.342 PDT-0700 (-1w5d10h52m30s720)

More examples
-------------

Piping:

::

    $ cat << EOF | ts -t America/Los_Angeles
    pipe heredoc> 1404424797009L
    pipe heredoc> 1415917836779L
    pipe heredoc> EOF
    1404424797009 2014-07-03 21:59:57.009 UTC+0000  2014-07-03 14:59:57.009 PDT-0700  -31w5d1h14m26s38
    1415917836779 2014-11-13 22:30:36.779 UTC+0000  2014-11-13 14:30:36.779 PST-0800  -12w5d43m46s268

Using the column output (assuming the same input in a ``/tmp/ts.txt``
file):

::

    $ cat /tmp/ts.txt | ts | cut -f4
    -31w5d1h16m17s703
    -12w5d45m37s933

Sorting on a column (here, by descending timestamps in first column):

::

    $ cat /tmp/ts.txt | ts -t America/Los_Angeles | sort -k1 -t $'\t' -r
    1415917836779 2014-11-13 22:30:36.779 UTC+0000  2014-11-13 14:30:36.779 PST-0800  -12w5d46m6s924
    1404424797009 2014-07-03 21:59:57.009 UTC+0000  2014-07-03 14:59:57.009 PDT-0700  -31w5d1h16m46s694

Deltas
------

Human-readable deltas can be expressed in weeks (``w``), days (``d``),
hours (``h``), minutes (``m``), and seconds (``s``). The remainder,
without a unit, is assumed to be milliseconds. Any "segment" can be
omitted, the only requirement is that the segments that are specified
are written in descending order of span (days before hours, hours before
minutes, etc.).

Here's an example: ``-12w4d6m57s257``. Note that *hours* are missing,
which simply means 12 weeks, 4 days, 6 minutes, 57 seconds and 257
milliseconds.

As you might have guessed, deltas can be both negative and positive. For
positive deltas, the leading ``+`` may be omitted if units are used,
otherwise the number is assumed to be an absolute timestamp:

::

    $ ts -t America/Los_Angeles -1
    1423599850752 2015-02-10 20:24:10.752 UTC+0000  2015-02-10 12:24:10.752 PST-0800  -1
    $ ts -t America/Los_Angeles 0 1
                0 1970-01-01 00:00:00.000 UTC+0000  1969-12-31 16:00:00.000 PST-0800  -2353w5d20h24m14s145
                1 1970-01-01 00:00:00.001 UTC+0000  1969-12-31 16:00:00.001 PST-0800  -2353w5d20h24m14s144
    $ ts -t America/Los_Angeles +1
    1423599855941 2015-02-10 20:24:15.941 UTC+0000  2015-02-10 12:24:15.941 PST-0800  1

Using a different local timezone
--------------------------------

The third column shows the timestamp's representation in local time. By
default it uses the operating system's configured local timezone, including
the daylight-saving offset appropriate to the timestamp being converted.
It does not depend on the legacy ``US/Pacific`` timezone alias. On POSIX
systems, the ``TZ`` environment variable can override the local timezone.

Use ``-t`` to select an explicit IANA timezone name, such as ``UTC``,
``America/Los_Angeles``, or ``Europe/Paris``. Invalid names produce a
command-line usage error. The Pacific-time examples above explicitly select
``America/Los_Angeles`` so their output does not depend on the host timezone:

::

    $ ts -t Europe/Paris
    1423600015955 2015-02-10 20:26:55.955 UTC+0000  2015-02-10 21:26:55.955 CET+0100  0

Absolute, human-readable offsets from Epoch
-------------------------------------------

By prefixing a human-readable delta with an equal sign (``=``), you
obtain an absolute offset from the Epoch. The side-effect of this is
that it allows for converting a human-readable delta into its
corresponding millisecond duration.

::

    $ ts -n '=1h'
          3600000
    $ ts -t America/Los_Angeles '=1d'
         86400000 1970-01-02 00:00:00.000 UTC+0000  1970-01-01 16:00:00.000 PST-0800  -2365w6d21h56m20s98

Alignment
---------

``-a minute``, ``-a hour``, and ``-a day`` round forward to the next UTC
boundary, even if the timestamp is already aligned. The chosen display
timezone does not change the alignment:

::

    $ ts -n -a hour 1
          3600000

Library compatibility
---------------------

UTC datetime helpers now return standard-library ``datetime`` objects with
``datetime.timezone.utc`` rather than ``pytz.utc``. ``date_from_utc`` still
requires a naive datetime and rejects an already timezone-aware value.
Replace ``pytz``-specific operations such as ``localize`` and ``normalize``
with standard-library datetime operations when upgrading.

``render_date(date)`` keeps its UTC display default for library callers.
Pass ``None`` to use the OS-local timezone, or a ``zoneinfo.ZoneInfo`` object
to select a named timezone:

::

    from zoneinfo import ZoneInfo
    from tslib import date_from_utc_ts, render_date

    print(render_date(date_from_utc_ts(1404424797009), ZoneInfo("Europe/Paris")))

Development
-----------

Install the development dependencies in a virtual environment, then run:

::

    $ python -m pip install -e '.[dev]'
    $ python -m pytest
    $ python -m ruff check .
    $ python -m build
    $ python -m twine check dist/*

CI runs these checks on Python 3.11 through 3.14 on Linux, macOS, and Windows.

Publishing
----------

Attach the validated wheel and source archive to a stable GitHub release
tagged ``tslib-VERSION``. Publishing that release triggers ``publish.yml``,
which verifies the distribution names, versions, and GitHub asset SHA-256
digests before uploading the same files to PyPI via Trusted Publishing.
Prereleases and drafts are not published.

The PyPI trusted publisher must match repository ``mpetazzoni/tslib``,
workflow ``publish.yml``, and GitHub environment ``pypi``. Only the isolated
publishing job receives OIDC permission; no API token is required. Configure
the GitHub ``pypi`` environment's protection rules as desired before running
the workflow.

For an existing release, dispatch the workflow from ``main`` with its tag:

::

    $ gh workflow run publish.yml --ref main -f tag=tslib-2.0

Upload both distributions before publishing the GitHub release. Dispatching
from another branch is ignored, and duplicate PyPI uploads fail rather than
silently skipping existing files.
