#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# dbparser.py
# Description: A parser of the db language used for specifying
#              database tables
# -----------------------------------------------------------------------------
#
# Started on  <Sat Aug 10 19:13:07 2013 Carlos Linares Lopez>
# Last update <lunes, 20 octubre 2014 17:25:26 Carlos Linares Lopez (clinares)>
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

import dbexpression                     # evaluation of databse expressions


# globals
# -----------------------------------------------------------------------------

# nst stands for NameSpace Name and nsv stands for NameSpace Variable. nst does
# not necessarily refer to a particular namespace. In fact, autobot maps types
# to namespaces. Here we refer to the particular types recognized by the
# dbparser
SYSNST   = 'SYS'
DATANST  = 'DATA'
DIRNST   = 'DIR'
FILENST  = 'FILE'
MAINNST  = 'MAIN'
PARAMNST = 'PARAM'
USERNST  = 'USER'

SYSNSV   = 'SYSVAR'
DATANSV  = 'DATAVAR'
DIRNSV   = 'DIRVAR'
FILENSV  = 'FILEVAR'
MAINNSV  = 'MAINVAR'
PARAMNSV = 'PARAMVAR'
USERNSV  = 'USERVAR'

# the following namespace types do not come with a specific definition of
# variables since they do generate their own instances
REGEXPNST  = 'REGEXP'
SNIPPETNST = 'SNIPPET'

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
        creates a column identified by the identifier, type, variable type,
        variable and action given in the arguments

        * identifier: it is a valid identifier which is represented with a
                      string that starts with a letter and can contain an
                      arbitrary number of digits and letters. The character '_'
                      is also allowed. Identifiers are implemented in the
                      grammar rule 'ID'

        * type: specifies the type of this database column (integer, real or
                string). It is implemented in the grammar rule 'type'

        * vartype: type of variable. It provides an indication of the namespace
                   that will hold its value. There are up to eight different
                   vartypes: sysvar, datavar, dirvar, filevar, mainvar, param,
                   regexp and snippets. All of them are implemented as terminal
                   symbols of the grammar with the same name

        * variable: internal name of the variable as it is known by autobot (for
                    the first six types) or as it is defined in a regexp/snippet
                    (in the last two cases). The internal names are computed in
                    different ways depending upon the vartype:

                    vartype   variable                  examples
                    sysvar    hard-coded in autobot     cputime, vsize
                    datavar   read from the stdout      cost, 'number of nodes'
                    dirvar    ordinal refs to params    0, 1, ...
                    filevar   filenames                 plan.soln
                    mainvar   flags given to testbot    quiet, test, db
                    param     params given to exec      beam-width, domain

                    The case of regexps/snippets is exceptional. A couple of
                    examples follow:

                    vartype   variable                  examples
                    regexp    regular expression        cost.value
                    regexp    regexp in a context       sys.name/filename.algo
                    snippet   simple snippet            time.currtime
                    snippet   snippet in a context      stats.average/label.name

                    In the first case, the user provided a regexp called 'cost'
                    with a group named 'value' and it is applied to the default
                    "context" which is the current stream (typically the stdout
                    of an executable or the contents of a text file). In the
                    second case, a specific ccontext is provided: the name of
                    the file being parsed which is accessed through the sys
                    variable 'sys.name' which is processed with a regexp called
                    'filename'. The value retrieved is accessed through its
                    group 'algo'. Any variable can be used as the context as a
                    regexp including the result of another regexp. The third
                    example shows how the result of a regexp can be processed
                    with an additional regexp and, in general, there is no limit
                    and regular expressions can be nested as much as
                    desired. The only constraint is that all contexts shall be
                    regexps but the first one which can be a variable of any
                    type.

                    The first example of snippets shows the case where some
                    external Python code returns the value of variable
                    'currtime' in a snippet labeled as 'stats'. The second case
                    is analagous to the case of regexps with contexts.

        * action: specifies what to do in case the variable was not found. The
                  following can be defined:

                  None - Do nothing
                  Warning - Just issue a warning
                  Error - Raise an execption

                  In the first two cases execution is resumed and the value of
                  the variable is computed with their "neutral" value (0 or 0.0
                  for numbers and the empty string for strings). In the last
                  case, execution is stopped and an error is raised

                  If any other value is given, then it is used as a default
                  value in case the variable was not available, e.g.,
                  "<Unavailable>"
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


    def execute_action (self, column, logger):
        """
        executes the action associated to the given column. An action can be
        either "Error", "Warning", "None" or anything else which is then
        returned.

        In case an error or a warning are issued, the specified logger is used
        to show up the messages
        """

        # execute the action specified for this column
        if column.get_action () == 'Warning':
            logger.warning (" Warning [%s]: The variable '%s' was not available!" % (self._name, column.get_variable ()))
        elif column.get_action () == 'Error':
            logger.error (" Error [%s]: The variable '%s' was not available!" % (self._name, column.get_variable ()))
            raise ValueError
        elif column.get_action () != 'None':
            return column.get_action ()

        # by default, return nothing
        return None


    def poll (self, dbspec, namespace, data, param, regexp, snippet, user, logger, logfilter):
        """
        returns a tuple of values according to the definition of columns of this
        table and the values specified in the given namespaces: namespace, data,
        param, regexp, snippet and user

        In case the value requested for a particular column is not found, the
        specified action is executed. An action consists of either doing
        nothing, raising a Warning, an Error or returning a default value

        columns might evaluate to either scalars (computed by default or
        explicitly) or lists (computed explicitly). In case at least one column
        evaluates to a list, the tuples are replicated making sure that all
        columns take either the maximum cardinality or one.

        this method is also in charge of computing 'volatile' snippets. If a
        column is a snippet on its own or it is a regexp whose head is a snippet
        and it turns out that the snippet is volatile (ie., at least one of its
        output variables is declared as volatile) then it requests the
        recomputation of the snippet

        this method is likely to raise warnings and errors (along with an
        exception). Therefore, it receives also a logger to show messages
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
                logger.error (" Unknown type '%s'" % ctype)
                raise TypeError


        def _cast_value (ctype, cvalue):
            """
            converts the given value to the specified column type
            """

            if ctype == 'text': return str (cvalue)
            elif ctype == 'integer': return int (cvalue)
            elif ctype == 'real': return float (cvalue)
            else:
                logger.error (" Unknown type '%s'" % ctype)
                raise TypeError

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


        # update information about the logger ---the child and its filter
        logger = logger.getChild ("DBTable.poll")
        logger.addFilter (logfilter)

        # initialization
        t=()                    # raw description of the tuples to return
        cardinality = 1         # default cardinality of every column

        # for all columns in this table
        for icolumn in self:

            # create an expresssion that contains the specification of this
            # column
            expression = dbexpression.DBExpression (icolumn.get_vartype (),
                                                    icolumn.get_variable (),
                                                    logger,
                                                    logfilter)

            # foremost, in case this is a volatile snippet, then request its
            # execution *now*

            # on one hand, because it is a snippet on its own
            if expression.get_type () == SNIPPETNST:

                snippetexp = dbspec.get_snippet (string.split (icolumn.get_variable (), '.') [0])
                if snippetexp.get_keyword () == 'volatile':
                    expression.eval_snippet (dbspec  = dbspec,
                                             sys     = namespace,
                                             data    = data,
                                             param   = param,
                                             regexp  = regexp,
                                             snippet = snippet,
                                             user    = user)

            # or because it is a regexp whose head is a snippet
            elif expression.get_type () == REGEXPNST:

                # all regexps belong to a context, so access the first one
                # freely
                (prefix, var) = string.split (expression.get_context () [0], '.')
                snippetexp = dbspec.get_snippet (prefix)
                if snippetexp and snippetexp.get_keyword () == 'volatile':

                    # in this case, a specific expression has to be created to
                    # represent the head of this regexp
                    nestedexp = dbexpression.DBExpression (SNIPPETNST,
                                                           expression.get_context () [0],
                                                           logger,
                                                           logfilter)

                    # and evaluate it
                    nestedexp.eval_snippet (dbspec  = dbspec,
                                            sys     = namespace,
                                            data    = data,
                                            param   = param,
                                            regexp  = regexp,
                                            snippet = snippet,
                                            user    = user)

            # at this point we are in good shape to ensure that all necessary
            # data to evaluate any expression is already present in the
            # corresponding namespaces, so that evaluate the expression of the
            # definition of this particular column
            result = expression.eval (dbspec  = dbspec,
                                      sys     = namespace,
                                      data    = data,
                                      param   = param,
                                      regexp  = regexp,
                                      snippet = snippet,
                                      user    = user)

            # in case that the evaluation of this column resolved to nothing
            if result == None:

                # then execute the specified action
                value = self.execute_action (icolumn, logger)

                # and include the pertinent value
                if value: t += (value,)
                else: t+=(_neutral (icolumn.get_type ()),)

            # otherwise, add it after coercing the desired type
            else:

                # the result might be either a single scalar or a list
                if isinstance (result, list):

                    vals = [_cast_value (icolumn.get_type (), iresult) for iresult in result]
                    t += (vals,)

                    # and check the cardinality ---if no column has been found
                    # with more than one item, then this one sets the maximum
                    # cardinality found so far
                    if cardinality == 1: cardinality = len (vals)

                    # otherwise, if the cardinality of this one is greater than
                    # one and it does not match the current max cardinality,
                    # then an error has been found
                    elif len (vals) > 1 and cardinality != len (vals):
                        logger.error ("""
     Error: while processing the table

    %s

     a cardinality mismatch has been found

     cardinality : %i
     vals        : %s
     len (vals)  : %i
     t           : %s
    """ % (self, cardinality, vals, len (vals), t))
                        raise ValueError

                # in case this is a scalar
                else:
                    t += (_cast_value (icolumn.get_type (), result),)

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
# DBSnippetInput
#
# Definition of an individual input statement of a DBSnippet
# -----------------------------------------------------------------------------
class DBSnippetInput:
    """
    Definition of an individual input statement of a DBSnippet
    """

    def __init__ (self, sidentifier, stype, svartype, svariable):
        """
        creates an input variable identified by the identifier, type and
        variable type given in the arguments:

        * identifier: it is a valid identifier which is represented with a
                      string

        * type: specifies the type of this input variable (integer, real or
                string)

        * vartype: type of variable. It provides an indication of the namespace
                   that will hold its value

        * variable: internal name of the variable as it is known by autobot.

        These fields are also used in the definition of columns of database
        tables. See the docstring of the __init__ method of DBColumn for more
        information
        """

        # just copy the attributes of this instance
        (self._identifier, self._type, self._vartype, self._variable) = \
          (sidentifier, stype, svartype, svariable)


    def __str__ (self):
        """
        output formatting
        """

        return "[type: %s] %s = [vartype: %s] [variable: %s]" % (self._type, self._identifier, self._vartype, self._variable)


    def get_identifier (self):
        """
        return the identifier of this input statement
        """

        return self._identifier


    def get_type (self):
        """
        return the type of this input statement
        """

        return self._type


    def get_vartype (self):
        """
        return the type of the variable of this input statement
        """

        return self._vartype


    def get_variable (self):
        """
        return the variable attached to the name of this input statement
        """

        return self._variable


# -----------------------------------------------------------------------------
# DBSnippetOutput
#
# Definition of an individual output statement of a DBSnippet
# -----------------------------------------------------------------------------
class DBSnippetOutput:
    """
    Definition of an individual output statement of a DBSnippet
    """

    def __init__ (self, identifier, keyword):
        """
        creates an output variable with the given name and keyword:

        * identifier: it is a valid string designating the name of the output
                      variable

        * keyword: either STATIC or VOLATILE. In the first case, the value of
                   the variable is the same for the same values of the input
                   variables (eg., computing the average over a list of
                   numbers); in the second case, the value of the output
                   variable might changd in every evaluation for the same values
                   of the input variables ---e.g., computing the current time
        """

        # just copy the name and the variable
        (self._identifier, self._keyword) = (identifier, keyword)


    def __str__ (self):
        """
        output formatting
        """

        return "return %s [keyword: %s]" % (self._identifier, self._keyword)


    def get_identifier (self):
        """
        return the identifier of this output variable
        """

        return self._identifier


    def get_keyword (self):
        """
        return the keyword of this output variable
        """

        return self._keyword


# -----------------------------------------------------------------------------
# DBSnippet
#
# Definition of an individual snippet of code
# -----------------------------------------------------------------------------
class DBSnippet:
    """
    Definition of an individiual snippet of code
    """

    def __init__ (self, name, inputvars, outputvars, filecode):
        """
        creates a snippet with the given name whose specification consists of:

        * inputvars: variables used in the snippet that should be initialized to
                     the values given in their variables. They should be
                     instances of DBSnippetInput

        * outputvars: variables computed in the snippet whose value should be
                      returned to the database specification file to be used in
                      a column

        * filecode: contains the name of the python code to execute

        A snippet is said to be volatile if any of its output variables is
        qualified with the keyword 'volatile' and static otherwise (ie., if all
        its output variables are either qualified with the keyword 'static' or
        they are not explicitly qualified since 'static' is applied by default')
        """

        # just copy the name and the specification of the snippet
        (self._name, self._inputvars, self._outputvars,
         self._filecode) = \
         (name, inputvars, outputvars,
          filecode)

        # decide whether this is a static or volatile snippet. In case any
        # output variable is volatile the whole snippet is said to be volatile
        # as well
        if (self._outputvars and
            filter (lambda x:string.upper (x.get_keyword ()) == 'VOLATILE',
                    self._outputvars)):
            self._keyword = 'volatile'
        else:
            self._keyword = 'static'


    def __str__ (self):
        """
        output formatting
        """

        output = " snippet %s [keyword: %s]\n" % (self._name, self._keyword)
        for ivar in self._inputvars:
            output += '\t' + ivar.__str__ () + '\n'
        for ivar in self._outputvars:
            output += '\t' + ivar.__str__ () + '\n'
        output += "\teval " + self._filecode

        return output


    def get_name (self):
        """
        return the name of this snippet
        """

        return self._name


    def get_inputvars (self):
        """
        return the inputvars of this snippet
        """

        return self._inputvars


    def get_outputvars (self):
        """
        return the outputvars of this snippet
        """

        return self._outputvars


    def get_filecode (self):
        """
        return the file with the Python code to execute
        """

        return self._filecode

    def get_keyword (self):
        """
        return the snippet keyword, either 'volatile' or 'static'
        """

        return self._keyword


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
        'regexp'    : REGEXPNST,
        'snippet'   : SNIPPETNST,
        'static'    : 'STATIC',
        'volatile'  : 'VOLATILE',
        'return'    : 'RETURN',
        'eval'      : 'EVAL',
        'integer'   : 'INTEGER',
        'real'      : 'REAL',
        'text'      : 'TEXT',
        'None'      : 'NONE',
        'Warning'   : 'WARNING',
        'Error'     : 'ERROR'
        }

    # List of token names.   This is always required
    tokens = (
        'NUMBER',
        'FLOAT',
        'STRING',
        'LCURBRACK',
        'RCURBRACK',
        'EQ',
        'SEMICOLON',
        'SLASH',
        SYSNSV,
        DATANSV,
        DIRNSV,
        FILENSV,
        MAINNSV,
        PARAMNSV,
        USERNSV,
        'QUALIFIEDVAR',
        'ID',
        'TABLEID'
        ) + tuple(reserved_words.values ())

    def __init__ (self):
        """
        Constructor
        """

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self,write_tables=0)

        # and also declare a couple of symbol tables for storing the names of
        # regexps and snippets
        self._regexptable = {}
        self._snippettable = {}

    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_LCURBRACK  = r'\{'
    t_RCURBRACK  = r'\}'
    t_EQ         = r'='
    t_SEMICOLON  = r';'
    t_SLASH      = r'/'

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
    # strings in a single line
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

    # param variables: any number preceded by the dollar sign. They stand for
    # the particular parameter passed to the solver identified by its
    # location. Examples are $0, $1, ...
    def t_PARAMVAR (self, t):
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

    # qualified variables: any variable preceded by a name and a dot. They are
    # used to refer to regexps and snippets. In the case of regexps the format
    # is <regexp-name>.<group-name>. In the case of snippets the format is
    # <snippet-name>.<output-variable-name>
    def t_QUALIFIEDVAR (self, t):
        r"[a-zA-Z][a-zA-Z_0-9]+\.[a-zA-Z_][a-zA-Z_0-9]+"
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
                       | snippet
                       | table definitions
                       | regexp definitions
                       | snippet definitions'''
        if len (p) == 2:
            p[0] = [p[1]]
        elif len (p) == 3:
            p[0] = [p[1]] + p[2]

    # definition of regexps
    # -----------------------------------------------------------------------------
    def p_regexp (self, p):
        '''regexp : REGEXP ID STRING'''
        p[0] = DBRegexp (p[2], p[3])

        # and now write the information of this regexp in the regexp table
        self._regexptable [p[2]] = p[0]

    # definition of snippets
    # -----------------------------------------------------------------------------
    def p_snippet (self, p):
        '''snippet : SNIPPET ID outputvars EVAL FILEVAR
                   | SNIPPET ID inputvars outputvars EVAL FILEVAR'''
        # note that the inputvars are optional since they might not be necessary
        # to perform any computation
        if len (p) == 6:
            p[0] = DBSnippet (p[2], [], p[3], p[5])
        else:
            p[0] = DBSnippet (p[2], p[3], p[4], p[6])

        # finally, write the information of this snippet in the snippet table
        self._snippettable [p[2]] = p[0]

    def p_snippet_inputvars (self, p):
        '''inputvars : input_statement
                     | input_statement inputvars'''
        if len (p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[2]

    def p_input_statement (self, p):
        '''input_statement : type ID EQ variable'''
        p[0] = DBSnippetInput (p[2], p[1], p[4][0], p[4][1])

    def p_snippet_outputvars (self, p):
        '''outputvars : output_statement
                      | output_statement outputvars'''
        if len (p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[2]

    def p_output_statement (self, p):
        '''output_statement : RETURN ID
                            | RETURN keyword ID'''
        # keywords are used to qualify the output variable: either static or
        # volatile. By default, they are static
        if len (p) == 3:
            p[0] = DBSnippetOutput (p[2], 'static')
        else:
            p[0] = DBSnippetOutput (p[3], p[2])

    def p_output_statement_keyword (self, p):
        '''keyword : STATIC
                   | VOLATILE'''
        p[0] = p[1]

    # definition of data tables
    # -----------------------------------------------------------------------------
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
        p[0] = (SYSNST, p[1])

    def p_variable_datavar (self, p):
        '''variable : DATAVAR'''
        p[0] = (DATANST, p[1])

    def p_variable_dirvar (self, p):
        '''variable : DIRVAR'''
        p[0] = (DIRNST, p[1])

    def p_variable_paramvar (self, p):
        '''variable : PARAMVAR'''
        p[0] = (PARAMNST, p[1])

    def p_variable_file (self, p):
        '''variable : FILEVAR'''
        p[0] = (FILENST, p[1])

    def p_variable_main (self, p):
        '''variable : MAINVAR'''
        p[0] = (MAINNST, p[1])

    def p_variable_user (self, p):
        '''variable : USERVAR'''
        p[0] = (USERNST, p[1])

    def p_variable_qualified (self, p):
        '''variable : QUALIFIEDVAR
                    | variable SLASH QUALIFIEDVAR'''

        # compute the prefix of the qualified var
        prefix = string.split (p[len (p)-1], '.') [0]

        # check whether it refers to a regexp or a snippet
        if prefix in self._regexptable: vartype = REGEXPNST
        elif prefix in self._snippettable: vartype = SNIPPETNST
        else:
            print "Line %i: The qualified var '%s' has been found but it does not appear to be either a REGEXP or a SNIPPET" % (p.lineno (1), p[1])
            self.p_error (p)

        if len (p) == 2:
            p[0] = (vartype, p[1])
        else:

            # check whether the variable (p[1]) is the *first* context
            if string.find (p[1][1], DBParser.t_SLASH) < 0:

                # in case it is, keep track of the type of the first context if
                # and only if it is not a regexp or a snippet. In case it is
                # either a regexp or a snippet then avoid writing down its type
                # (since they are qualified by their name solely)
                if p[1][0] != REGEXPNST and p[1][0] != SNIPPETNST:
                    p[0] = (vartype, string.lower (p[1][0]) + '.' + p[1][1] + DBParser.t_SLASH + p[3])
                else:
                    p[0] = (vartype, p[1][1] + DBParser.t_SLASH + p[3])
            else:

                # if not then just concatenate the variable name to the full
                # expression
                p[0] = (vartype, p[1][1] + DBParser.t_SLASH + p[3])

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
