#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# dbparser.py
# Description: A parser of the db language used for specifying
#              database tables
# -----------------------------------------------------------------------------
#
# Started on  <Sat Aug 10 19:13:07 2013 Carlos Linares Lopez>
# Last update <miércoles, 13 agosto 2014 01:53:38 Carlos Linares Lopez (clinares)>
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
A parser of the testbot language used for specifying
#              command lines
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import string                           # split

import ply.lex as lex
import ply.yacc as yacc

import colors                           # tty colors


# -----------------------------------------------------------------------------
# DBColumn
#
# Definition of an individual column of a table
# -----------------------------------------------------------------------------
class DBColumn:
    """
    Definition of an individiual column of a table
    """

    def __init__ (self, cidentifier, ctype, cvartype, cvariable, caction):
        """
        creates a column identified by the identifier, type, variable
        and action given in the arguments

        * identifier: it is a valid identifier which is represented with a
                      string that starts with a letter and can contain an
                      arbitrary number of digits and letters. The character '_'
                      is also allowed. Identifiers are implemented in the
                      grammar rule 'ID'

        * type: specifies the type of this database column (integer, real or
                string). It is implemented in the grammar rule 'type'

        * vartype: type of variable. It provides an indication of the namespace
                   that will hold its value. There are up to seven different
                   vartypes: sysvar, datavar, dirvar, filevar, mainvar, param
                   and regexp. All of them are implemented as terminal symbols
                   of the grammar with the same name

        * variable: internal name of the variable as it is known by autobot (for
                    the first six types) or as it is defined in a regexp (in the
                    last case). The internal names are computed in different
                    ways depending upon the vartype:

                    vartype   variable                  examples
                    sysvar    hard-coded in autobot     cputime, vsize
                    datavar   read from the stdout      cost, 'number of nodes'
                    dirvar    ordinal refs to params    0, 1, ...
                    filevar   filenames                 plan.soln
                    mainvar   flags given to testbot    quiet, test, db
                    param     params given to exec      beam-width, domain
                    regexp    regular expression        cost.value

                    In the last case, the user provided a regexp called 'cost'
                    with a group named 'value'

        * action: specifies what to do in case the variable was not found. The
                  following can be defined:

                  None - Do nothing
                  Warning - Just issue a warning
                  Error - Raise an execption

                  In the first two cases execution is resumed and the value of
                  the variable is computed with their "neutral" value (0 or 0.0
                  for numbers and the empty string for strings). In the last
                  case, execution is stopped and an error is raised
        """

        (self._identifier, self._type, self._vartype, self._variable , self._action) = \
            (cidentifier, ctype, cvartype, cvariable, caction)

    def __str__ (self):
        """
        output formatting
        """

        return "\t [identifier: %s] [type: %s] [vartype: %s] [variable: %s] [action: %s]" % \
            (self._identifier, self._type, self._vartype, self._variable, self._action)


    def get_identifier (self):
        """
        return the identifier of this column
        """

        return self._identifier


    def get_type (self):
        """
        return the type of this column
        """

        return self._type


    def get_vartype (self):
        """
        return the type of variable of this column
        """

        return self._vartype


    def get_variable (self):
        """
        return the variable of this column
        """

        return self._variable


    def get_action (self):
        """
        return the action of this column
        """

        return self._action


# -----------------------------------------------------------------------------
# DBTableIter
#
# returns an iterator over all columns of the given table
# -----------------------------------------------------------------------------
class DBTableIter(object):

    """
    returns an iterator over all columns of the given table
    """

    def __init__ (self, dbtable):
        """
        initialization
        """

        # initialize the position of the first test case to return
        self._current = 0

        # copy the table
        self._dbtable = dbtable


    def __iter__ (self):
        """
        (To be included in iterators)
        """

        return self


    def next (self):
        """
        returns the current column
        """

        if self._current >= len (self._dbtable._columns):
            raise StopIteration
        else:
            self._current += 1
            return self._dbtable._columns [self._current - 1]


# -----------------------------------------------------------------------------
# The db specification language acknowledges two different types of objets:
#
#       1. Database specification tables
#       2. Regular expressions
#
# These are created as instances of DBTable and DBRegexp
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# DBTable
#
# Definition of an individual database table. It also includes services for
# populating it from data in various namespaces
# -----------------------------------------------------------------------------
class DBTable:
    """
    Definition of an individual database table. It also includes services for
    populating it from data in various namespaces
    """

    def __init__ (self, name, columns):
        """
        creates a table with the given name and the specified columns
        """

        (self._name, self._columns) = (name, columns)


    def __iter__ (self):
        """
        return an iterator over the columns defined in this database
        """

        return DBTableIter (self)


    def __len__ (self):
        """
        return the number of columns of this table
        """

        return len (self._columns)


    def __str__ (self):
        """
        output formatting
        """

        # first, print the columns
        columns = reduce (lambda x,y:x+'\n'+y,
                          [DBColumn.__str__ (icolumn) for icolumn in self._columns])

        return """ %s {
%s
 }""" % (self._name, columns)


    def get_name (self):
        """
        return the name of this database table
        """

        return self._name


    def get_columns (self):
        """
        return the columns of this database table
        """

        return self._columns


    def sysp (self):
        """
        returns True if this is a sys table, ie., those that contain system
        information that is computed at every cycle
        """

        return self._name[0:4] == 'sys_'


    def datap (self):
        """
        returns True if this is a data table, ie., those that contain
        information that is stored once a particular test case has been given to
        a solver
        """

        return self._name[0:5] == 'data_'


    def userp (self):
        """
        returns True if this is a user table, ie., a table that is filled
        programatically by the client code of autobot
        """

        return self._name[0:5] == 'user_'


    def execute_action (self, column):
        """
        executes the action associated to the given column. An action can be
        either "Error", "Warning", "None" or anything else which is then
        returned
        """

        # execute the action specified for this column
        if column.get_action () == 'Warning':
            print """%s Warning [%s]: The variable '%s' was not available!
""" % (colors.yellow, self._name, column.get_variable ())
        elif column.get_action () == 'Error':
            print """%s Error [%s]: The variable '%s' was not available!
""" % (colors.red, self._name, column.get_variable ())
            raise ValueError
        elif column.get_action () != 'None':
            return column.get_action ()

        # by default, return nothing
        return None


    def poll (self, namespace, data, user, param, regexp):
        """
        returns a tuple of values according to the definition of columns of this
        table and the values specified in the given namespaces: namespace, data,
        user, param and regexp.

        In case the value requested for a particular column is not found, the
        specified action is executed.
        """

        def _neutral (ctype):
            """
            returns the neutral element of the given column type:
            text (''), integer (0) or real (0.0)
            """

            if ctype == 'text': return ''
            elif ctype == 'integer': return 0
            elif ctype == 'real': return 0.0
            else:
                print " Unknown type '%s'" % ctype
                raise TypeError


        def _cast_value (ctype, cvalue):
            """
            converts the given value to the specified column type
            """

            if ctype == 'text': return str (cvalue)
            elif ctype == 'integer': return int (cvalue)
            elif ctype == 'real': return float (cvalue)
            else:
                print " Unknown type '%s'" % ctype
                raise TypeError

        def _get_namespace (vartype):
            """
            return the namespace that should contain the values of a variable of
            the given vartype. This function actually implements the logic that
            associates variable types as specified by the user with namespaces
            as handled internally by autobot

            Note that, by default, the main namespace is used instead of raising
            an error (and, instead, if there is an action set to Error and the
            value is not find anywhere an error is finally raised)
            """

            if vartype == "SYS" or vartype == "MAINVAR": return namespace
            elif vartype == "DATA" or vartype == "FILEVAR": return data
            elif vartype == "PARAM" or vartype == "DIR": return param
            elif vartype == "USERVAR": return user
            elif vartype == "REGEXP": return regexp
            else: return namespace

        def _replicate (t, cardinality):
            """
            it returns a list of tuples with length equal to cardinality such
            that the i-th tuple contains the i-th item of t if it is a list and
            the item itself otherwise. It effectively replicates the specified t
            generating up to 'cardinality' tuples where 'cardinality' has to be
            equal to the maximum length of all lists if any or 1 otherwise.
            """

            return [tuple (map (lambda x:x[i] if isinstance (x, list) else x, t))
                    for i in range(cardinality)]


        # initialization
        t=()                    # raw description of the tuples to return
        cardinality = 1         # default cardinality of every column

        # for all columns in this table
        for icolumn in self:

            # in case this is not the regexp namespace (the cardinality is
            # always fixed to one)
            if icolumn.get_vartype () != "REGEXP":

                # get the right namespace for retrieving the value of this
                # variable
                nspace = _get_namespace (icolumn.get_vartype ())

                # if this variable does not exist in this namespace
                if icolumn.get_variable () not in nspace:

                    # then execute the specified action
                    value = self.execute_action (icolumn)

                    # and include the pertinent value
                    if value: t += (value,)
                    else: t+=(_neutral (icolumn.get_type ()),)

                # otherwise, add it after coercing the desired type
                else:
                    t += (_cast_value (icolumn.get_type (), nspace[icolumn.get_variable ()]),)

            # otherwise, in case this is the regexp namespace (the cardinality
            # can be any arbitrary number greater or equal than one)
            else:

                # compute the name of the regexp and the group within this
                # regexp from the variable name
                (name, group) = string.split (icolumn.get_variable (), '.')

                # in case this regexp does not exist in the regexp namespace
                if name not in regexp:

                    # then execute the specified action
                    value = self.execute_action (icolumn)

                    # and include the pertinent value
                    if value: t += (value,)
                    else: t+=(_neutral (icolumn.get_type ()),)

                # otherwise, compute the value of this regexp which is stored in
                # the namespace as a list of tuples of the same length than the
                # key
                else:

                    # if this group does not exist in this attribute then this
                    # is an error most likely due to the fact that the user
                    # accidentally mistyped the right name
                    if group not in regexp.getkeynames (name):
                        print """%s
 Error: while processing the table

%s

 the group '%s' was not found in the regexp '%s'
""" % (colors.red, self, group, name)
                        raise ValueError

                    # the following statement is simple (in spite of its fierce
                    # looking). It just return the i-th content of every tuple where
                    # the location (i) is computed as the position of the group in
                    # the keys of this attribute
                    vals = [jval [regexp._fields [name].index (group)]
                            for jval in regexp.getattr (name,
                                                        key=dict (zip (regexp.getkeynames (name),
                                                                       regexp.getkeynames (name))))]

                    # and add it to this tuple
                    t += (vals,)

                    # and check the cardinality ---if no column has been found
                    # with more than one item, then this one sets the maximum
                    # cardinality found so far
                    if cardinality == 1: cardinality = len (vals)

                    # otherwise, if the cardinality of this one is greater than
                    # one and it does not match the current max cardinality,
                    # then an error has been found
                    elif len (vals) > 1 and cardinality != len (vals):
                        print """%s
 Error: while processing the table

%s

 a cardinality mismatch has been found

 cardinality : %s
 vals        : %s
 t           : %s
""" % (colors.red, self, cardinality, vals, t)
                        raise ValueError

        # and finally replicate this tuple and return the result
        return _replicate (t, cardinality)


# -----------------------------------------------------------------------------
# DBRegexp
#
# Definition of an individual regular expression
# -----------------------------------------------------------------------------
class DBRegexp:
    """
    Definition of an individiual regular expression
    """

    def __init__ (self, name, specification):
        """
        creates a regular expression with the given name and specification
        """

        # just copy the name and specification of this regexp. Note that the
        # specification automatically eliminates the quotes (either double or
        # single)
        (self._name, self._specification) = (name, specification[1:-1])


    def __str__ (self):
        """
        output formatting
        """

        return " regexp %s : %s" % (self._name, self._specification)


    def get_name (self):
        """
        return the name of this regular expression
        """

        return self._name


    def get_specification (self):
        """
        return the specification of this regular expression
        """

        return self._specification


# -----------------------------------------------------------------------------
# DBParser
#
# Class used to define the lex and grammar rules necessary for
# interpreting the db language used for specifying database tables
# -----------------------------------------------------------------------------
class DBParser :
    """
    Class used to define the lex and grammar rules necessary for
    interpreting the db language used for specifying database tables
    """

    # reserved words
    reserved_words = {
        'regexp'  : 'REGEXP',
        'integer' : 'INTEGER',
        'real'    : 'REAL',
        'text'    : 'TEXT',
        'None'    : 'NONE',
        'Warning' : 'WARNING',
        'Error'   : 'ERROR'
        }

    # List of token names.   This is always required
    tokens = (
        'NUMBER',
        'FLOAT',
        'STRING',
        'LCURBRACK',
        'RCURBRACK',
        'SEMICOLON',
        'SYSVAR',
        'DATAVAR',
        'DIRVAR',
        'FILEVAR',
        'MAINVAR',
        'PARAM',
        'USERVAR',
        'ID',
        'TABLEID'
        ) + tuple(reserved_words.values ())

    def __init__ (self):
        """
        Constructor
        """

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self)


    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_LCURBRACK = r'\{'
    t_RCURBRACK = r'\}'
    t_SEMICOLON = r';'

    # Definition of integer numbers
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # Definition of real numbers
    def t_FLOAT(self, t):
        r'((\d*\.\d+)(E[\+-]?\d+)?|([1-9]\d*E[\+-]?\d+))'
        t.value = float(t.value)
        return t

    # A regular expression for recognizing both single and doubled quoted
    # strings
    def t_STRING (self, t):
        r"""\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?'"""
        return t

    # system variables: any variable preceded by a colon. They stand for
    # variables computed at every cycle
    def t_SYSVAR (self, t):
        r"(:|sys\.)[a-zA-Z_][a-zA-Z_0-9]*"
        if t.value[0]==':':
            t.value = t.value[1:]
        else:
            t.value = t.value[4:]
        return t

    # data variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank
    # characters). They stand for information processed from the standard output
    # once the execution is over
    def t_DATAVAR (self, t):
        r"""(\?|data\.)([a-zA-Z_][a-zA-Z_0-9]*|'[^']+'|\"[^\"]+\")"""
        if t.value[0]=='?':
            if t.value[1]=='"' or t.value[1]=="'":
                t.value = t.value [2:-1]
            else:
                t.value = t.value[1:]
        else:
            if t.value[5]=='"' or t.value[5]=="'":
                t.value = t.value [6:-1]
            else:
                t.value = t.value[5:]
        return t

    # directive variables: the value of any directive passed to the
    # executable. They stand for the value of directives given to the solver
    def t_DIRVAR (self, t):
        r"(@|dir\.)[a-zA-Z_][a-zA-Z_0-9\-]*"
        if t.value[0]=='@':
            t.value = t.value[1:]
        else:
            t.value = t.value[4:]
        return t

    # file variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank characters)
    # preceded by <. They stand for files whose content is copied once the
    # execution is over
    def t_FILEVAR (self, t):
        r"""(\<|file\.)([0-9a-zA-Z_/\.~]+|\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?')"""
        if t.value[0]=='<':
            if t.value[1]=='"' or t.value[1]=="'":
                t.value = t.value [2:-1]
            else:
                t.value = t.value[1:]
        else:
            if t.value[5]=='"' or t.value[5]=="'":
                t.value = t.value [6:-1]
            else:
                t.value = t.value[5:]
        return t

    # main variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank characters)
    # preceded by _. They stand for parameters passed to the testbot that
    # invokes executable
    def t_MAINVAR (self, t):
        r"""(_|main\.)([0-9a-zA-Z_/\.~]+|\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?')"""
        if t.value[0]=='_':
            if t.value[1]=='"' or t.value[1]=="'":
                t.value = t.value [2:-1]
            else:
                t.value = t.value[1:]
        else:
            if t.value[5]=='"' or t.value[5]=="'":
                t.value = t.value [6:-1]
            else:
                t.value = t.value[5:]
        return t

    # param: any number preceded by the dollar sign. They stand for the
    # particular parameter passed to the solver identified by its
    # location. Examples are $0, $1, ...
    def t_PARAM (self, t):
        r"(\$|param\.)\d+"
        if t.value[0]=='$':
            t.value = int (t.value[1:])
        else:
            t.value = int (t.value[6:])
        return t

    # user variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank characters)
    # preceded by ~. They stand for variables created and managed by the user
    def t_USERVAR (self, t):
        r"""(~|user\.)([0-9a-zA-Z_/\.~]+|\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?')"""
        if t.value[0]=='~':
            if t.value[1]=='"' or t.value[1]=="'":
                t.value = t.value [2:-1]
            else:
                t.value = t.value[1:]
        else:
            if t.value[5]=='"' or t.value[5]=="'":
                t.value = t.value [6:-1]
            else:
                t.value = t.value[5:]
        return t

    # regexp variables: any variable preceded by the name of a regexp. They
    # stand for namespaces whose contents can be accessed with the groups
    # defined in the regexp with the format <regexp-name>.<group-name>
    def t_REGEXP (self, t):
        r"[a-zA-Z][a-zA-Z_0-9]*\.[a-zA-Z_][a-zA-Z_0-9]*"

        # just return the string
        return t

    # tableid: a correct name for tables (either sys_, data_ or user_)
    def t_TABLEID (self, t):
        r'(sys|data|user)\_[a-zA-Z_][a-zA-Z_0-9]*'
        return t

    # The following rule distinguishes automatically between reserved words and
    # identifiers
    def t_ID (self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved_words.get(t.value,'ID')   # Check for reserved words
        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'

    # Rule to skip comments
    def t_COMMENT (self, t):
        r'\#.*'
        pass                                     # No return value. Token discarded

    # Error handling rule
    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    # grammar rules
    # -------------------------------------------------------------------------

    # definition of legal statements
    # -----------------------------------------------------------------------------

    # a valid db specification consists of tables which might contain regexp
    # anywhere between the table definitions
    def p_definitions (self, p):
        '''definitions : table
                       | regexp
                       | table definitions
                       | regexp definitions'''
        if len (p) == 2:
            p[0] = [p[1]]
        elif len (p) == 3:
            p[0] = [p[1]] + p[2]

    def p_table (self, p):
        '''table : TABLEID LCURBRACK columns RCURBRACK'''
        p[0] = DBTable (p[1], p[3])

    def p_columns (self, p):
        '''columns : column
                   | column columns'''
        if len (p) == 2:
            p[0] = [p[1]]
        elif len (p) == 3:
            p[0] = [p[1]] + p[2]

    def p_column (self, p):
        '''column : ID type variable SEMICOLON
                  | ID type variable action SEMICOLON'''
        if len (p) == 5:
            p[0] = DBColumn (p[1], p[2], p[3][0], p[3][1], 'None')
        elif len (p) == 6:
            p[0] = DBColumn (p[1], p[2], p[3][0], p[3][1], p[4])

    def p_type (self, p):
        '''type : INTEGER
                | REAL
                | TEXT'''
        p[0] = p[1]

    def p_variable_sysvar (self, p):
        '''variable : SYSVAR'''
        p[0] = ('SYS', p[1])

    def p_variable_datavar (self, p):
        '''variable : DATAVAR'''
        p[0] = ('DATA', p[1])

    def p_variable_dirvar (self, p):
        '''variable : DIRVAR'''
        p[0] = ('DIR', p[1])

    def p_variable_param (self, p):
        '''variable : PARAM'''
        p[0] = ('PARAM', p[1])

    def p_variable_file (self, p):
        '''variable : FILEVAR'''
        p[0] = ('FILEVAR', p[1])

    def p_variable_main (self, p):
        '''variable : MAINVAR'''
        p[0] = ('MAINVAR', p[1])

    def p_variable_user (self, p):
        '''variable : USERVAR'''
        p[0] = ('USERVAR', p[1])

    def p_variable_regexp (self, p):
        '''variable : REGEXP'''
        p[0] = ('REGEXP', p[1])

    def p_action (self, p):
        '''action : NONE
                  | WARNING
                  | ERROR
                  | default'''
        p[0] = p[1]

    def p_default (self, p):
        '''default : NUMBER
                   | FLOAT
                   | STRING'''
        p[0] = p[1]

    def p_regexp (self, p):
        '''regexp : REGEXP ID STRING'''
        p[0] = DBRegexp (p[2], p[3])

    # error handling
    # -----------------------------------------------------------------------------
    # Error rule for syntax errors
    def p_error(self, p):
        print "Syntax error while processing the database specification file!"
        print
        exit ()


# -----------------------------------------------------------------------------
# VerbatimDBParser
#
# Class used to process a verbatim string
# -----------------------------------------------------------------------------
class VerbatimDBParser (DBParser):
    """
    Class used to process a verbatim string
    """

    def run(self, data):
        """
        Just parse the given string
        """

        self._tables = self._parser.parse(data, lexer=self._lexer)


# -----------------------------------------------------------------------------
# InteractiveDBParser
#
# Class used to run the parser in interactive mode
# -----------------------------------------------------------------------------
class InteractiveDBParser (DBParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        while True:
            try:
                s = raw_input('db> ')
            except EOFError:
                break
            if not s: continue
            print self._parser.parse(s, lexer=self._lexer)


# -----------------------------------------------------------------------------
# FileDBParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileDBParser (DBParser):
    """
    Class used to parse the contents of the given file
    """

    def run(self, filename):
        """
        Just read the contents of the given file and process them
        """

        with open (filename) as f:
            self._tables = self._parser.parse(f.read (), lexer=self._lexer)



# Local Variables:
# mode:python
# fill-column:80
# End:
