#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# bots.py
# Description: General framework for starting services from the testbot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 21:27:32 2013 Carlos Linares Lopez>
# Last update <viernes, 26 septiembre 2014 00:42:52 Carlos Linares Lopez (clinares)>
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
General framework for starting services from the testbot
"""

__version__  = '2.0'
__revision__ = '$Revision$'
__date__     = '$Date:$'


# imports
# -----------------------------------------------------------------------------
import importlib                # importing modules
import inspect                  # inspect live objects
import re                       # regular expressions

from collections import defaultdict


# -----------------------------------------------------------------------------
# BotAction
#
# autbot receives either an arbitrary selection of solvers and test cases (the
# former is given in the command line while the latter is specified in a test
# specification file) or an arbitrary specification of text files to
# parse. Let "experiment" denote the execution of a particular solver (among
# an arbitrary large collection of them) over its tests cases or the parsing
# process of all text files. Similarly, let "run" denote a particular
# execution of a solver over a given test case or the parsing process of a
# single text file.
#
# autobot implements the following execution flow: before an experiment is
# started it first invokes an *enter* action and it invokes a *windUp* action
# when the experiment is over. Similary, a *prologue* action is invoked before
# every run and an *epilogue* action is invoked immediately after.
#
# To allow further flexibility these actions are implemented as subclasses of
# BotAction which have to implement __call__. If these functions are provided
# then the corresponding subclass is invoked with all the variables that
# define the current environment of the execution.
# -----------------------------------------------------------------------------
class BotAction (object):
    """
    autbot receives either an arbitrary selection of solvers and test cases (the
    former is given in the command line while the latter is specified in a test
    specification file) or an arbitrary specification of text files to
    parse. Let "experiment" denote the execution of a particular solver (among
    an arbitrary large collection of them) over its tests cases or the parsing
    process of all text files. Similarly, let "run" denote a particular
    execution of a solver over a given test case or the parsing process of a
    single text file.

    autobot implements the following execution flow: before an experiment is
    started it first invokes an *enter* action and it invokes a *windUp* action
    when the experiment is over. Similary, a *prologue* action is invoked before
    every run and an *epilogue* action is invoked immediately after.

    To allow further flexibility these actions are implemented as subclasses of
    BotAction which have to implement __call__. If these functions are provided
    then the corresponding subclass is invoked with all the variables that
    define the current environment of the execution.
    """

    def __init__ (self, **kws):
        """
        stores the values of all the given keywords in kws as attributes of this
        class
        """

        # set the attributes of this class according to the dictionary given in
        # kws
        for k in kws:
            setattr (self, k, kws[k])


    def __call__(self, itest):
        raise NotImplementedError ('__call__() not defined')


# -----------------------------------------------------------------------------
# BotLoader
#
# This class is responsible of processing all classes in the given module and to
# return all of those that are children of the given class along with the
# methods that should be executed
# -----------------------------------------------------------------------------
class BotLoader:
    """
    This class is responsible of processing all classes in the given module and
    to return all of those that are children of the given class along with the
    methods that should be executed
    """

    _botTestre = 'test_'

    def loadTestsFromModule (self, module, classdef):
        """
        Browse all the definitions in the given module and process those classes
        that are descendants of classdef. 'module' is the module object
        properly imported. It returns a tuple with a couple of dictionaries. The
        first one provides the definition of all classes that contain methods to
        execute. The second one contains the (unbound) methods that have to be
        executed within every class
        """

        # initialization
        classDict = {}
        methodsDict = defaultdict (list)

        # Retrieve all classes defined in the given module. getmembers
        # return tuples of the form (name, value) so that all values
        # are processed to preserve only those that are inherited from
        # the given class
        self._classes = filter (lambda x:issubclass (x[1], classdef),
                                inspect.getmembers (module,
                                                    lambda x:inspect.isclass (x)))

        # process every class looking for methods matching botTestre and create
        # a dictionary which stores the methods to execute (value) of every
        # class (key)
        for classname, classdef in self._classes:

            # get its members
            for member, methoddef in inspect.getmembers (classdef):

                if (re.match (self._botTestre, member)):
                    classDict [classname] = classdef
                    methodsDict [classname].append (methoddef)

        # and return both dictionaries
        return (classDict, methodsDict)


# -----------------------------------------------------------------------------
# BotMain
#
# This class provides the main definitions for accessing the services provided
# by testbot
# -----------------------------------------------------------------------------
class BotMain:
    """
    This class provides the main definitions for accessing the services provided
    by the testbot
    """

    def __init__ (self, module, classdef, cmp=None):
        """
        Process the parameters of this session from the given module retrieving
        the test functions to execute which are defined as methods in the given
        class. Valid class definitions are BotTester and BotParser

        Test functions are sorted according to cmp. If it equals None then they
        are sorted in ascending order of the lexicographical order
        """

        def _cmp (methodA, methodB):
            """
            Returns -1, 0 or +1 if depending on whether the first argument is
            smaller, equal or larger than the second argument. 'methodA' and
            'methodB' are method implementations so that their names are accessed
            through __name__
            """

            if methodA.__name__ < methodB.__name__: return -1
            elif methodA.__name__ > methodB.__name__:   return +1
            return 0


        # retrieve the module to process
        self._module = importlib.import_module (module)

        # get all the test cases to execute --- classes is a dictionary of names
        # to defs and methods is another dictionary of class names to method
        # implementations
        (self._classes, self._methods) = BotLoader ().loadTestsFromModule (self._module, classdef)

        # and execute all methods
        for classname, methodList in self._methods.items ():

            # create an instance of this class so that methods will be
            # bounded
            instance = self._classes [classname] ()

            # first, execute the setUp method if any was defined
            setUp = getattr (self._classes [classname], 'setUp', False)
            if setUp:
                instance.setUp ()

            # sort the methods in ascending order according to cmp. If no
            # comparison function is given then sort them lexicographically in
            # ascending order
            if (not cmp):
                cmp = _cmp
            methodList = sorted (methodList, cmp=lambda x,y: cmp (x, y))

            # now execute all methods in this class
            for method in methodList:

                # we go through the descriptors of our instance to bind the
                # method to our instance and then to execute it
                method.__get__ (instance, self._classes [classname]) ()

            # tearing down, if given
            tearDown = getattr (self._classes [classname], 'tearDown', False)
            if tearDown:
                instance.tearDown ()



# Local Variables:
# mode:python
# fill-column:80
# End:
