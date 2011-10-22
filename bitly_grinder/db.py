#!/usr/bin/env python
# ---*< bitly_grinder/db.py >*------------------------------------------------
# Copyright (C) 2011 st0w
# 
# This module is part of bit.ly grinder and is released under the MIT License.
# Please see the LICENSE file for details.

"""DB-related functions

Created on Oct 22, 2011

"""
# ---*< Standard imports >*---------------------------------------------------
import json
import sys
try:
    # First try pysqlie2, assuming if it exists, it is newer
    from pysqlite2 import dbapi2 as sqlite3
except:
    import sqlite3

# ---*< Third-party imports >*------------------------------------------------
from dictshield.base import DictPunch

# ---*< Local imports >*------------------------------------------------------
from models import BitlyUrl

# ---*< Initialization >*-----------------------------------------------------
sqlite3.register_converter('json', json.loads)

# ---*< Code >*---------------------------------------------------------------
def init_db_conn(**kwargs):
    db_conn = sqlite3.connect('bitly-grinder.db',
                              detect_types=sqlite3.PARSE_DECLTYPES
                              | sqlite3.PARSE_COLNAMES)
    db_conn.row_factory = sqlite3.Row # fields by names
    setup_db(db_conn)

    return db_conn


def setup_db(db):
    """Creates SQLite tables if needed
    
    """

    db.execute('''
        CREATE TABLE IF NOT EXISTS
        urls(
            url TEXT PRIMARY KEY,
            updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status INTEGER,
            data json
        )
    ''')


def get_results(db, status=None):
    """Returns a list of all results
    
    :param db: `SQLite3` handle to DB with results
    :param status: (optional) `int` of result status codes to show
    :rtype: `list` of resulting `BitlyUrl` objects
    
    """
    if status:
        try:
            status = int(status)
        except ValueError:
            status = None

    if status:
        curs = db.execute('''
            SELECT data FROM urls WHERE status=? 
        ''', (status,))
    else:
        curs = db.execute('''
            SELECT data FROM urls
        ''')

    rows = curs.fetchall()
    res = []

    for row in rows:
        row = row['data']
        bitly = BitlyUrl(**row)

        try:
            bitly.validate()
        except DictPunch, dp:
            sys.stderr.write('DictShield error: %s\nData: %s' %
                             (dp, bitly.to_python()))
        else:
            res.append(bitly)

    return res


def save_result(db, data, commit=True):
    """Saves a result into the SQLite DB
    
    :param db: `SQLite3` DB handle
    :param data: `BitlyUrl` object to save
    :param commit: `Boolean` indicating whether or not to commit.  If
                   performing a large batch of operations, it's
                   significantly quicker to set this to False and then
                   just commit it yourself. 
    :rtype: None 
    
    """
    if not isinstance(data, BitlyUrl):
        raise ValueError('data passed to save_results() must be of type'
                         'BitlyUrl')

    curs = db.cursor()
    data.validate()

    curs.execute('''
        INSERT OR REPLACE INTO urls (url, status, data)
        VALUES (?, ?, ?)
    ''', (data.base_url, data.status, data.to_json()))

    if commit:
        db.commit()



__all__ = (init_db_conn, save_result)

