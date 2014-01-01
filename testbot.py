#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# testbot.py
# Description: automatically executes any program and records various data using
#              the services provided by autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 12 12:52:22 2012 Carlos Linares Lopez>
# Last update <mi�rcoles, 01 enero 2014 22:29:10 Carlos Linares Lopez (clinares)>
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
import parsetools               # argument parser

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

        # parse arguments
        # self.args = self._parser.parse_args ()
        self.args = parsetools.BotArgParser ().parse_args ()

        # convert properly the memory allotted from Gb to bytes
        self.args.memory *= 1024**3

    def test_case (self):

        # invoke the main service provided by autobot
        self.go (self.args.solver, self.args.tests, self.args.db, self.args.timeout,
                 self.args.memory, argnamespace=self.args,
                 output=self.args.output, check=self.args.check,
                 directory=self.args.directory, compress=self.args.bz2,
                 quiet=self.args.quiet)


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    autobot.BotMain (module='testbot')


# Local Variables:
# mode:python
# fill-column:80
# End:
