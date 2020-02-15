#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tbparser.py
# Description: A parser of the testbot language used for specifying
#              command lines
# -----------------------------------------------------------------------------
#
# Started on  <Fri Aug  2 09:16:49 2013 Carlos Linares Lopez>
# Last update <jueves, 20 noviembre 2014 14:04:57 Carlos Linares Lopez (clinares)>
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
A parser of the testbot language used for specifying command lines
"""


# imports
# -----------------------------------------------------------------------------
import ply.lex as lex
import ply.yacc as yacc

# -----------------------------------------------------------------------------
# TBParser
#
# Class used to define the lex and grammar rules necessary for
# interpreting the tb language used for specifying command lines
# -----------------------------------------------------------------------------
class TBParser :
    """
    Class used to define the lex and grammar rules necessary for
    interpreting the tb language used for specifying command lines
    """

    # reserved words
    reserved_words = {
        'exec'  : 'EXEC',
        'range' : 'RANGE',
        }

    # List of token names
    tokens = (
        'NUMBER',
        'STRING',
        'EQUAL',
        'PLUS',
        'MINUS',
        'CARTPROD',
        'TIMES',
        'DIVIDE',
        'MOD',
        'EXP',
        'LPAREN',
        'RPAREN',
        'LBRACK',
        'RBRACK',
        'COMMA',
        'SEMICOLON',
        'ID',
        ) + tuple(reserved_words.values ())

    # precedence rules
    precedence = (
        ('left', 'EQUAL'),
        ('left', 'MINUS', 'PLUS'),
        ('left', 'MOD'),
        ('left', 'CARTPROD', 'TIMES', 'DIVIDE'),
        ('right', 'EXP'),
        ('right', 'UMINUS', 'UPLUS'),
        )

    def __init__ (self):
        """
        Constructor
        """

        # commands
        self.cmds = []
        
        # global symbol table
        self.symbols = {}

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self)


    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_EQUAL     = r'='
    t_PLUS      = r'\+'
    t_MINUS     = r'-'
    t_CARTPROD  = r'@'
    t_TIMES     = r'\*'
    t_DIVIDE    = r'/'
    t_MOD       = r'%'
    t_EXP       = r'\^'
    t_LPAREN    = r'\('
    t_RPAREN    = r'\)'
    t_LBRACK    = r'\['
    t_RBRACK    = r'\]'
    t_COMMA     = r','
    t_SEMICOLON = r';'

    # A regular expression rule with some action code
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)    
        return t

    # A regular expression for recognizing both single and doubled quoted strings
    def t_STRING (self, t):
        r"""'[^']*'|\"[^"]*\""""
        return t

    # The following rule distinguishes automatically between reserved words and
    # identifiers
    def t_ID (self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved_words.get(t.value,'ID')    # Check for reserved words
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
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # grammar rules
    # -------------------------------------------------------------------------

    # definition of legal statements
    # -----------------------------------------------------------------------------
    def p_script (self, p):
        '''script : statement SEMICOLON
                  | script statement SEMICOLON'''
        if len (p) == 3:
            p[0] = p[1]
        elif len (p) == 4:
            p[0] = p[2];

    def p_statement_expr (self, p):
        '''statement : expression'''
        p[0] = p[1]

    def p_statement_assignment (self, p):
        '''statement : ID EQUAL expression'''
        self.symbols [p[1]] = p[3]
        p[0]=p[3]

    def p_statement_exec (self, p):
        'statement : EXEC statement'
        if isinstance (p[2], tuple):
            for ip in p[2]:
                self.cmds.append (ip)
        else:
            self.cmds.append (p[2])

    # valid expressions
    # -----------------------------------------------------------------------------
    def p_num_expr (self, p):
        'expression : NUMBER'
        p[0] = p[1]

    def p_str_expr (self, p):
        'expression : STRING'
        p[0] = p[1][1:-1]

    def p_id_expr (self, p):
        'expression : ID'
        p[0] = self.symbols [p[1]]

    def p_array_expr (self, p):
        'expression : list'
        p[0] = p[1]

    def p_list (self, p):
        '''list : array
                | range'''
        p[0] = p[1]

    def p_array (self, p):
        '''array : LBRACK RBRACK
                 | LBRACK body_array RBRACK'''
        if len (p) == 3:
            p[0] = ()
        elif len (p) == 4:
            p[0] = p[2]

    def p_body_array (self, p):
        '''body_array : expression
                      | expression COMMA body_array'''
        if len (p) == 2:
            p[0] = tuple ([p[1]])
        elif len (p) == 4:
            p[0] = tuple ([p[1]]) + p[3]

    def p_range_expr (self, p):
        '''range : RANGE LPAREN expression COMMA expression RPAREN
                 | RANGE LPAREN expression COMMA expression COMMA expression RPAREN'''
        if len (p) == 7:
            p[0] = tuple (range (p[3], p[5]))
        elif len (p) == 9:
            p[0] = tuple (range (p[3], p[5], p[7]))

    # operations
    # -----------------------------------------------------------------------------
    def p_expr_plus(self, p):
        'expression : expression PLUS expression'
        if isinstance (p[1], tuple):
            p[0] = tuple (map (lambda x,y:x+y, p[1], p[3]))
        else:
            p[0] = p[1] + p[3]

    def p_expr_minus(self, p):
        'expression : expression MINUS expression'
        if isinstance (p[1], tuple):
            p[0] = tuple (map (lambda x,y:x-y, p[1], p[3]))
        else:
            p[0] = p[1] - p[3]

    def p_expr_cartprod(self, p):
        'expression : expression CARTPROD expression'
        if isinstance (p[1], tuple) and isinstance (p[3], tuple):
            p[0] = tuple ([i+j for i in p[1] for j in p[3]])
        else:
            p[0] = None

    def p_expr_times(self, p):
        'expression : expression TIMES expression'
        if isinstance (p[1], tuple) and isinstance (p[3], tuple):
            p[0] = tuple (map (lambda x,y:x*y, p[1], p[3]))
        else:
            p[0] = p[1] * p[3]

    def p_expr_div(self, p):
        'expression : expression DIVIDE expression'
        if isinstance (p[1], tuple):
            p[0] = tuple (map (lambda x,y:x/y, p[1], p[3]))
        else:
            p[0] = p[1] / p[3]

    def p_expr_mod(self, p):
        'expression : expression MOD expression'
        if isinstance (p[1], tuple):
            p[0] = tuple (map (lambda x,y:x%y, p[1], p[3]))
        elif isinstance (p[1], str):
            p[0] = p[1] % tuple (p[3])
        else:
            p[0] = p[1] % p[3]

    def p_num_expr_exp (self, p):
        'expression : expression EXP expression'
        p[0] = p[1]**p[3]

    def p_expr_uminus(self, p):
        'expression : MINUS expression %prec UMINUS'
        p[0] = -p[2]

    def p_expr_uplus(self, p):
        'expression : PLUS expression %prec UPLUS'
        p[0] = +p[2]

    def p_paren_expr(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = p[2]

    # error handling
    # -----------------------------------------------------------------------------
    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error while processing the tests specification file!")
        print()
        exit ()


# -----------------------------------------------------------------------------
# VerbatimTBParser
#
# Class used to process a verbatim string
# -----------------------------------------------------------------------------
class VerbatimTBParser (TBParser):
    """
    Class used to process a verbatim string
    """

    def run(self, data):
        """
        Just parse the given string
        """

        self.cmds = []                       # initialization
        self._parser.parse(data, lexer=self._lexer)


# -----------------------------------------------------------------------------
# InteractiveTBParser
#
# Class used to run the parser in interactive mode
# -----------------------------------------------------------------------------
class InteractiveTBParser (TBParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        self.cmds = []                       # initialization

        while True:
            try:
                s = raw_input('testbot> ')
            except EOFError:
                break
            if not s: continue
            print(self._parser.parse(s, lexer=self._lexer))


# -----------------------------------------------------------------------------
# FileTBParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileTBParser (TBParser):
    """
    Class used to parse the contents of the given file
    """

    def run(self, filename):
        """
        Just read the contents of the given file and process them
        """

        self.cmds = []                       # initialization
        with open (filename) as f:
            self._parser.parse(f.read (), lexer=self._lexer)


# Local Variables:
# mode:python
# fill-column:79
# End:
