#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# dbparser.py
# Description: A parser of the db language used for specifying
#              database tables
# -----------------------------------------------------------------------------
#
# Started on  <Sat Aug 10 19:13:07 2013 Carlos Linares Lopez>
# Last update <Wednesday, 14 August 2013 12:31:15 Carlos Linares Lopez (clinares)>
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
A parser of the testbot language used for specifying
#              command lines
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import ply.lex as lex
import ply.yacc as yacc


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
# returns an iterator of all the columns in the given table
# -----------------------------------------------------------------------------
class DBTableIter(object):

    """
    returns an iterator of all the columns in the given table
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
# DBTable
#
# Definition of an individual table
# -----------------------------------------------------------------------------
class DBTable:
    """
    Definition of an individiual table
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


    def sysp (self):
        """
        returns True if this is a sys table
        """

        return self._name[0:4] == 'sys_'


    def datap (self):
        """
        returns True if this is a data table
        """

        return self._name[0:5] == 'data_'


    def execute_action (self, column):
        """
        executes the action associated to the given column
        """

        # value to return
        value = None

        # execute the action specified for this column
        if column.get_action () == 'Warning':
            print " The variable '%s' was not available!" % column.get_variable ()
        elif column.get_action () == 'Error':
            print " The variable '%s' was not available!" % column.get_variable ()
            raise ValueError
        elif column.get_action () != 'None':
            return column.get_action ()

        # by default, return nothing
        return None


    def poll (self, D):
        """
        returns a tuple of values according to the definition of
        columns of this table and the values specified in D. In case
        the value requested for a particular column is not found, the
        specified action is executed.
        """

        def _neutral (ctype):
            """
            returns the neutral element of the given column type:
            text, integer or real
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


        # initialization 
        t=()

        # for all columns in this table
        for icolumn in self._columns:

            # in case the variable requested for this column is not
            # available, ...
            if icolumn.get_variable () not in D:

                # then execute the specified action
                value = self.execute_action (icolumn)

                # and include the pertinent value
                if value: t += (value,)
                else: t+=(_neutral (icolumn.get_type ()),)

            # otherwise
            else:
                t += (_cast_value (icolumn.get_type (), D[icolumn.get_variable ()]),)
                
        # and finally return the tuple
        return t
        

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
        'PARAM',
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
        r":[a-zA-Z_][a-zA-Z_0-9]*"
        t.value = t.value[1:]
        return t

    # data variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank
    # characters). They stand for information processed from the standard output
    # once the execution is over
    def t_DATAVAR (self, t):
        r"""\?([a-zA-Z_][a-zA-Z_0-9]*|'[^']+'|\"[^\"]+\")"""
        if t.value[1]=='"' or t.value[1]=="'": t.value = t.value [2:-1]
        else: t.value = t.value[1:]
        return t

    # file variables: strings (either single|double quoted that might contain
    # blank characters or just ordinary variables without any blank characters)
    # preceded by <. They stand for files whose content is copied once the
    # execution is over
    def t_FILEVAR (self, t):
        r"""\<([0-9a-zA-Z_/\.~]+|\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?')"""
        if t.value[1]=='"' or t.value[1]=="'": t.value = t.value [2:-1]
        else: t.value = t.value[1:]
        return t

    # directive variables: the value of any directive passed to the
    # executable. They stand for the value of directives given to the solver
    def t_DIRVAR (self, t):
        r"@[a-zA-Z_][a-zA-Z_0-9\-]*"
        t.value = t.value[1:]
        return t

    # param: any number preceded by the dollar sign. They stand for the
    # particular parameter passed to the solver
    def t_PARAM (self, t):
        r"\$\d+"
        t.value = int (t.value[1:])
        return t

    # tableid: a correct name for tables (either sys_ or data_)
    def t_TABLEID (self, t):
        r'(sys\_|data\_)[a-zA-Z_][a-zA-Z_0-9]*'
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
    def p_definitions (self, p):
        '''definitions : table
                       | table definitions'''
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
