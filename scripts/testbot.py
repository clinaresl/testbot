#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# testbot.py
# Description: automatically executes any program and records various data using
#              the services provided by autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 12 12:52:22 2012 Carlos Linares Lopez>
# Last update <jueves, 18 septiembre 2014 13:41:39 Carlos Linares Lopez (clinares)>
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
import datetime                         # date and time services
import getpass                          # getuser
import logging                          # loggers
import os                               # path mgmt
import socket                           # gethostname

from autobot import colors              # tty colors
from autobot.bots import BotMain        # main service
from autobot.bots import BotAction      # automated pre/post actions
from autobot.bots import BotTestCase    # automated full execution
from autobot import parsetools          # default argument parser


# -----------------------------------------------------------------------------
# configure_logger
#
# opens a file in write mode in the specified directory in case a logfile is
# given. If not, it creates a basic logger. Messages above the given level are
# issued.
# -----------------------------------------------------------------------------
def configure_logger (directory, logfile, level):

    """
    opens a file in write mode in the specified directory in case a logfile is
    given. If not, it creates a basic logger. Messages above the given level are
    issued
    """

    # create the log file either as a file stream or a stream handler
    if (logfile):

        # if a filename is specified, append the current date and time
        logfilename = logfile + '.' + datetime.datetime.now ().strftime ("%y-%m-%d.%H:%M:%S")
        logging.basicConfig (filename=os.path.abspath (os.path.join (directory, logfilename)),
                             filemode = 'w', level=level,
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s\n")

    else:
        logfilename = ''
        logging.basicConfig (level=level,
                             format="%(color)s[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s\n")


# -----------------------------------------------------------------------------
# ContextFilter
#
# creates contextual information to be used in all the log messages issued in
# this module
# -----------------------------------------------------------------------------
class ContextFilter(logging.Filter):
    """
    defines contextual information to be passed to other modules
    """

    def filter(self, record):
        """
        Defines the additional information (color, node and user) that is set up
        in the logger configuration
        """

        record.node = socket.gethostname ()
        record.user = getpass.getuser ()

        if record.levelname == 'DEBUG':
            record.color = colors.darkwhite
        elif record.levelname == 'INFO':
            record.color = colors.bluesea
        elif record.levelname == 'WARNING':
            record.color = colors.yellow
        elif record.levelname == 'ERROR':
            record.color = colors.red
        elif record.levelname == 'CRITICAL':
            record.color = colors.red
        else:
            record.color = colors.white

        return True


# -----------------------------------------------------------------------------
# TestBot
#
# Execution of a particular test case that can involve various executions
# -----------------------------------------------------------------------------
class TestBot (BotTestCase):
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
        self.args = parsetools.BotArgParser ().parse_args ()

        # convert properly the memory allotted from Gb to bytes
        self.args.memory *= 1024**3

        # --- logging

        # configure the main logger
        configure_logger (self.args.directory, self.args.logfile, self.args.level)
        self.logger = logging.getLogger (self.__class__.__module__ + '.' +
                                         self.__class__.__name__)
        self.logger.addFilter (ContextFilter ())

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
                 logfilter=ContextFilter (),
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
        childlogger.addFilter (ContextFilter ())
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
        childlogger.addFilter (ContextFilter ())
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
        childlogger.addFilter (ContextFilter ())
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
        childlogger.addFilter (ContextFilter ())
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

    BotMain (module='testbot')


# Local Variables:
# mode:python
# fill-column:80
# End:
