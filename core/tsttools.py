#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tsttools.py
# Description: test tools
# -----------------------------------------------------------------------------
#
# Started on  <Sat May  4 01:37:54 2013 Carlos Linares Lopez>
# Last update <domingo, 26 abril 2015 22:52:07 Carlos Linares Lopez (clinares)>
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
test tools
"""

__version__  = '1.0'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import re                       # regexp

import tbparser                 # testbot parser utilities (lex and yacc)

from collections import defaultdict


# functions
# -----------------------------------------------------------------------------
def partition (string, sep="""\"[^\"]+\"|'[^']+'"""):
    """
    partition the given string according to the given separator (which might be
    any valid regexp that represents a couple of grouping characters such as the
    single|double quotes, parenthesis, brackets, etc.)
    """

    def _split_aux_ (l):
        """
        creates a unique list that joins all the lists that result from
        splitting all the items in l
        """

        return reduce (lambda x,y:x+y,                  # operation: join
                       map (lambda x:x.split (),        # operation: split
                            l))

    def _partition_aux_ (string, groups, rest):
        """
        partitions the original string in a list whose items are taken from
        groups and rest in the same order they appear in string. Whitespaces are
        automatically removed in all items of the final list. Items in rest are
        split (using whitespaces) but items in groups are copied as is
        """

        # case bases - one of the lists is empty
        if not groups:
            return _split_aux_ (rest)

        if not rest:
            return groups

        # general case - the beginning of the string should match either the
        # first item in groups or the first item in rest (which are known to contain
        # items)
        if re.match (groups[0], string):
            return ([groups[0]] +
                    _partition_aux_ (string[len (groups[0]):], groups[1:], rest))

        if re.match (rest[0], string):
            return (rest[0].split () +
                    _partition_aux_ (string[len (rest[0]):], groups, rest[1:]))

        # impossible case - paranoid checking
        print("""
 Fatal Error in _partition_aux
 string: %s
 groups: %s
 rest: %s""" % (string, groups, rest))
        raise ValueError

    # split the string in two different parts: groups matching the separators
    # and the rest
    groups = re.findall (sep, string)
    rest   = re.split   (sep, string)

    # now, add items from one list and the other in the same order
    return _partition_aux_ (string, groups, rest)


# -----------------------------------------------------------------------------
# TstIter
#
# returns an iterator of all the cases found in the given TstSpec, even if it is
# empty
# -----------------------------------------------------------------------------
class TstIter(object):

    """
    returns an iterator of all the cases found in the given TstSpec, even if it
    is empty
    """

    def __init__ (self, tstspec):
        """
        initialization
        """

        # initialize the position of the first test case to return
        self._current = 0

        # copy the test specification
        self._tstspec = tstspec


    def __iter__ (self):
        """
        (To be included in iterators)
        """

        return self


    def next (self):
        """
        returns the current test case
        """

        if len (self._tstspec._tstdefs):

            if self._current >= len (self._tstspec._tstdefs):
                raise StopIteration
            else:
                self._current += 1
                return self._tstspec._tstdefs [self._current - 1]

        # a particularly interesting case is whether this test case is
        # empty. Since solvers can be also invoked without any parameters this
        # should be allowed
        else:

            return []


# -----------------------------------------------------------------------------
# TstCase
#
# this class provides the synthetic definition of a single test case
# -----------------------------------------------------------------------------
class TstCase(object):

    """
    this class provides the synthetic definition of a single test case
    """

    def __init__ (self, index, args):
        """
        initializes the definition of this test case. Both 'index' and 'args'
        are strings
        """

        # while it is absolutely legal to create a test case with no arguments
        # (so that any object of length zero or just None can be given), this is
        # internally represented as a list with the empty string
        if not args:
            args = ['']

        # store the index and definition of the test case
        (self._index, self._args) = (index, args)

    def __str__ (self):
        """
        Informal representation of this test case
        """

        # in case there are any args, process them
        if self._args:
            return self._index + ' ' + reduce (lambda x,y:x + ' ' + y,
                                               self._args)

        # otherwise, return just the empty string
        return ''


    def get_id (self):
        """
        returns the id of this test case
        """

        return self._index


    def get_args (self):
        """
        returns the definition of this test case
        """

        return self._args


    def get_directives (self):
        """
        returns a list with all the directives included in self._args

        In case the args contain the stdin redirection operator ('<') it is
        automatically discarded
        """

        # discard the stding redirection operator if necessary
        if '<' in self._args:
            args = self._args[0:self._args.index('<')]
        else:
            args = self._args
        
        # just look for all the (unique) occurrences of strings starting with an
        # arbitrary number of dashes and return a list with them but with dashes
        # removed
        return list (set (map (lambda x:x.lstrip ('-'),
                               filter (lambda y:re.match ("\-+",y), args))))


    def get_value (self, directive):
        """
        returns the values of the given directive. It explicitly takes into
        account the case of command lines that contain the same directive
        several times or the case of directives that contain an arbitrary number
        of values

        In case the args contain the stdin redirection operator ('<') it is
        automatically discarded
        """

        # discard the stding redirection operator if necessary
        if '<' in self._args:
            args = self._args[0:self._args.index('<')]
        else:
            args = self._args
        
        # take all the occurrences of this directive in the list of arguments
        # along with their position
        for iL in [jL for jL in zip (range(len(args)), args)
                   if re.match ("\-+"+directive+'$', jL[1])]:

            # while the next position is not a directive
            nextidx = iL[0]+1
            while (nextidx < len (args) and
                   not re.match ("^\-+", args [nextidx])):

                # return it
                try:
                    yield (args[nextidx])
                except EnvironmentError:
                    pass

                # and move to the next one
                nextidx += 1


    def get_values (self):
        """
        returns a dictionary with the value of all directives that contain, at
        least, a value. If more than one is available, they are all grouped
        within the same string. If no value is found, the null string is
        returned.

        In case the args contain the stdin redirection operator ('<') it is
        automatically discarded
        """

        # discard the stding redirection operator if necessary
        if '<' in self._args:
            args = self._args[0:self._args.index('<')]
        else:
            args = self._args
        
        # create the dictionary to return
        d = defaultdict (str)

        # take all the occurrences of all directives in the list of arguments
        # along with their position
        for iL in [jL for jL in zip (range(len(args)), args)
                   if re.match ("\-+", jL[1])]:

            # while the next position is not a directive
            nextidx = iL[0]+1
            while (nextidx < len (args) and
                   not re.match ("^\-+", args [nextidx])):

                # add white spaces in between if required, i.e., if something
                # was already writen
                if d[iL[1].lstrip ('-')]:
                    d [iL[1].lstrip ('-')] += ' '

                # add it to the list of values of this directive (with the
                # leading '-' removed)
                d [iL[1].lstrip ('-')] += args [nextidx]

                # and move to the next one
                nextidx += 1

            # otherwise, just add the empty string - this is useful for showing
            # directives without arguments
            else:
                d [iL[1].lstrip ('-')] += ''

        # and return the dictionary computed so far
        return d


# -----------------------------------------------------------------------------
# TstSpec
#
# this class provides services for accessing and interpreting the
# contents of test specifications
# -----------------------------------------------------------------------------
class TstSpec(object):

    """
    this class provides services for accessing and interpreting the contents of
    test specifications
    """

    def __init__ (self, spec):
        """
        decodes the contents of a test specification
        """

        # copy the data
        self.data = spec

        # parse the given string
        p = tbparser.VerbatimTBParser ()
        p.run (spec)

        # verify whether the user has requested explicitly to redirect the
        # stdin with the operator '<' in the arguments of any test case
        cmds = list()
        for itstcase in p.cmds:
            m=re.match(".*<\S", itstcase)
            if m:
                cmds.append (re.sub("<", "< ", itstcase))
            else:
                cmds.append(itstcase)

        # and now, create a TstCase for every command line parsed and qualify
        # them with a string that consits of three digits
        self._tstdefs = zip (map (lambda x,y:x%y,
                                  ["%03d"] * len (cmds),      # identifiers
                                  range (0, len (cmds))),
                             cmds)                            # command lines

        # create a TstCase with the information stored in every tuple
        # ---implemented in a different line to avoid getting a very confusing
        # one. The function partition is invoked to split the string into a list
        # where groups (embraced by single|double quotes) are preserved
        self._tstdefs = [TstCase (identifier, partition (cmdline))      # TstCase
                         for identifier, cmdline in self._tstdefs]


    def __iter__ (self):
        """
        return an iterator over the test cases defined in this specification
        """

        return TstIter (self)


    def __len__ (self):
        """
        return the number of tests cases in this instance
        """

        return len (self._tstdefs)


    def __str__ (self):
        """
        Informal string of this instance
        """

        # in case there are any directives
        if self._tstdefs:

            # just insert a newline char between two successive string
            # representations
            return reduce (lambda x,y:x+'\n'+y,
                           [TstCase.__str__ (z) for z in self._tstdefs])

        # otherwise, return the null str
        return ''


    def get_defs (self):
        """
        return a list of tuples of the form (idx, string of arguments)
        for every test case
        """

        return [(icase.get_id (), reduce (lambda x,y:x+' '+y, icase.get_args ()))
                for icase in self._tstdefs]


# -----------------------------------------------------------------------------
# TstVerbatim
#
# this class provides services for accessing and interpreting the contents of a
# string ---it is just an alias of TstSpec
# -----------------------------------------------------------------------------
class TstVerbatim(TstSpec):

    """
    this class provides services for accessing and interpreting the contents of
    a string ---it is just an alias of TstSpec
    """

    def __init__ (self, data):
        """
        decodes the contents given in data
        """

        # simply invoke the constructor of the base class with the contents
        # given in data
        super (TstVerbatim, self).__init__(spec=data)


# -----------------------------------------------------------------------------
# TstFile
#
# this class provides services for accessing and interpreting the
# contents of test specification files
# -----------------------------------------------------------------------------
class TstFile(TstSpec):

    """
    this class provides services for accessing and interpreting the
    contents of test specification files
    """

    def __init__ (self, filename):
        """
        decodes the contents of a test specification file
        """

        # store the filename
        self.filename = filename

        # and now process its contents
        with open (filename) as stream:

            # simply invoke the constructor of the base class with the contents
            # of the file
            super (TstFile, self).__init__(spec=stream.read ())




# Local Variables:
# mode:python
# fill-column:79
# End:
