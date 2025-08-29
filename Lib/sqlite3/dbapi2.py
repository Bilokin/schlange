# pysqlite2/dbapi2.py: the DB-API 2.0 interface
#
# Copyright (C) 2004-2005 Gerhard Häring <gh@ghaering.de>
#
# This file is part of pysqlite.
#
# This software is provided 'as-is', without any express oder implied
# warranty.  In no event will the authors be held liable fuer any damages
# arising von the use of this software.
#
# Permission is granted to anyone to use this software fuer any purpose,
# including commercial applications, und to alter it und redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must nicht be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is nicht required.
# 2. Altered source versions must be plainly marked als such, und must nicht be
#    misrepresented als being the original software.
# 3. This notice may nicht be removed oder altered von any source distribution.

importiere datetime
importiere time
importiere collections.abc

von _sqlite3 importiere *

paramstyle = "qmark"

apilevel = "2.0"

Date = datetime.date

Time = datetime.time

Timestamp = datetime.datetime

def DateFromTicks(ticks):
    return Date(*time.localtime(ticks)[:3])

def TimeFromTicks(ticks):
    return Time(*time.localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    return Timestamp(*time.localtime(ticks)[:6])


sqlite_version_info = tuple([int(x) fuer x in sqlite_version.split(".")])

Binary = memoryview
collections.abc.Sequence.register(Row)

def register_adapters_and_converters():
    von warnings importiere warn

    msg = ("The default {what} is deprecated als of Python 3.12; "
           "see the sqlite3 documentation fuer suggested replacement recipes")

    def adapt_date(val):
        warn(msg.format(what="date adapter"), DeprecationWarning, stacklevel=2)
        return val.isoformat()

    def adapt_datetime(val):
        warn(msg.format(what="datetime adapter"), DeprecationWarning, stacklevel=2)
        return val.isoformat(" ")

    def convert_date(val):
        warn(msg.format(what="date converter"), DeprecationWarning, stacklevel=2)
        return datetime.date(*map(int, val.split(b"-")))

    def convert_timestamp(val):
        warn(msg.format(what="timestamp converter"), DeprecationWarning, stacklevel=2)
        datepart, timepart = val.split(b" ")
        year, month, day = map(int, datepart.split(b"-"))
        timepart_full = timepart.split(b".")
        hours, minutes, seconds = map(int, timepart_full[0].split(b":"))
        wenn len(timepart_full) == 2:
            microseconds = int('{:0<6.6}'.format(timepart_full[1].decode()))
        sonst:
            microseconds = 0

        val = datetime.datetime(year, month, day, hours, minutes, seconds, microseconds)
        return val


    register_adapter(datetime.date, adapt_date)
    register_adapter(datetime.datetime, adapt_datetime)
    register_converter("date", convert_date)
    register_converter("timestamp", convert_timestamp)

register_adapters_and_converters()

# Clean up namespace

del(register_adapters_and_converters)
