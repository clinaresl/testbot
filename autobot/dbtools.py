#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# dbtools.py
# Description: database access
# -----------------------------------------------------------------------------
#
# Started on  <Sun Aug 11 18:09:23 2013 Carlos Linares Lopez>
# Last update <sábado, 04 enero 2014 01:39:38 Carlos Linares Lopez (clinares)>
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
database access
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import dbparser         # testbot parser utilities (lex and yacc)


# -----------------------------------------------------------------------------
# DBIter
#
# returns an iterator of all tables found in the given DBSpec, even if
# it is empty
# -----------------------------------------------------------------------------
class DBIter(object):

    """
    returns an iterator of all tables found in the given DBSpec, even
    if it is empty
    """

    def __init__ (self, dbspec):
        """
        initialization
        """

        # initialize the position of the first test case to return
        self._current = 0

        # copy the database specification
        self._dbspec = dbspec


    def __iter__ (self):
        """
        (To be included in iterators)
        """

        return self

    
    def next (self):
        """
        returns the current test case
        """

        if len (self._dbspec._tables):

            if self._current >= len (self._dbspec._tables):
                raise StopIteration
            else:
                self._current += 1
                return self._dbspec._tables [self._current - 1]

        # in case there are no tables, just return the empty list
        else:

            return []


# -----------------------------------------------------------------------------
# DBSpec
#
# this class provides services for accessing and interpreting the
# contents of database specifications
# -----------------------------------------------------------------------------
class DBSpec(object):
    """
    this class provides services for accessing and interpreting the
    contents of database specifications
    """

    def __init__ (self, spec):
        """
        decodes the contents of a database specification
        """

        # parse the given string
        p = dbparser.VerbatimDBParser ()
        p.run (spec)

        # and copy all tables
        self._tables = p._tables


    def __iadd__ (self, itable):
        """
        adds a new table to this specification
        """

        self._tables.append (itable)

        return self


    def __iter__ (self):
        """
        return an iterator over the tables defined for this database
        specification
        """

        return DBIter (self)

    
    def __len__ (self):
        """
        return the number of data tables in this instance
        """

        return len (self._tables)


    def __str__ (self):
        """
        Informal string of this instance
        """

        # just insert a newline char between two successive string
        # representations
        return reduce (lambda x,y:x+'\n'+y,
                       [dbparser.DBTable.__str__ (z) for z in self._tables])


# -----------------------------------------------------------------------------
# DBFile
#
# this class provides services for accessing and interpreting the
# contents of test specification files
# -----------------------------------------------------------------------------
class DBFile(DBSpec):

    """
    this class provides services for accessing and interpreting the
    contents of database specification files
    """

    def __init__ (self, filename):
        """
        decodes the contents of a database specification file
        """

        self._filename = filename

        with open (filename) as stream:

            # simply invoke the constructor of the base class with the
            # contents of the file
            super (DBFile, self).__init__(spec=stream.read ())


    def get_filename (self):
        """
        returns the filename of the database specification
        """

        return self._filename



# Local Variables:
# mode:python
# fill-column:80
# End: