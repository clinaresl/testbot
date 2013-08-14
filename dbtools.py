#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# dbtools.py
# Description: read/write access to sqlite3 databases
# -----------------------------------------------------------------------------
#
# Started on  <Wed Apr 17 10:13:28 2013 Carlos Linares Lopez>
# Last update <Wednesday, 24 July 2013 09:25:52 Carlos Linares Lopez (clinares)>
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


# globals
# -----------------------------------------------------------------------------
DATAPREFIX = 'data_'
DATAREGEXP = 'data\_(?P<name>.*)'

# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# spacify
#
# substitute underscores by blanks
# -----------------------------------------------------------------------------
def spacify (s):
    """
    substitute underscores by blanks
    """

    return ''.join (map (lambda x:' ' if (x == '_') else x, s))


# -----------------------------------------------------------------------------
# despacify
#
# substitute blanks by underscores
# -----------------------------------------------------------------------------
def despacify (s):
    """
    substitute blanks by underscores
    """

    return ''.join (map (lambda x:'_' if (x == ' ') else x, s))


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


    def create_version_table (self):
        """
        creates the version table
        """

        # first, create the version table in case it does not exist
        if (not self.find ('version')):
            self._cursor.execute ('''CREATE TABLE version 
                                     (progname text, version text, revision text, date text)''')
        

    def insert_version_data (self, progname, version, revision, date):
        """
        stores all the version data given in the parameters
        """

        # populate the admin table
        self._cursor.execute ("INSERT INTO version VALUES (?, ?, ?, ?)", 
                              (progname, version, revision, date))

        
    def create_admin_table (self):
        """
        creates the admin table
        """

        # first, create the admin table in case it does not exist
        if (not self.find ('admin')):
            self._cursor.execute ('''CREATE TABLE admin (filename text, solver text, delay integer, time integer, memory integer)''')
        

    def insert_admin_data (self, filename, solver, check, time, memory):
        """
        stores all the admin data given in the parameters
        """

        # populate the admin table
        self._cursor.execute ("INSERT INTO admin VALUES (?, ?, ?, ?, ?)", 
                              (filename, solver, check, time, memory))

        
    def create_systime_table (self):
        """
        creates the systime table for storing the CPU time indexed by wall-clock
        time
        """

        if (not self.find ('sys_time')):
            self._cursor.execute ('''CREATE TABLE sys_time
                                     (id text, wctime real, cputime real)''')
        

    def create_sysvsize_table (self):
        """
        creates the systime table for storing the memory usage indexed by wall-clock
        time
        """

        if (not self.find ('sys_vsize')):
            self._cursor.execute ('''CREATE TABLE sys_vsize
                                     (id text, wctime real, vsize real)''')
        

    def create_sysprocs_table (self):
        """
        creates the sysprocs table for storing the current number of processes
        indexed by wall-clock time
        """

        # systime
        if (not self.find ('sys_procs')):
            self._cursor.execute ('''CREATE TABLE sys_procs
                                     (id text, wctime real, numprocs integer)''')
        

    def create_systhreads_table (self):
        """
        creates the systhreads table for storing the current number of threads
        indexed by wall-clock time
        """

        # systime
        if (not self.find ('sys_threads')):
            self._cursor.execute ('''CREATE TABLE sys_threads
                                     (id text, wctime real, numthreads integer)''')
        

    def create_systimeline_table (self):
        """
        creates the systimeline table for storing the start/end time of every
        process
        """

        # systime
        if (not self.find ('sys_timeline')):
            self._cursor.execute ('''CREATE TABLE sys_timeline
                                     (id text, 
pid integer, cmdline string, start string, end string)''')
        

    def create_sysfd_table (self):
        """
        creates the sysfd table for storing information about files
        """

        # sysfd
        if (not self.find ('sys_fd')):
            self._cursor.execute ('''CREATE TABLE sys_fd
                                     (id text, pid integer, path string, uid string, gid string)''')
        

    def create_sysfd_atime_table (self):
        """
        creates the sysfd_atime table for storing the atime of every file
        """

        # sysfd_atime
        if (not self.find ('sys_fd_atime')):
            self._cursor.execute ('''CREATE TABLE sys_fd_atime
                                     (id text, pid integer, path string, atime string)''')
        

    def create_sysfd_mtime_table (self):
        """
        creates the sysfd_mtime table for storing the mtime of every file
        """

        # sysfd_mtime
        if (not self.find ('sys_fd_mtime')):
            self._cursor.execute ('''CREATE TABLE sys_fd_mtime
                                     (id text, pid integer, path string, mtime string)''')
        

    def create_sysfd_ctime_table (self):
        """
        creates the sysfd_ctime table for storing the ctime of every file
        """

        # sysfd_ctime
        if (not self.find ('sys_fd_ctime')):
            self._cursor.execute ('''CREATE TABLE sys_fd_ctime
                                     (id text, pid integer, path string, ctime string)''')
        

    def create_sysfd_size_table (self):
        """
        creates the sysfd_size table for recording how the size of a file
        evolves over time
        """

        # sysfd_ctime
        if (not self.find ('sys_fd_size')):
            self._cursor.execute ('''CREATE TABLE sys_fd_size
                                     (id text, pid integer, path string, time string, size integer)''')
        

    def insert_sysdata (self, acronym, values):
        """
        inserts the given values into the table specified by acronym
        """

        if (values):
            
            # compute the arity of the tuples
            specline = "?, " * (len (values [0]) - 1)
            cmdline = "INSERT INTO sys_%s VALUES (%s)" % (acronym,
                                                          specline + '?')
            self._cursor.executemany (cmdline, values)
        

    def create_time_table (self):
        """
        creates the time table
        """

        # first, create the time table in case it does not exist
        if (not self.find ('time')):
            self._cursor.execute ('''CREATE TABLE time 
                                     (starttime text, endtime text, elapsed_seconds real)''')
        

    def insert_time_data (self, starttime, endtime):
        """
        stores all the time data given in the parameters
        """

        # compute the elapsedtime
        delta = endtime-starttime

        # populate the admin table
        self._cursor.execute ("INSERT INTO time VALUES (?, ?, ?)", (starttime, endtime,
                                                                    delta.total_seconds ())) 

        
    def create_test_table (self):
        """
        creates the test table
        """

        # first, create the test table in case it does not exist
        if (not self.find ('test')):
            self._cursor.execute ('''CREATE TABLE test 
                                     (id text, args text)''')
        

    def insert_test_data (self, cases):
        """
        stores all the test data given in the parameters
        """

        # populate the test table with all the given cases
        if (cases):
            self._cursor.executemany ("INSERT INTO test VALUES (?, ?)", cases) 

        
    def select_metadata (self, metaname):
        """
        returns a list with tuples containing all rows of the specified name
        """

        # query sqlite3 to retrieve all data in case the table exists
        if (self.find (metaname)):
            command = "SELECT * FROM %s;" % metaname
            self._cursor.execute(command)

            # and now return the data - note that fetchall is used though in
            # some cases there should be only one line
            return self._cursor.fetchall ()

        # and otherwise return the empty list
        return []


    def create_data_table (self, table):
        """
        creates the specified data table
        """

        # initialization
        tablename = DATAPREFIX + despacify (table)

        # first, create the data table in case it does not exist
        if (not self.find (tablename)):
            command = "CREATE TABLE %s (id text, value real)" % tablename
            self._cursor.execute (command)
        

    def insert_data (self, table, data):
        """
        it creates the specified table in case it does not exist and stores data
        in it. 'data' consists of a list of tuples and it is mandatory that the
        table has as many cols as elements there are in each tuple
        """

        # initialization
        tablename = DATAPREFIX + despacify (table)

        # now, just iterate through all data and store all tuples into the table
        for idata in data:

            command = "INSERT INTO %s VALUES (%s, %f)" % (tablename, idata[0], idata[1])
            self._cursor.execute (command)
            

    def select_data (self, table):
        """
        returns a list with tuples containing all rows of the specified table
        """

        # initialization
        tablename = DATAPREFIX + despacify (table)

        # query sqlite3 to retrieve all data in case the table exists
        if (self.find (tablename)):
            command = "SELECT * FROM %s;" % tablename
            self._cursor.execute(command)

            # and now return the data
            return self._cursor.fetchall ()

        # and otherwise return the empty list
        return []


    def get_data_tables (self):
        """
        retrieves the names of all data tables
        """

        # query the sqlite master the names of all tables
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # and now, process the result leaving out those tables that are not
        # prefixed with DATAPREFIX
        result = []
        for itable in self._cursor.fetchall ():

            # match the table name with the data regexp
            m = re.match (DATAREGEXP, itable[0])
            if (m):
                result.append (spacify (m.group ('name')))
                
        # and now return whether the specified table exists or not
        return result



# Local Variables:
# mode:python
# fill-column:80
# End:
