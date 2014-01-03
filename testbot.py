#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# testbot.py
# Description: automatically executes any program and records various data using
#              the services provided by autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 12 12:52:22 2012 Carlos Linares Lopez>
# Last update <viernes, 03 enero 2014 22:16:57 Carlos Linares Lopez (clinares)>
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

__version__  = '2.0'
__revision__ = '$Revision:$'
__date__     = '$Date:$'


# imports
# -----------------------------------------------------------------------------
import autobot                  # main facility for automating experimentation
import datetime                 # date and time services
import getpass                  # getuser
import logging                  # loggers
import os                       # path mgmt
import parsetools               # argument parser
import socket                   # gethostname


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
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s\n")


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
        Defines the additional information (node and user) that is set up in the
        logger configuration
        """

        record.node = socket.gethostname ()
        record.user = getpass.getuser ()
        return True


# -----------------------------------------------------------------------------
# TestCase
#
# Execution of a particular test case that can inivolve various executions
# -----------------------------------------------------------------------------
class TestBot (autobot.BotTestCase):
    """
    Execution of a particular test case that can inivolve various executions
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
        self.go (self.args.solver, self.args.tests, self.args.db, self.args.timeout,
                 self.args.memory, argnamespace=self.args,
                 output=self.args.output, check=self.args.check,
                 directory=self.args.directory, compress=self.args.bz2,
                 logger=self.logger, logfilter=ContextFilter (),
                 prologue = Prologue, epilogue= Epilogue,
                 quiet=self.args.quiet)


    def tearDown (self):
        """
        wrap up the execution environment. This is executed only once before
        exiting
        """

        self.logger.debug (" Exiting from the testbot ...")



class Prologue (autobot.BotAction):
    """
    Bot Action to be executed before every invocation of the solver with every
    test case
    """

    def __call__ (self, logger):
        """
        Method invoked before the execution of the solver with regard to every
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, itest, dbspec, time, memory, output, check,
        resultsdir, compress and placeholders (which is a dictionary with all
        variables used for filling the database)
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (ContextFilter ())
        childlogger.debug (""" Prologue:
 * solver      : %s
 * itest       : %s
 * time        : %d seconds
 * memory      : %d bytes
 * output      : %s
 * check       : %d seconds
 * resultsdir  : %s
 * compress    : %s
 * placeholders: %s
""" % (self.solver, self.itest, self.time, self.memory, self.output, self.check, self.resultsdir, self.compress, self.placeholders))

        self.placeholders ['dummy'] = 'testing the prologue/epilogue'


class Epilogue (autobot.BotAction):
    """
    Bot Action to be executed after every invocation of the solver with every
    test case
    """

    def __call__ (self, logger):
        """
        Method invoked before the execution of the solver with regard to every
        test case. It automatically inherits the values of the following
        attributes: solver, tstspec, itest, dbspec, time, memory, output, check,
        resultsdir, compress and placeholders (which is a dictionary with all
        variables used for filling the database)
        """
        
        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (ContextFilter ())
        childlogger.debug (""" Epilogue:
 * solver      : %s
 * itest       : %s
 * time        : %d seconds
 * memory      : %d bytes
 * output      : %s
 * check       : %d seconds
 * resultsdir  : %s
 * compress    : %s
 * placeholders: %s
""" % (self.solver, self.itest, self.time, self.memory, self.output, self.check, self.resultsdir, self.compress, self.placeholders))



# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    autobot.BotMain (module='testbot')


# Local Variables:
# mode:python
# fill-column:80
# End:
