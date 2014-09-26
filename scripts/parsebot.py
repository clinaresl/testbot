#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# parsebot.py
# Description: automatically parses any collection of text files and records
#              various data using the services provided by autobot
# -----------------------------------------------------------------------------
#
# Started on  <Fri Sep 19 16:30:12 2014 Carlos Linares Lopez>
# Last update <viernes, 26 septiembre 2014 18:13:21 Carlos Linares Lopez (clinares)>
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
automatically parses any collection of text files and records various
data using the services provided by autobot
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import logging                          # loggers

from autobot.bots import BotMain        # main service
from autobot.bots import BotAction      # automated pre/post actions
from autobot import BotParser           # automated parsing
from autobot import logutils            # utilities to configure loggers
from autobot import parsetools          # default argument parser


# -----------------------------------------------------------------------------
# ParseBot
#
# Automated parsing of text files
# -----------------------------------------------------------------------------
class ParseBot (BotParser):
    """
    Automated parsing of text files
    """

    def setUp (self):
        """
        set up the environment. This method is executed only once before all the
        test_ methods
        """

        # --- parsing

        # parse arguments using a parser specifically designed for testbot
        self.args = parsetools.BotParseArgParser ().parse_args ()

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
        self.go (self.args.file,
                 self.args.db,
                 self.args.dbname,
                 directory=self.args.directory,
                 compress=self.args.bz2,
                 argnamespace=self.args,
                 output=self.args.output,
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
    Bot Action to be executed before parsing the first text file
    """

    def __call__ (self, logger):
        """
        Method invoked before parsing the first text file. It automatically
        inherits the values of the following attributes: dbfile, directory, the
        sys namespace and the user namespace

        This method provides additional information in case the debug level is
        requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
%s
 * dbfile    : %s
 * directory : %s
 * namespace :

%s

 * user namespace :

%s
""" % (self.__class__.__name__, self.dbfile, self.directory, self.namespace, self.user))


class Prologue (BotAction):
    """
    Bot Action to be executed before parsing every text file.
    """

    def __call__ (self, logger):
        """
        Method invoked before parsing every text file.. It automatically
        inherits the values of the following attributes: text file, dbfile,
        directory, startruntime, the sys namespace and the user namespace

        The Prologue is in charge of providing additional information in case
        the debug information level is requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
%s
 * text file     : %s
 * dbfile        : %s
 * directory     : %s
 * startruntiime : %s
 * namespace     :

%s

 * user namespace :

%s
""" % (self.__class__.__name__, self.textfile, self.dbfile, self.directory, self.startruntime, self.namespace, self.user))


class Epilogue (BotAction):
    """
    Bot Action to be executed after parsing every text file
    """

    def __call__ (self, logger):
        """
        Method invoked after parsing every text file. It automatically inherits
        the values of the following attributes: textfile, dbfile, direcftory,
        startruntime, endruntime, the sys namespace, the data namespace and the
        user namespace

        The Epilogue provides additional information in case the debug level is
        requested
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
%s
 * text file    : %s
 * dbfile       : %s
 * directory    : %s
 * startruntime : %s
 * endruntime   : %s
 * namespace    :

%s

 * data namespace :

%s

 * user namespace :

%s
""" % (self.__class__.__name__, self.textfile, self.dbfile, self.directory, self.startruntime, self.endruntime, self.namespace, self.data, self.user))


class WindUp (BotAction):
    """
    Bot Action to be executed after parsing the last text file
    """

    def __call__ (self, logger):
        """
        Method invoked after parsing the last text file. It automatically
        inherits the values of the following attributes: dbfile, directory, the
        sys namespace, the data namespace and the user namespace

        This method provides additional information in case the debug level has
        been requested.
        """

        childlogger = logger.getChild (self.__class__.__module__ + '.' + self.__class__.__name__)
        childlogger.addFilter (logutils.ContextFilter ())
        childlogger.debug ("""
%s
 * dbfile    : %s
 * directory : %s
 * namespace :

%s

 * data namespace :

%s

 * user namespace :

%s
""" % (self.__class__.__name__, self.dbfile, self.directory, self.namespace, self.data, self.user))


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    BotMain (module='parsebot', classdef=BotParser)


# Local Variables:
# mode:python
# fill-column:80
# End:
