#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# autobot.py
# Description: General framework for starting services from the testbot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 21:27:32 2013 Carlos Linares Lopez>
# Last update <sábado, 14 diciembre 2013 00:31:07 Carlos Linares Lopez (clinares)>
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
__date__     = '$Date:$'


# imports
# -----------------------------------------------------------------------------
import getpass                  # getuser
import importlib                # importing modules
import inspect                  # inspect live objects
import logging                  # loggers
import re                       # regular expressions
import socket                   # gethostname

from collections import defaultdict

import parsetools

# -----------------------------------------------------------------------------
# BotLogger
#
# Provides various services for creating a logger and logging messages
# of different kinds
# -----------------------------------------------------------------------------
class BotLogger ():
    """
    Provides various services for creating a logger and logging
    messages of different kinds
    """

    # Static members

    # Extra parameters used by the logger
    # -----------------------------------------------------------------------------
    _logdict = {'node': socket.gethostname (),
                'user': getpass.getuser ()}

    # -----------------------------------------------------------------------------
    # create_logger
    #
    # opens a file in write mode in the current working directory in case
    # a logfile is given. If not, it creates a basic logger. Messages
    # above the given level are issued.
    #
    # it returns the name of the logfile recording all logrecords. If none has been
    # created it returns the empty string
    # -----------------------------------------------------------------------------
    def create_logger (self, level='INFO', logfile=None):

        """
        opens a file in write mode in the current working directory in
        case a logfile is given. If not, it creates a basic
        logger. Messages above the given level are issued.

        it returns the name of the logfile recording all logrecords. If
        none has been created it returns the empty string
        """

        # create the log file either as a file stream or to the stdout
        if (logfile):

            logging.basicConfig (filename=logfile, filemode = 'w', level=level,
                                 format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")

        else:
            logging.basicConfig (level=level,
                                 format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")


    # -----------------------------------------------------------------------------
    # debug
    #
    # logs the debug message 'msg' through the given logger appending
    # the static member _logdict
    # -----------------------------------------------------------------------------
    def debug (self, logger, msg):

        """
        logs the debug message 'msg' through the given logger appending
        the static member _logdict
        """

        logger.debug (msg, extra=self._logdict)


    # -----------------------------------------------------------------------------
    # info
    #
    # logs the info message 'msg' through the given logger appending
    # the static member _logdict
    # -----------------------------------------------------------------------------
    def info (self, logger, msg):

        """
        logs the info message 'msg' through the given logger appending
        the static member _logdict
        """

        logger.info (msg, extra=self._logdict)


    # -----------------------------------------------------------------------------
    # warning
    #
    # logs the warning message 'msg' through the given logger
    # appending the static member _logdict
    # -----------------------------------------------------------------------------
    def warning (self, logger, msg):

        """
        logs the warning message 'msg' through the given logger
        appending the static member _logdict
        """

        logger.warning (msg, extra=self._logdict)


    # -----------------------------------------------------------------------------
    # error
    #
    # logs the error message 'msg' through the given logger appending
    # the static member _logdict
    # -----------------------------------------------------------------------------
    def error (self, logger, msg):

        """
        logs the error message 'msg' through the given logger
        appending the static member _logdict
        """

        logger.error (msg, extra=self._logdict)


    # -----------------------------------------------------------------------------
    # critical
    #
    # logs the critical message 'msg' through the given logger
    # appending the static member _logdict
    # -----------------------------------------------------------------------------
    def critical (self, logger, msg):

        """
        logs the critical message 'msg' through the given logger
        appending the static member _logdict
        """

        logger.critical (msg, extra=self._logdict)


# -----------------------------------------------------------------------------
# BotTestCase
#
# Base class of all testbots. This class is equipped with an argument
# parser that can be reused/extended and it also provides various
# logging services
# -----------------------------------------------------------------------------
class BotTestCase (object):
    """
    Base class of all testbots. This class is equipped with an
    argument parser that can be reused/extended and it also provides
    various logging services
    """

    # arguments parser
    # -----------------------------------------------------------------------------
    _parser = parsetools.BotArgParser ()

    # logging services
    # -----------------------------------------------------------------------------
    # set up the configuration of the default logger
    logging.basicConfig (level='INFO',
                         format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")

    # and now provide various services to access the logger
    def create_logger (self, level='INFO', logfile=None): BotLogger ().create_logger (level, logfile)
    def debug (self, logger, msg): BotLogger ().debug (logger, msg)
    def info (self, logger, msg): BotLogger ().info (logger, msg)
    def warning (self, logger, msg): BotLogger ().warning (logger, msg)
    def error (self, logger, msg): BotLogger ().error (logger, msg)
    def critical (self, logger, msg): BotLogger ().critical (logger, msg)

    # -----------------------------------------------------------------------------
    # go
    #
    # main service provided by this class. It automates the whole execution
    # -----------------------------------------------------------------------------
    def go (self):
        """
        main service provided by this class. It automates the whole execution
        """

        # print _logger
        logger=logging.getLogger ('BotTestCase::go')
        self.info (logger, "\t\t gotest!! go, go!!!")


# -----------------------------------------------------------------------------
# BotLoader
#
# This class is responsible of processing all classes in the given
# module and to return all of those that are children of BotTestCase
# along with the methods that should be executed
# -----------------------------------------------------------------------------
class BotLoader:
    """
    This class is responsible of processing all classes in the given
    module and to return all of those that are children of BotTestCase
    along with the methods that should be executed
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

            # create an instance of this class so that methods will be
            # bounded
            instance = self._classes [classname] ()

            # first, execute the setUp method if any was defined
            setUp = getattr (self._classes [classname], 'setUp', False)
            if setUp:
                instance.setUp ()

            # now execute all methods in this class
            for method in methodList:

                # we go through the descriptors of our instance to bind the
                # method to our instance and then to execute it
                method.__get__ (instance, self._classes [classname]) ()

            # tearing down, if given
            tearDown = getattr (self._classes [classname], 'tearDown', False)
            if tearDown:
                instance.tearDown ()

            print



# Local Variables:
# mode:python
# fill-column:80
# End:
