#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# autobot.py
# Description: General framework for starting services from the testbot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 21:27:32 2013 Carlos Linares Lopez>
# Last update <jueves, 12 diciembre 2013 11:29:17 Carlos Linares Lopez (clinares)>
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
General framework for starting services from the testbot
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import importlib                # importing modules
import inspect                  # inspect live objects
import re                       # regular expressions

from collections import defaultdict


# -----------------------------------------------------------------------------
# BotTestCase
#
# Base class of all testbots
# -----------------------------------------------------------------------------
class BotTestCase:
    """
    Base class of all testbots
    """

    def __init__ (self):
        pass

    def gotest (self):
        """
        main service provided by this class. It automates the whole execution
        """

        print "\t\t gotest!! go, go!!!"


# -----------------------------------------------------------------------------
# BotLoader
#
#
# -----------------------------------------------------------------------------
class BotLoader:
    """
    This class is loads all classes in the given module that are
    children of BotTestCase
    """

    _botTestre = 'test_'

    def loadTestsFromModule (self, module):
        """
        Browse all the definitions in the given module and process those classes
        that are descendants of BotTestCase. 'module' is the module object
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
        # BotTestCase
        self._classes = filter (lambda x:issubclass (x[1], BotTestCase),
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
# This class provides the main definitions for accessing the services
# provided by testbot
# -----------------------------------------------------------------------------
class BotMain:
    """
    This class provides the main definitions for accessing the
    services provided by the testbot
    """

    def __init__ (self, module='__main__'):
        """
        Process the parameters of this session retrieving the test
        functions to execute
        """

        # retrieve the module to process
        self._module = importlib.import_module (module)

        # get all the test cases to execute
        (self._classes, self._methods) = BotLoader ().loadTestsFromModule (self._module)

        # and execute all methods
        for classname, methodList in self._methods.items ():

            print " Processing class %s" % classname

            # first, execute the setUp method if any was defined
            setUp = getattr (self._classes [classname], 'setUp', False)
            if setUp:
                setUp.im_func (BotTestCase)

            # now execute all methods in this class
            for method in methodList:
                method.im_func (BotTestCase)

            # tearing down, if given
            tearDown = getattr (self._classes [classname], 'tearDown', False)
            if tearDown:
                tearDown.im_func (BotTestCase)

            print

        # and execute all methods
        # for classdef, methoddef in self._tests:
        #     setUp = getattr (classdef, 'setUp', False)

        #     if setUp :
        #         print " setting up ..."

        #     methoddef.im_func (BotTestCase)

        #     tearDown = getattr (classdef, 'tearDown', False)

        #     if tearDown :
        #         print " tearing down ..."



# Local Variables:
# mode:python
# fill-column:80
# End:
