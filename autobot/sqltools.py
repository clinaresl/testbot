#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# sqltools.py
# Description: read/write access to sqlite3 databases
# -----------------------------------------------------------------------------
#
# Started on  <Wed Apr 17 10:13:28 2013 Carlos Linares Lopez>
# Last update <viernes, 03 enero 2014 19:58:49 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id::                                                                      $
# $Date::                                                                    $
# $Revision::                                                                $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@psyche>
#

# -----------------------------------------------------------------------------
#     This file is part of testbot
#
#     testbot is free software: you can redistribute it and/or modify it under
#     the terms of the GNU General Public License as published by the Free
#     Software Foundation, either version 3 of the License, or (at your option)
#     any later version.
#
#     testbot is distributed in the hope that it will be useful, but WITHOUT ANY
#     WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#     FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#     details.
#
#     You should have received a copy of the GNU General Public License along
#     with testbot.  If not, see <http://www.gnu.org/licenses/>.
#
#     Copyright Carlos Linares Lopez, 2014
# -----------------------------------------------------------------------------

"""
read/write access to sqlite3 databases
"""

__version__  = '1.0'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import datetime         # date/time management
import re               # regexp
import sqlite3          # sql lite dbs


# -----------------------------------------------------------------------------
# sqldb
#
# this class wraps read/write access to sqlite3 databases
# -----------------------------------------------------------------------------
class sqldb(object):

    """
    this class wraps read/write access to sqlite3 databases
    """

    def __init__ (self, dbname):
        """
        connects to a sqlite3 database
        """

        # store the name of the database
        self._dbname = dbname

        # connect to this database
        self._conn = sqlite3.connect (dbname)
        
        # and get a cursor
        self._cursor = self._conn.cursor ()


    def execute (self, command):
        """
        executes the given command in the current cursor
        """

        self._cursor.execute (command)


    def fetchone (self):
        """
        fetches the next row from the current cursor
        """

        return self._cursor.fetchone ()


    def fetchall (self):
        """
        fetches all rows from the current cursor
        """

        return self._cursor.fetchall ()


    def find (self, table):
        """
        return True if table exists in the current database and false otherwise
        """

        # query the sqlite master the names of all tables
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # and now return whether the specified table exists or not
        return (table,) in self._cursor.fetchall ()


    def close (self):
        """
        commits changes and closes the connection
        """

        self._conn.commit ()
        self._conn.close ()


# -----------------------------------------------------------------------------
# dbtest
#
# this class wraps read/write access to sqlite3 databases for storing and
# retrieving information of various automated tests
# -----------------------------------------------------------------------------
class dbtest(sqldb):

    """
    this class wraps read/write access to sqlite3 databases for storing and
    retrieving information of various automated tests
    """

    def __init__ (self, dbname):
        """
        create/connect a test db
        """

        # invoke the parent's constructor
        sqldb.__init__ (self, dbname)


    def create_table (self, dbtable):
        """
        creates a table with the name and columns specified in dbtable (DBTable)
        """

        # create the sql command
        cmdline = 'CREATE TABLE ' + dbtable.get_name () + ' ('
        for icolumn in range (0, len (dbtable) - 1):
            cmdline += dbtable._columns[icolumn].get_identifier () + ' '
            cmdline += dbtable._columns[icolumn].get_type () + ', '

        cmdline += dbtable._columns[len (dbtable) - 1].get_identifier () + ' '
        cmdline += dbtable._columns[len (dbtable) - 1].get_type () + ')'

        # and now, create the table
        self._cursor.execute (cmdline)
        

    def insert_data (self, dbtable, data):
        """
        it stores data in the table qualified by dbtable (DBTable)
        """

        if (len (data) > 0):

            # populate the table with the given data
            specline = "?, " * (len (data[0]) - 1)
            cmdline = "INSERT INTO %s VALUES (%s)" % (dbtable.get_name (), specline + '?')
            self._cursor.executemany (cmdline, data)


        
# Local Variables:
# mode:python
# fill-column:80
# End:
