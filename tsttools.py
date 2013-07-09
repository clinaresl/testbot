#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# tsttools.py
# Description: test tools
# -----------------------------------------------------------------------------
#
# Started on  <Sat May  4 01:37:54 2013 Carlos Linares Lopez>
# Last update <Friday, 21 June 2013 15:49:41 Carlos Linares Lopez (clinares)>
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
test tools
"""

__version__  = '1.0'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import re               # regexp

from collections import defaultdict
from string import find
from string import Template


# globals
# -----------------------------------------------------------------------------

# comment lines and blank lines
COMMENTREGEXP = "[ \t]*#.*"
BLANKREGEXP = "[ \t]*$"

# enumerates: enumerate sentence, and values of enumerates
ENUMREGEXP = "enumerate[ \t]*(?P<name>\S+)[ \t]*="
ENUMREGEXP1 = """(?P<value>"[^"]*")"""
ENUMREGEXP2 = "(?P<value>'[^']*')"
ENUMREGEXP3 = "(?P<value>\S+)"

# ranges: range sentence and values
RANGEREGEXP = "range[ \t]*(?P<name>\S+)[ \t]*="
RANGEREGEXP1 = "(?P<start>[-+]*\d+):(?P<end>[-+]*\d+)(:(?=(?P<step>[-+]*\d+)))?"

# specification lines: separator between fields, directives and strings
SPECSEPREGEXP = "\s+"
DIRECTIVETYPEREGEXP = "^\-+"
STYPEREGEXP = "(S|s)$"

# fields of the datalines: indexes and strings
IDXREGEXP = "(?P<index>\d+) "
SREGEXP = """(?P<value>'[^']*'|"[^"]*"|\S+)"""
ENUMVAR = "(?P<prefix>\S*)\$(?P<suffix>\S+)"

# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# parse_enum
#
# parse an enumerate. It returns a list with the strings contained in it
# -----------------------------------------------------------------------------
def parse_enum(enumline):

    """
    parse an enumerate. It returns a list with the strings contained in it
    """

    # initialization
    values = []

    # try the following matches from the most general (quoted strings) to the
    # least general (strings with no whitespace chars)
    regexps = [ENUMREGEXP1, ENUMREGEXP2, ENUMREGEXP3]
    while (enumline):

        for iregex in regexps:

            m = re.match (iregex, enumline)
            if (m):
                values.append (m.group ('value'))
                enumline = enumline[m.end ():].lstrip ()

                break

    # and return the list of values computed so far
    return values


# -----------------------------------------------------------------------------
# parse_range
#
# parse a range. It returns a list with the values in the range
# -----------------------------------------------------------------------------
def parse_range(rangeline, lineno, filename):

    """
    parse a range. It returns a list with the values in the range
    """

    # parses the range limits
    m = re.match (RANGEREGEXP1, rangeline)
    if not m:
        raise SyntaxError ("Wrong range specification, line %i in %s: %s" % 
                           (lineno, filename, rangeline))

    # compute the limits of the range ---if a step was not given, 1 is assumed
    # by default
    (start, end, step) = (int (m.group ('start')), int (m.group ('end')), 1)
    if (m.group ('step')):
        step = int (m.group ('step'))

    # check the limits are correct
    if ((end > start and step < 0) or
        (end < start and step > 0)):
        raise SyntaxError ("The specified range diverges, line %i in %s: %s" %
                           (lineno, filename, rangeline))
    
    # and return the values in the range
    return range (start, end, step)


# -----------------------------------------------------------------------------
# process_specline
#
# process the specification line and performs the right substitutions in the
# dataline without considering variables and return a list of strings with the
# result of the expansion. lineno and filename are used to label syntax errors
# in case any is found
# -----------------------------------------------------------------------------
def process_specline(specline, dataline, lineno, filename):

    """
    process the specification line and performs the right substitutions in the
    dataline without considering variables and return a list of strings with the
    result of the expansion. lineno and filename are used to label syntax errors
    in case any is found
    """

    # initialization
    cmdline = []                        # no contents in the cmdline yet

    # for every item in the specification line
    for ispec in specline:

        # if this is a directive, just copy it to all cmdlines
        if (re.match (DIRECTIVETYPEREGEXP, ispec)):

            cmdline.append (ispec)
            continue

        # otherwise, if it is not a string, raise a syntax error
        if (not re.match (STYPEREGEXP, ispec)):
            raise SyntaxError ("Unknown Type '%s', line %i in %s: %s" % 
                               (ispec, lineno, filename, dataline))

        # otherwise, retrieve the value from the dataline
        m = re.match (SREGEXP, dataline)
        if (not m):
            raise SyntaxError ("Syntax Error, line %i in %s: %s" % 
                               (lineno, filename, dataline))

        # and append it to the cmdline
        cmdline.append (m.group ('value'))

        # and move forward in the data line
        dataline=dataline[m.end ():].lstrip ()

    # check whether the dataline is not empty
    if (len (dataline) != 0):
        print """
 Warning - line %i, file %s seems to contain more fields than those appearing in 
           its specification line""" % (lineno, filename)

    # and now return the cmdline computed so far
    return cmdline


# -----------------------------------------------------------------------------
# substitute
#
# substitute all the placeholders in cmdline (which is a list of strings) by the
# appropriate values in table
# -----------------------------------------------------------------------------
def substitute(cmdline, table):

    """
    substitute all the placeholders in cmdline (which is a list of strings) by
    the appropriate values in table
    """

    # initialization - initially, the result equals the same cmdline
    result = [cmdline]

    # for every placeholder that ever appears in the current cmdline
    for ivar in [jvar for jvar in table 
                 if any ([find (icmd, jvar)>=0 for icmd in cmdline])]:

        # perform the safe substitution of this variable in all strings of every
        # cmdline
        result = [[Template.safe_substitute (Template (icmd), {ivar:ivalue}) 
                   for icmd in icmdline] 
                  for icmdline in result for ivalue in table [ivar]]
            
    # and return the substitution
    return result
        

# -----------------------------------------------------------------------------
# expand
#
# expand the dataline according to the contents of the given specification line
# and the values of variables stored in table
# -----------------------------------------------------------------------------
def expand(specline, dataline, table, lineno, filename):

    """
    expand the dataline according to the contents of the given specification
    line and the values of variables stored in table
    """

    # first, process the specification line - this preliminary step returns a
    # tuple with a list (with the contents of the dataline which are interpreted
    # according to the specification line) and a list of user-defined variables
    # appearing in the command line
    cmdline = process_specline (specline, dataline, lineno, filename)
    
    # second, process all placeholders in the cmdline and substitute them
    # appropriately by the values specified in the symbols table
    return substitute (cmdline, table)


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

            if (self._current >= len (self._tstspec._tstdefs)):
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
        initializes the definition of this test case. 'index' is just a string
        while args shall consist of a list of strings which is interpreted in
        the same order from left to right
        """

        # while it is absolutely legal to create a test case with no arguments
        # (so that any object of length zero or just None can be given), this is
        # internally represented as a list with the empty string
        if (not args):
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
        """

        # just look for all the occurrences of strings starting with an
        # arbitrary number of dashes and return a list with them but with dashes
        # removed
        return map (lambda x:x.lstrip ('-'),
                    filter (lambda y:re.match ("\-+",y), self._args))


    def get_value (self, directive):
        """
        returns the values of the given directive. It explicitly takes into
        account the case of command lines that contain the same directive
        several times or the case of directives that contain an arbitrary number
        of values
        """

        # take all the occurrences of this directive in the list of arguments
        # along with their position
        for iL in [jL for jL in zip (range(len(self._args)), self._args) 
                   if re.match ("\-+"+directive+'$', jL[1])]:
            
            # while the next position is not a directive
            nextidx = iL[0]+1
            while (nextidx < len (self._args) and
                   not re.match ("^\-+", self._args [nextidx])):

                # return it
                try:
                    yield (self._args[nextidx])
                except EnvironmentError:
                    pass

                # and move to the next one
                nextidx += 1


    def get_values (self):
        """
        returns a dictionary with the value of all directives that contain, at
        least, a value. If more than one is available, they are all grouped
        within the same string. If no value is found, the null string is
        returned
        """

        # create the dictionary to return
        d = defaultdict (str)

        # take all the occurrences of all directives in the list of arguments
        # along with their position
        for iL in [jL for jL in zip (range(len(self._args)), self._args) 
                   if re.match ("\-+", jL[1])]:
            
            # while the next position is not a directive
            nextidx = iL[0]+1
            while (nextidx < len (self._args) and
                   not re.match ("^\-+", self._args [nextidx])):

                # add white spaces in between if required, i.e., if something
                # was already writen
                if d[iL[1].lstrip ('-')]:
                    d [iL[1].lstrip ('-')] += ' '

                # add it to the list of values of this directive (with the
                # leading '-' removed)
                d [iL[1].lstrip ('-')] += self._args [nextidx]

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
    this class provides services for accessing and interpreting the
    contents of test specifications
    """

    def __init__ (self, spec):
        """
        decodes the contents of a test specification
        """

        # store the test specification after splitting it by lines
        self._tstspec = spec.split ('\n')

        # initialize the 'symbols table'
        self._table = defaultdict (list)

        # make the test definitions null
        self._tstdefs = []

        # decode its contents
        self._decode (self._tstspec)


    def _decode (self, tstspec):
        """
        decodes the contents of the given test specification
        """

        # initialization
        lineno = 1                      # line number
        specline = []                   # no specification line has been found yet

        # process separately each line of the test specification

        # for every line not being a comment or blank line
        for iline in [jline for jline in self._tstspec
                      if (not re.match (COMMENTREGEXP, jline) and 
                          not re.match (BLANKREGEXP, jline))]:

            iline = iline.lstrip ()         # remove leading white spaces

            # if this is a spec line, then process its contents
            if (iline [0] == '@'):

                # get the specification line ---the filter just
                # removes the empty strings that might appear. The
                # matching starts at position 2 since after ':'
                # there should be a blank
                specline = filter (lambda x:x,
                                   re.split (SPECSEPREGEXP, iline[2:]))
                lineno += 1
                continue

            # is it an enumerate?
            m = re.match (ENUMREGEXP, iline)
            if (m):
                self._table [m.group ('name')] = parse_enum (iline[m.end ():].lstrip ())

                lineno += 1
                continue

            # is it a range?
            m = re.match (RANGEREGEXP, iline)
            if (m):
                self._table [m.group ('name')] = parse_range (iline[m.end ():].lstrip (),
                                                              lineno, self._tstspec)

                lineno += 1
                continue

            # otherwise, this is treated as a data line - note that data
            # lines can be specified even without spec lines (this is useful
            # when a solver is invoked without arguments)

            # find the index number first
            m = re.match (IDXREGEXP, iline)

            # if no index is found, raise a syntax error
            if (not m):
                raise SyntaxError ("Index not found in line %i file %s: %s" %
                                   (lineno, self._tstspec, iline))

            index = m.group ('index')

            # expand the current specification line with the contents of
            # this data line
            self._tstdefs += [TstCase (index, icase)
                              for icase in expand (specline, iline[m.end ():].lstrip (),
                                                   self._table, lineno, self._tstspec)]

            lineno += 1                             # and move forward


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

        # store the test specification after splitting it by lines
        with open (filename) as stream:

            # simply invoke the constructor of the base class with the contents
            # of the file
            super (TstFile, self).__init__(spec=stream.read ())




# Local Variables:
# mode:python
# fill-column:80
# End:
