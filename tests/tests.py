#!/usr/bin/env python
##############################################################################
# Copyright (c) 2009-2011 Hajime Nakagami<nakagami@gmail.com>
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
#
# Python DB-API 2.0 module for Firebird. 
##############################################################################
import os,sys
sys.path.append('./../')
import firebirdsql
from firebirdsql import *

def debug_print(msg):
    print(msg)

if __name__ == '__main__':
    if sys.platform in ('win32', 'darwin'):
        fbase = os.path.abspath('.') + '/test'
    else:
        import tempfile
        fbase = tempfile.mktemp()
    TEST_HOST = 'localhost'
    TEST_PORT = 3050
    TEST_DATABASE = fbase + '.fdb'
    TEST_DSN = TEST_HOST + '/' + str(TEST_PORT) + ':' + TEST_DATABASE
    print('dsn=', TEST_DSN)
    TEST_USER = 'sysdba'
    TEST_PASS = 'masterkey'
    conn = firebirdsql.create_database(dsn=TEST_DSN,
                        user=TEST_USER, password=TEST_PASS, page_size=2<<13)
    conn.cursor().execute('''
        CREATE TABLE foo (
            a INTEGER NOT NULL,
            b VARCHAR(30) NOT NULL UNIQUE,
            c VARCHAR(1024),
            d DECIMAL(16,3) DEFAULT -0.123,
            e DATE DEFAULT '1967-08-11',
            f TIMESTAMP DEFAULT '1967-08-11 23:45:01',
            g TIME DEFAULT '23:45:01',
            h BLOB SUB_TYPE 0, 
            i DOUBLE PRECISION DEFAULT 0.0,
            j FLOAT DEFAULT 0.0,
            PRIMARY KEY (a),
            CONSTRAINT CHECK_A CHECK (a <> 0)
        )
    ''')
    conn.commit()

    cur = conn.cursor()
    cur.execute("select * from foo")
    assert cur.fetchone() is None
    cur.close()

    cur = conn.cursor()
    cur.execute("select a as alias_name from foo")
    assert cur.description[0][0] == 'ALIAS_NAME'
    cur.close()

    # 3 records insert
    conn.cursor().execute("insert into foo(a, b, c) values (1, 'a', 'b')")
    conn.cursor().execute("""insert into foo(a, b, c, e, g, i, j) 
        values (2, 'A', 'B', '1999-01-25', '00:00:01', 0.1, 0.1)""")
    conn.cursor().execute("""insert into foo(a, b, c, e, g, i, j) 
        values (3, 'X', 'Y', '2001-07-05', '00:01:02', 0.2, 0.2)""")

    # 1 record insert and rollback to savepoint
    cur = conn.cursor()
    conn.savepoint('abcdefghijklmnopqrstuvwxyz')
    cur.execute("""insert into foo(a, b, c, e, g, i, j) 
        values (4, 'x', 'y', '1967-05-08', '00:01:03', 0.3, 0.3)""")
    conn.rollback(savepoint='abcdefghijklmnopqrstuvwxyz')

    conn.cursor().execute("update foo set c='Hajime' where a=1")
    conn.cursor().execute("update foo set c=? where a=2", ('Nakagami', ))
    conn.commit()

    cur = conn.cursor()
    cur.execute("select * from foo where c=?", ('Nakagami', ))
    len(cur.fetchall()) == 1
    cur.close()

    cur = conn.cursor()
    cur.execute("select * from foo")
    assert not cur.fetchone() is None
    assert not cur.fetchone() is None
    assert not cur.fetchone() is None
    assert cur.fetchone() is None
    cur.close()

    cur = conn.cursor()
    try:
        conn.cursor().execute("insert into foo(a, b, c) values (1, 'a', 'b')")
    except firebirdsql.IntegrityError:
        pass
    try:
        conn.cursor().execute("bad sql")
    except firebirdsql.OperationalError:
        e = sys.exc_info()[1]
        assert e.sql_code == -104

    cur = conn.cursor()
    cur.execute("select * from foo")
    print(cur.description)
    for c in cur.fetchall():
        print(c)
    cur.execute("select * from foo")
    for r in cur.fetchallmap():
        print(r)
        for key in r:
            print (key, r[key])
    cur.execute("select * from foo")
    conn.close()

    conn = firebirdsql.connect(host=TEST_HOST, database=TEST_DATABASE,
                        port=TEST_PORT, user=TEST_USER, password=TEST_PASS)

    # db_info
    print('isc_info_ods_version =', conn.db_info(isc_info_ods_version))
    print('isc_info_base_level =', conn.db_info(isc_info_base_level))
    print('isc_info_db_id =', conn.db_info(isc_info_db_id))
    print('isc_info_implementation =', conn.db_info(isc_info_implementation))
    print('isc_info_firebird_version =', conn.db_info(isc_info_firebird_version))
    print('isc_info_user_names =', conn.db_info(isc_info_user_names))
    print('isc_info_reqd_idx_count =', conn.db_info(isc_info_read_idx_count))
    print('isc_info_creation_date =', conn.db_info(isc_info_creation_date))

    requests = [isc_info_ods_version, 
                isc_info_user_names,
                isc_info_ods_minor_version,
    ]
    print(conn.db_info(requests))

    conn.set_isolation_level(firebirdsql.ISOLATION_LEVEL_SERIALIZABLE)
    cur = conn.cursor()
    cur.execute("select * from foo")
    print(cur.description)
    for c in cur.fetchall():
        print(c)
    conn.close()

    # drop database
    conn = firebirdsql.connect(host=TEST_HOST, database=TEST_DATABASE,
                        port=TEST_PORT, user=TEST_USER, password=TEST_PASS)
    conn.drop_database()

