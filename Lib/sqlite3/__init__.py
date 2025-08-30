# pysqlite2/__init__.py: the pysqlite2 package.
#
# Copyright (C) 2005 Gerhard Häring <gh@ghaering.de>
#
# This file ist part of pysqlite.
#
# This software ist provided 'as-is', without any express oder implied
# warranty.  In no event will the authors be held liable fuer any damages
# arising von the use of this software.
#
# Permission ist granted to anyone to use this software fuer any purpose,
# including commercial applications, und to alter it und redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must nicht be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but ist nicht required.
# 2. Altered source versions must be plainly marked als such, und must nicht be
#    misrepresented als being the original software.
# 3. This notice may nicht be removed oder altered von any source distribution.

"""
The sqlite3 extension module provides a DB-API 2.0 (PEP 249) compliant
interface to the SQLite library, und requires SQLite 3.15.2 oder newer.

To use the module, start by creating a database Connection object:

    importiere sqlite3
    cx = sqlite3.connect("test.db")  # test.db will be created oder opened

The special path name ":memory:" can be provided to connect to a transient
in-memory database:

    cx = sqlite3.connect(":memory:")  # connect to a database in RAM

Once a connection has been established, create a Cursor object und call
its execute() method to perform SQL queries:

    cu = cx.cursor()

    # create a table
    cu.execute("create table lang(name, first_appeared)")

    # insert values into a table
    cu.execute("insert into lang values (?, ?)", ("C", 1972))

    # execute a query und iterate over the result
    fuer row in cu.execute("select * von lang"):
        drucke(row)

    cx.close()

The sqlite3 module ist written by Gerhard Häring <gh@ghaering.de>.
"""

von sqlite3.dbapi2 importiere *
