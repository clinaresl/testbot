#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# testbot.py
# Description: automatically executes any program and records various data using
#              the services provided by autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 12 12:52:22 2012 Carlos Linares Lopez>
# Last update <viernes, 26 septiembre 2014 00:15:46 Carlos Linares Lopez (clinares)>
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
automatically executes any program and records various data using the services
provided by autobot
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '2.0'
__revision__ = '$Revision:$'
__date__     = '$Date:$'


# imports
# -----------------------------------------------------------------------------
import logging                          # loggers

from autobot.bots import BotMain        # main service
from autobot.bots import BotAction      # automated pre/post actions
from autobot import BotTester           # automated full execution
from autobot import logutils            # utilities to configure loggers
from autobot import parsetools          # default argument parser


# -----------------------------------------------------------------------------
# TestBot
#
# Execution of a particular test case that can involve various executions
# -----------------------------------------------------------------------------
class TestBot (BotTester):
    """
    Execution of a particular test case that can involve various executions
    """

    def setUp (self):
        """
        set up the environment. This method is executed only once before all the
        test_ methods
        """

        # --- parsing

        # parse arguments using a parser specifically designed for testbot
        self.args = parsetools.BotTestArgParser ().parse_args ()

        # convert properly the memory allotted from Gb to bytes
        self.args.memory *= 1024**3

        # --- logging

        # configure the main logger
        logutils.configure_logger (self.args.directory, self.args.logfile, self.args.level)
        self.logger = logging.getLogger (self.__class__.__module__ + '.' +
                                         self.__class__.__name__)
        self.logger.addFilter (logutils.ContextFilter ())

        self.logger.debug (" setUp finished")


    def test_case (self):
        """
        test case - it just invokes the autobot with all the information passed
        in the command line
        """

        # invoke the main service provided by autobot
        self.go (self.args.solver,
                 self.args.tests,
                 self.args.db,
                 self.args.timeout,
                 self.args.memory,
                 argnamespace=self.args,
                 output=self.args.output,
                 check=self.args.check,
                 directory=self.args.directory,
                 compress=self.args.bz2,
                 logger=self.logger,
                 logfilter=logutils.ContextFilter (),
                 prologue=Prologue,
                 epilogue=Epilogue,
                 enter=Enter,
                 windUp=WindUp,
                 quiet=self.args.quiet)


    def tearDown (self):
        """
        wrap up the execution environment. This is executed only once before
        exiting
        """

        self.logger.debug (" Exiting from the testbot ...")


class Enter (BotAction):
    """
    Bot Action to be executed before every invocation of the solver with the
    very first test case
    """

    def __call__ (self, logger):
        """
        Method invoked before the execution of the solver with the very first
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, dbspec, timeout, memory, check, basedir,
        resultsdir, compress, namespace, user namespace and stats.

        This method provides additional information in case the debug level is
        requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
 %s:
 * solver      : %s
 * timeout     : %d seconds
 * memory      : %d bytes
 * check       : %.2f seconds
 * basedir     : %s
 * resultsdir  : %s
 * compress    : %s
 * namespace   :

%s

 * user namespace:

%s""" % (self.__class__.__name__, self.solver, self.timeout, self.memory, self.check, self.basedir, self.resultsdir, self.compress, self.namespace, self.user))


class Prologue (BotAction):
    """
    Bot Action to be executed before every invocation of the solver with every
    test case
    """

    def __call__ (self, logger):
        """
        Method invoked before the execution of the solver with regard to every
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, itest, dbspec, timeout, memory, output,
        check, basedir, resultsdir, compress, namespace, user namespace, param
        namespace, stats and startruntime.

        The Prologue is in charge of providing additional information in case
        the debug information level is requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
 %s:
 * solver      : %s
 * itest       : %s
 * timeout     : %d seconds
 * memory      : %d bytes
 * output      : %s
 * check       : %.2f seconds
 * basedir     : %s
 * resultsdir  : %s
 * compress    : %s
 * startruntime: %i
 * namespace   :

%s

 * user namespace:

%s

 * param namespace:

%s""" % (self.__class__.__name__, self.solver, self.itest, self.timeout, self.memory, self.output, self.check, self.basedir, self.resultsdir, self.compress, self.startruntime, self.namespace, self.user, self.param))


class Epilogue (BotAction):
    """
    Bot Action to be executed after every invocation of the solver with every
    test case
    """

    def __call__ (self, logger):
        """
        Method invoked after the execution of the solver with regard to every
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, itest, dbspec, timeout, memory, output,
        check, basedir, resultsdir, compress, namespace, data namespace, user
        namespace, param namespace, regexp namespace, stats, startruntime and
        endruntime.

        The Epilogue provides additional information in case the debug level is
        requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
 %s:
 * solver      : %s
 * itest       : %s
 * timeout     : %d seconds
 * memory      : %d bytes
 * output      : %s
 * check       : %.2f seconds
 * basedir     : %s
 * resultsdir  : %s
 * compress    : %s
 * startruntime: %i
 * endruntime  : %i
 * namespace   :

%s

 * data namespace:

%s

 * user namespace:

%s

 * param namespace:

%s

 * regexp namespace:

%s""" % (self.__class__.__name__, self.solver, self.itest, self.timeout, self.memory, self.output, self.check, self.basedir, self.resultsdir, self.compress, self.startruntime, self.endruntime, self.namespace, self.data, self.user, self.param, self.regexp))


class WindUp (BotAction):
    """
    Bot Action to be executed after the execution of the current solver on the
    last test case
    """

    def __call__ (self, logger):
        """
        Method invoked after the execution of the current solver with the last
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, dbspec, timeout, memory, check, basedir,
        resultsdir, compress, namespace, data namespace, user namespace regexp
        namespace and stats.

        This method provides additional information in case the debug level has
        been requested.
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
 %s:
 * solver      : %s
 * timeout     : %d seconds
 * memory      : %d bytes
 * check       : %.2f seconds
 * basedir     : %s
 * resultsdir  : %s
 * compress    : %s
 * namespace   :

%s

 * data namespace:

%s

 * user namespace:

%s

 * regexp namespace:

%s""" % (self.__class__.__name__, self.solver, self.timeout, self.memory, self.check, self.basedir, self.resultsdir, self.compress, self.namespace, self.data, self.user, self.regexp))


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    BotMain (module='testbot', classdef=BotTester)


# Local Variables:
# mode:python
# fill-column:80
# End:
