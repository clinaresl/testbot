#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbtools.py
# Description: database access
# -----------------------------------------------------------------------------
#
# Started on  <Sun Aug 11 18:09:23 2013 Carlos Linares Lopez>
# -----------------------------------------------------------------------------
# Made by Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
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


# imports
# -----------------------------------------------------------------------------
import re               # compile, groups

import dbparser         # testbot parser utilities (lex and yacc)


# -----------------------------------------------------------------------------
# DBSpec
#
# this class provides services for accessing and interpreting the
# contents of database specifications
# -----------------------------------------------------------------------------
class DBSpec:
    """
    this class provides services for accessing and interpreting the contents of
    database specifications
    """

    def __init__(self, spec):
        """
        decodes the contents of a database specification
        """

        # copy the data
        self.data = spec

        # parse the given string
        parsed_string = dbparser.VerbatimDBParser ()
        parsed_string.run(spec)

        # and copy all definitions found by the parser
        self._tables = parsed_string._tables

        # create different lists for storing regexps and database tables. They
        # are also indexed in a dictionary by their name
        self._regexp = []
        self._regexpdict = {}
        self._db = []
        self._dbdict = {}
        self._snippet = []
        self._snippetdict = {}
        for itable in self._tables:
            if isinstance(itable, dbparser.DBRegexp):
                self._regexp.append(itable)
                self._regexpdict[itable.get_name()] = itable
            elif isinstance(itable, dbparser.DBTable):
                self._db.append(itable)
                self._dbdict[itable.get_name()] = itable
            elif isinstance(itable, dbparser.DBSnippet):
                self._snippet.append(itable)
                self._snippetdict[itable.get_name()] = itable
            else:
                raise NotImplementedError ('Unknown table type')

        # initialize the position of the first table to return
        self._current = 0


    def __iadd__(self, itable):
        """
        adds a new table/regexp to this specification
        """

        # first, add it to the right list of tables
        if isinstance(itable, dbparser.DBRegexp):
            self._regexp.append(itable)
        elif isinstance(itable, dbparser.DBTable):
            self._db.append(itable)
        else:
            raise NotImplementedError ('Unknown table type')

        # second, add it also to the generic list of tables
        self._tables.append(itable)

        return self


    def __iter__(self):
        '''defines the simplest case for iterators'''

        return self


    def __next__(self):
        """
        returns the current test case
        """

        if self._tables:

            if self._current >= len (self._tables):
                self._current = 0
                raise StopIteration

            self._current += 1
            return self._tables[self._current - 1]

        # in case there are no tables, stop the iteration
        raise StopIteration


    def __len__(self):
        """
        return the number of data tables/regexp in this instance
        """

        return len(self._tables)


    def __str__(self):
        """
        Informal string of this instance
        """

        # this instance might containt database table and/or snippets and/or
        # regexp specifications. Other cases should raise a not implemented
        # error
        stdb = str()
        stregexp = str()
        stsnippet = str()

        # database tables, regexps and snippets are processed separately to be
        # shown altogether in different groups: first, snippets, second, regexp;
        # next, database tables
        for itable in self._tables:
            if isinstance(itable, dbparser.DBSnippet):
                stsnippet += str(itable) + '\n'
            elif isinstance(itable, dbparser.DBRegexp):
                stregexp += str(itable) + '\n'
            elif isinstance(itable, dbparser.DBTable):
                stdb += str(itable) + '\n'
            else:
                raise NotImplementedError('Unknown table type')

        # finally, return the regexp and database specs one after the other. In
        # case there are regexps, then show them before. Otherwise, skip that
        # part (this is just to prevent that two newlines are shown when
        # printing the contents of this session)
        if stregexp:
            return '\n' + stregexp + '\n' + stsnippet + '\n' + stdb

        return '\n' + stsnippet + '\n' + stdb


    def get_db(self, name=None):
        """
        return a list with all database tables found in this instance. Every
        database table is an instance of dbparser.DBTable

        If a specific name is given then the database table with that name is
        returned or None if it does not exist
        """

        if not name:
            return self._db

        if name not in self._dbdict:
            return None

        return self._dbdict[name]


    def get_regexp(self, name=None):
        """
        return a list with all regexp found in this instance. Every regexp is an
        instance of dbparser.DBRegexp.

        If a specific name is given then the regexp with that name is returned
        or None if it does not exist
        """

        if not name:
            return self._regexp
        if name not in self._regexpdict:
            return None

        return self._regexpdict[name]


    def get_snippet(self, name=None):
        """
        return a list with all snippets found in this instance. Every snippet is
        an instance of dbparser.DBSnippet.

        If a specific name is given then the snippet with that name is returned
        or None if it does not exist
        """

        if not name:
            return self._snippet
        if name not in self._snippetdict:
            return None

        return self._snippetdict[name]


    def isregexp(self, name):
        """
        return true if and only if the given string is the name of a regexp and
        false otherwise
        """

        for iregexp in self._regexp:
            if iregexp.get_name() == name:
                return True

        return False


    def verify_regexps(self):
        """
        Verify that all regexps referenced within different database tables
        exist and have the specified groups. It returns true if everything went
        fine and an exception is raised otherwise
        """

        def _seek_regexp(name):
            """
            returns an instance of DBRegexp if there is one with the specified
            name and None otherwise
            """

            # in case the regexp is found within the current collection of
            # regexps, return it
            for iregexp in self._regexp:
                if iregexp.get_name() == name:
                    return iregexp

            # otherwise, return None
            return None


        def _seek_group (regexp, group):
            """
            returns the index to the specified group in the given regexp if it
            exists and -1 otherwise
            """

            # compile this regular expression and go over all its groups. If the
            # specified one exists, return its index
            compiled = re.compile (regexp.get_specification())
            if group in compiled.groupindex:
                return compiled.groupindex[group]

            # otherwise, return -1
            return -1


        # go over all columns of all database tables in this instance
        for itable in self._db:

            for icolumn in itable:

                # in case this is a regexp
                if icolumn.get_vartype() == dbparser.REGEXPNST:

                    # split the constituents of the variable field of this
                    # column into two different parts: the regexp name and the
                    # group
                    (name, group) = icolumn.get_variable().split('.')

                    # first, is there a regexp named after 'name'?
                    regexp = _seek_regexp(name)
                    if regexp:

                        # check if the given group exists in this regular
                        # expression
                        groupidx = _seek_group (regexp, group)
                        if groupidx < 0:
                            raise ValueError(" There is no group named '%s' in regexp '%s' but it is used in the specification of column '%s' in table '%s'" % (group, name, icolumn.get_identifier (), itable.get_name ()))

                    else:
                        raise ValueError(" There is no regexp named '%s' but it was found in the specification of column '%s' in table '%s'" % (name, icolumn.get_identifier (), itable.get_name ()))

        # return true if everything went fine
        return True


# -----------------------------------------------------------------------------
# DBVerbatim
#
# this class provides services for accessing and interpreting the contents of a
# string ---it is just an alias of DBSpec
# -----------------------------------------------------------------------------
class DBVerbatim(DBSpec):

    """
    this class provides services for accessing and interpreting the contents of
    a string ---it is just an alias of DBSpec
    """

    def __init__(self, data):
        """
        decodes the contents given in data
        """

        # simply invoke the constructor of the base class with the contents
        # given in data
        super(DBVerbatim, self).__init__(spec=data)


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

        # store the filename
        self.filename = filename

        # and now process its contents
        with open(filename) as stream:

            # simply invoke the constructor of the base class with the
            # contents of the file
            super(DBFile, self).__init__(spec=stream.read ())



# Local Variables:
# mode:python
# fill-column:79
# End:
