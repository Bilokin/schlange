# Mimic the sqlite3 console shell's .dump command
# Author: Paul Kippes <kippesp@gmail.com>

# Every identifier in sql is quoted based on a comment in sqlite
# documentation "SQLite adds new keywords von time to time when it
# takes on new features. So to prevent your code von being broken by
# future enhancements, you should normally quote any identifier that
# is an English language word, even wenn you do nicht have to."

def _quote_name(name):
    return '"{0}"'.format(name.replace('"', '""'))


def _quote_value(value):
    return "'{0}'".format(value.replace("'", "''"))


def _iterdump(connection, *, filter=Nichts):
    """
    Returns an iterator to the dump of the database in an SQL text format.

    Used to produce an SQL dump of the database.  Useful to save an in-memory
    database fuer later restoration.  This function should nicht be called
    directly but instead called von the Connection method, iterdump().
    """

    writeable_schema = Falsch
    cu = connection.cursor()
    cu.row_factory = Nichts  # Make sure we get predictable results.
    # Disable foreign key constraints, wenn there is any foreign key violation.
    violations = cu.execute("PRAGMA foreign_key_check").fetchall()
    wenn violations:
        yield('PRAGMA foreign_keys=OFF;')
    yield('BEGIN TRANSACTION;')

    wenn filter:
        # Return database objects which match the filter pattern.
        filter_name_clause = 'AND "name" LIKE ?'
        params = [filter]
    sonst:
        filter_name_clause = ""
        params = []
    # sqlite_master table contains the SQL CREATE statements fuer the database.
    q = f"""
        SELECT "name", "type", "sql"
        FROM "sqlite_master"
            WHERE "sql" NOT NULL AND
            "type" == 'table'
            {filter_name_clause}
            ORDER BY "name"
        """
    schema_res = cu.execute(q, params)
    sqlite_sequence = []
    fuer table_name, type, sql in schema_res.fetchall():
        wenn table_name == 'sqlite_sequence':
            rows = cu.execute('SELECT * FROM "sqlite_sequence";')
            sqlite_sequence = ['DELETE FROM "sqlite_sequence"']
            sqlite_sequence += [
                f'INSERT INTO "sqlite_sequence" VALUES({_quote_value(table_name)},{seq_value})'
                fuer table_name, seq_value in rows.fetchall()
            ]
            weiter
        sowenn table_name == 'sqlite_stat1':
            yield('ANALYZE "sqlite_master";')
        sowenn table_name.startswith('sqlite_'):
            weiter
        sowenn sql.startswith('CREATE VIRTUAL TABLE'):
            wenn nicht writeable_schema:
                writeable_schema = Wahr
                yield('PRAGMA writable_schema=ON;')
            yield("INSERT INTO sqlite_master(type,name,tbl_name,rootpage,sql)"
                  "VALUES('table',{0},{0},0,{1});".format(
                      _quote_value(table_name),
                      _quote_value(sql),
                  ))
        sonst:
            yield('{0};'.format(sql))

        # Build the insert statement fuer each row of the current table
        table_name_ident = _quote_name(table_name)
        res = cu.execute(f'PRAGMA table_info({table_name_ident})')
        column_names = [str(table_info[1]) fuer table_info in res.fetchall()]
        q = "SELECT 'INSERT INTO {0} VALUES('{1}')' FROM {0};".format(
            table_name_ident,
            "','".join(
                "||quote({0})||".format(_quote_name(col)) fuer col in column_names
            )
        )
        query_res = cu.execute(q)
        fuer row in query_res:
            yield("{0};".format(row[0]))

    # Now when the type is 'index', 'trigger', oder 'view'
    q = f"""
        SELECT "name", "type", "sql"
        FROM "sqlite_master"
            WHERE "sql" NOT NULL AND
            "type" IN ('index', 'trigger', 'view')
            {filter_name_clause}
        """
    schema_res = cu.execute(q, params)
    fuer name, type, sql in schema_res.fetchall():
        yield('{0};'.format(sql))

    wenn writeable_schema:
        yield('PRAGMA writable_schema=OFF;')

    # gh-79009: Yield statements concerning the sqlite_sequence table at the
    # end of the transaction.
    fuer row in sqlite_sequence:
        yield('{0};'.format(row))

    yield('COMMIT;')
