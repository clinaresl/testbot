#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# dbexpression.py
# Description: DBExpression implements the main services for evaluating database
#              expressions with data in different namespaces
# -----------------------------------------------------------------------------
#
# Started on  <Sun Sep 28 00:22:50 2014 Carlos Linares Lopez>
# Last update <lunes, 20 octubre 2014 00:45:04 Carlos Linares Lopez (clinares)>
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
# Definition of a database expression.
#
# Database expression provide facilities for updating namespaces with the
# results of some particular expressions (such as snippets) and also to resolve
# the value of an expression (such as a regexp) provided that the namespaces
# have the values of all the involved variables
# -----------------------------------------------------------------------------
class DBExpression:
    """
    Definition of a database expression.

    Database expression provide facilities for updating namespaces with the
    results of some particular expressions (such as snippets) and also to
    resolve the value of an expression (such as a regexp) provided that the
    namespaces have the values of all the involved variables
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

        # copy the expression (and its type) given to this instance
        self._type, self._expression, self._logfilter = \
          (exptype, expression, logfilter)

        # Do this expression contain a context? If so, process them in a list
        if string.count (expression, dbparser.DBParser.t_SLASH) > 0:
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


    def eval_snippet (self, dbspec, sys, data, param, regexp, snippet, user):
        """
        evaluates the expression stored in this instance which is certainly
        known to be a snippet.

        The evaluation of a snippet goes through the following steps:

        1. It first initializes a dictionary of globals with the values of all
           input variables specified in the snippet. Importantly, the
           initialization includes a casting operation to types explicitly
           declared by the user

        2. It then compiles the code specified in the snippet and evaluates the
           resulting object.

        3. It finally updates the snippet namespace with the information of the
           output variables specified in the definition of the snippet

        Thus, this method actually modifies the snippet namespace whereas it
        uses all the other namespaces for retrieving data
        """

        def _cast_value (value, itype):
            """
            converts the given value to the specified type
            """

            if itype == "text": value = str (value)
            elif itype == "integer": value = int (value)
            elif itype == "real": value = float (value)
            else:
                self._logger.error (" Unknown type '%s'" % itype)
                raise TypeError

            return value


        # Get information about the snippet whose name is specified in the
        # expression under evaluation
        (prefix, variable) = string.split (self._expression, '.')
        isnippet = dbspec.get_snippet (prefix)

        # Step #1
        # ---------------------------------------------------------------------
        # first step, initialize a dictionary with the values of all the input
        # variables casted to their respective types as specified by the user
        dglobals = {}

        # for every input variable, compute its value and update the dictionary
        # of globals
        for ivariable in isnippet.get_inputvars ():

            # simply create a dbexpression and requests its evaluation
            result = DBExpression (ivariable.get_vartype (),
                                   ivariable.get_variable (),
                                   self._logger, self._logfilter).eval (dbspec,
                                                                        sys,
                                                                        data,
                                                                        param,
                                                                        regexp,
                                                                        snippet,
                                                                        user)

            # cast this value to its corresponding type as specified by the
            # user. Two different cases are allowed: either the input variable
            # is a list or it is a scalar value. In the first case, all items
            # are casted, in the second one just the scalar is casted to the
            # desiredy type
            if isinstance (result, list):
                result = map (lambda x:_cast_value (x, ivariable.get_type ()),
                              result)
            else:
                result = _cast_value (result, ivariable.get_type ())

            # and now add this variable to the dictionary of globals
            dglobals [ivariable.get_identifier ()] = result

        # Step #2
        # ---------------------------------------------------------------------
        # compile the python file and execute it
        with open (isnippet.get_filecode ()) as stream:

            contents = stream.read ()
            fobject = compile (contents, isnippet.get_filecode (), 'exec')

            # and now evaluate its contants using the dictionary of globals
            # computed in the previous step
            eval (fobject, dglobals)

        # Step #3
        # ---------------------------------------------------------------------
        # retrieve data from the globals dictionary and update the snippet
        # namespace accordingly

        # Just write the data of all the output variables in a multi-key
        # attribute so that the same names can be used in output-variables of
        # different snippets (which are then distinguished by their
        # name). Compute the keys and values as the output variable names and
        # values returned by the evaluation of the snippet
        keys = tuple ([jvariable.get_identifier ()
                       for jvariable in isnippet.get_outputvars ()])
        values = [dglobals [jvariable.get_identifier ()]
                  for jvariable in isnippet.get_outputvars ()]

        # Now, declare this snippet as a multi-key attribute whose keys are the
        # output variables
        snippet.setkeynames (prefix, *keys)
        snippet.setattr (prefix,
                         key = dict (zip (keys, keys)),
                         value = [tuple (values)])


    def eval (self, dbspec, sys, data, param, regexp, snippet, user):
        """
        eval returns the evaluation of the expression stored in this
        instance. The evaluation is resolved with information of the regular
        expressions stored in the database specification, output variables of
        the snippets and data in the different namespaces given in the arguments.

        'sys', 'data', 'param', 'regexp', 'snippet' and 'user' are namespaces
        whose description is given in the bot that uses
        dbexpressions. Currently, eval maps different prefixes given to the
        expression to the different namespaces as follows:

        namespace   prefix
        ----------+------------------------------------
        sys       | sys. main.
        data      | data. file.
        param     | param. dir.
        regexp    | <regexp-name>.<group-name>
        snippet   | <snippet-name>.<variable-name>
        user      | user.
        ----------+------------------------------------

        'eval' affects neither the database specification nor the namespaces and
        they are used solely to retrieve data.

        The result of the evaluation can be either a scalar or a list of
        values. In case that the evaluation resolves to nothing eval returns
        None.

        eval also welcomes regular expressions which consist of an arbitrary
        number of contexts. The final value in this case is computed as the
        match of every regexp to the result of the previous evaluation. All
        contexts shall be regular expressions, but the first one which can be of
        any type but a regexp!

        eval might raise warnings and errors. Therefore, it receives a logger to
        show messages
        """

        def _get_namespace (atype = None):
            """
            return the namespace that should contain the values of a variable of
            the type of this instance or the given type if any.

            This function actually implements the logic that associates prefixes
            to namespaces as given above. In case no namespace is found for this
            particular type it returns None
            """

            # if no type is given, use the default type of this
            # instance. Otherwise, copy the specified one
            if atype:
                prefix = string.upper (atype)
            else:
                prefix = string.upper (self._type)

            if prefix == "SYS" or prefix == "MAIN": return sys
            elif prefix == "DATA" or prefix == "FILE": return data
            elif prefix == "PARAM" or prefix == "DIR": return param
            elif prefix == "REGEXP": return regexp
            elif prefix == "SNIPPET": return snippet
            elif prefix == "USER": return user
            else: return None


        def _retrieve (nspace, variable):
            """
            return the value of the given variable which should be accessed in
            the specified namespace. In case it does not exist, an error is
            raised
            """

            # check the given variable exists in the current namespace
            if variable not in nspace:

                self._logger.critical (" Variable '%s' has not been found!" % variable)
                raise ValueError

            # and return its value
            return nspace [variable]


        def _eval_without_context (expression):
            """
            returns the value of the given expression according to the
            namespaces given to 'eval'. This applies just to expressions without
            context or the first context of regular expressions with an
            arbitrary number of them
            """

            # -----------------------------------------------------------------
            # IMPORTANT: an expression should be the variable name (without any
            # reference to the namespace that contains it) in case they are
            # neither regexps nor snippets. Otherwise, they are qualified with
            # the name of the regexp/snippet and then the group name/output
            # variable separated by a dot.
            # -----------------------------------------------------------------

            # in case this is a regexp/snippet, then we have to compute the
            # projection over the given variable
            if self._type == "REGEXP" or self._type == "SNIPPET":

                # compute the prefix (either a regexp-name or a snippet-name)
                # and variable name of this expression
                (prefix, variable) = string.split (expression, '.')

                # If this instance is a regexp, maybe this refers to the first
                # context, which is not a regexp on its own. Thus, it is
                # mandatory now to check the real type of this argument
                nspace = _get_namespace (prefix)

                # in case this is proven to be either a regular expression or a
                # snippet---because its prefix refers to no known namespace,
                # then project it over the specified variable
                if not nspace:

                    # dissambiguate between the regexp and the snippet
                    # namespaces looking at the definitions of regexps and
                    # snippets instead of using the type of this instance
                    if dbspec.get_regexp (prefix):
                        result = regexp.projection (prefix, variable)
                    elif dbspec.get_snippet (prefix):
                        result = snippet.projection (prefix, variable)
                    else:
                        self._logger.critical (" The expression '%s' is neither a 'REGEXP' nor a 'SNIPPET'" % expression)
                        raise ValueError

                    # the result of a projection is a list with a tuple that
                    # contains the keys used for the projection and then a list
                    # of tuples with the values (also projected). We get rid
                    # here of the tuple of keys and we convert the list of
                    # tuples into a list of values
                    values = map (lambda x:x[0], result[1])

                    # also, in case this list consists of a single value we
                    # return it as a scalar
                    if len (values) == 1:
                        return values [0]
                    return values

                # otherwise, just retrieve the right value from the given
                # namespace
                else:
                    return _retrieve (nspace, variable)

            # otherwise, get the namespace that should contain the value of this
            # expression and return the value of this variable as stored in that
            # namespace
            else:

                return _retrieve (_get_namespace (), expression)


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


        # ---------------------------------------------------------------------
        # first case: the expression given has no context
        if not self._hascontext:

            return _eval_without_context (self._expression)

        # otherwise, in case it has a context
        else:

            # first of all, evaluate the first context and store its value in
            # an ancilliary variable
            currvalue = _eval_without_context (self._contexts [0])

            # process all contexts one after another but the first one ---these
            # shall be all regular expressions!
            for icontext in self._contexts[1:]:

                # compute the prefix and variable of this expression
                (regexp, group) = string.split (icontext, '.')
                sregexp = dbspec.get_regexp (regexp).get_specification ()

                # Check whether the current value consists of a scalar or a list
                # of values
                if isinstance (currvalue, (int, float, str)):

                    # there is no guarantee that this value is a string (maybe
                    # this is a value returned by a snippet). Enforce a
                    # conversion if necessary
                    if not isinstance (currvalue, str):
                        currvalue = str (currvalue)

                    # if it is a string just compute the value that results by
                    # applying the corresponding specification
                    currvalue = _apply_regexp (currvalue,
                                               sregexp,
                                               group)

                    # in case there was no match return None
                    if not currvalue:
                        currvalue = None

                else:

                    # in case it is a list, then process each item separately,
                    # getting rid of all empty lists
                    newvalue = list ()
                    for ivalue in currvalue:

                        # of course, it might happen that this particular value
                        # is not a string (e.g., it is returned by a snippet),
                        # in that case enforce the type conversion
                        if not isinstance (ivalue, str):
                            ivalue = str (ivalue)
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
