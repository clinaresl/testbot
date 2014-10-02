#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# dbexpression.py
# Description: DBExpression implements the main services for
#              evaluating database expressions with data in different
#              namespaces
# -----------------------------------------------------------------------------
#
# Started on  <Sun Sep 28 00:22:50 2014 Carlos Linares Lopez>
# Last update <domingo, 28 septiembre 2014 00:23:13 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id::                                                                      $
# $Date::                                                                    $
# $Revision::                                                                $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@atlas>
#

"""
DBExpression implements the main services for evaluating database expressions
with data in different namespaces
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import colors                           # terminal colors
import logging                          # logging services
import re                               # regular expressions (finditer)
import string                           # split, find

import dbparser                         # t_SLASH


# -----------------------------------------------------------------------------
# DBExpression
#
# Definition of a database expression
# -----------------------------------------------------------------------------
class DBExpression:
    """
    Definition of a database expression
    """

    def __init__ (self, exptype, expression, logger, logfilter):
        """
        creates an instance of DBExpression with the specified expression of the
        given type (exptype)

        the services of this class handle fatal errors and thus, a logger is
        given to it to let the user know about them
        """

        # update information about the logger ---the child and its filter
        self._logger = logger.getChild ("DBExpression.dbexpression")
        self._logger.addFilter (logfilter)

        # verify that the expression is of the form
        #
        # <prefix 1>.<var 1>/.../<prefix n.var n>
        #
        # for n>0
        nbseps = string.count (expression, dbparser.DBParser.t_SLASH)
        nbdots = string.count (expression, '.')
        if nbdots != nbseps + 1:
            self._logger.critical (" Syntax error in expression: '%s'" % expression)
            raise ValueError

        # copy the expression (and its type) given to this instance
        self._type, self._expression = (exptype, expression)

        # Do this expression contain a context? If so, process them in a list
        if nbseps > 0:
            self._hascontext = True
            self._contexts = string.split (expression, dbparser.DBParser.t_SLASH)
        else:
            self._hascontext = False
            self._contexts = None


    def get_expression (self):
        """
        return the expression of this instance
        """

        return self._expression


    def get_type (self):
        """
        return the type of the expression of this instance
        """

        return self._type


    def has_context (self):
        """
        returns True if expression is given within a context and False otherwise
        """

        return self._hascontext


    def get_context (self):
        """
        returns the context of this expression in case it has any and None
        otherwise
        """

        return self._contexts


    def eval (self, dbspec, sys, data, param, regexp, user, logger):
        """
        eval returns the evaluation of the expression stored in this
        instance. The evaluation is resolved with information of the regular
        expressions stored in the database specification and data in the
        different namespaces given in the arguments solely.

        'sys', 'data', 'param', 'regexp' and 'user' are namespaces whose
        description is given in the bot that uses dbexpressions. Currently, eval
        maps different prefixes given to the expression to the different
        namespaces as follows:

        namespace   prefix
        ----------+-----------------
        sys       | sys. main.
        data      | data. file.
        param     | param. dir.
        user      | user.
        regexp    | <regexp-name>.<group-name>
        ----------+-----------------

        'eval' affects neither the database specification nor the namespaces and
        they are used solely to retrieve data.

        The result of the evaluation can be either a scalar or a list of
        values. In case that the evaluation resolves to nothing eval returns
        None.

        eval also welcomes regular expressions with an arbitrary number of
        contexts. The final value in this case is computed as the match of every
        regexp to the result of the previous evaluation. All contexts shall be
        regular expressions, but the first one which can be any type.

        eval might raise warnings and errors. Therefore, it receives a
        logger to show messages
        """

        def _get_namespace ():
            """
            return the namespace that should contain the values of a variable of
            the type of this instance. This function actually implements the
            logic that associates prefixes to namespaces as given above.
            """

            if self._type == "SYS" or self._type == "MAIN": return sys
            elif self._type == "DATA" or self._type == "FILE": return data
            elif self._type == "PARAM" or self._type == "DIR": return param
            elif self._type == "REGEXP": return regexp
            elif self._type == "USER": return user
            else:
                self._logger.critical (" Unknown prefix '%s'" % self._type)
                raise ValueError


        def _eval_without_context (expression):
            """
            returns the value of the given expression according to the
            namespaces given to 'eval'. This applies just to expressions without
            context or the first context of regular expressions with an
            arbitrary number of them
            """

            # compute the prefix and variable of this expression
            (prefix, variable) = string.split (expression, '.')

            # in case this is a regexp, then we have to compute the projection
            # of the regexp over the given variable
            if self._type == "REGEXP":

                result = regexp.projection (prefix, variable)

                # the result of a project is a list with a tuple that contains
                # the keys used for the projection and then a list of tuples
                # with the values (also projected). We get rid here of the tuple
                # of keys and we convert the list of tuples into a list of
                # values
                return map (lambda x:x[0], result[1])

            # otherwise, get the namespace that should contain the value of this
            # expression
            else:

                nspace = _get_namespace ()

                # check that this variable exists in the current namespace
                if variable not in nspace:

                    self._logger.critical (" Variable '%s' has not been found!" % variable)
                    raise ValueError

                # and return its value
                return nspace [variable]


        def _apply_regexp (s, regexp, groupname):
            """
            returns all matches in s of the given regexp and returns the values
            of the specified group.

            it returns either a single string or a list of strings in case there
            is an arbitrary number of matches strictly greater than 1
            """

            # initialization
            values = list ()

            # for all matches of the given regexp in s
            for imatch in re.finditer (regexp, s):

                # add the value of the specified group to the list of values
                values.append (imatch.group (groupname))

            # in case there is just a single match return just that string
            if len (values) == 1:
                return values [0]

            # otherwise, return the list of values
            return values


        #
        # ---------------------------------------------------------------------
        # first case: the expression given has no context
        if not self._hascontext:

            return _eval_without_context (self._expression)

        # otherwise, in case it has a context
        else:

            # first of all, evaluate the first context and store its value in
            # an ancilliary variable
            currvalue = _eval_without_context (self._contexts [0])

            # process all contexts one after another but the first one ---this
            # shall be all regular expressions!
            for icontext in self._contexts[1:]:

                # compute the prefix and variable of this expression
                (regexp, group) = string.split (icontext, '.')
                sregexp = dbspec.get_regexp (regexp).get_specification ()

                # Check whether the current value consists of a scalar or a list
                # of values
                if isinstance (currvalue, str):

                    # if it is a string just compute the value that results by
                    # applying the corresponding specification
                    currvalue = _apply_regexp (currvalue,
                                               sregexp,
                                               group)

                    # in case there was no match return None
                    if not currvalue:
                        currvalue = None

                else:

                    # in case it is a list of strings, then process each
                    # separately, getting rid of all empty lists
                    newvalue = list ()
                    for ivalue in currvalue:
                        result = _apply_regexp (ivalue, sregexp, group)
                        if result:
                            newvalue.append (result)
                    if not newvalue:
                        currvalue = None
                    else:
                        currvalue = newvalue

            # and return the final value of processing all contexts
            return currvalue



# Local Variables:
# mode:python
# fill-column:80
# End:
