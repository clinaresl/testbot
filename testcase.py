#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# testcase.py
# Description: testing the autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 22:09:24 2013 Carlos Linares Lopez>
# Last update <domingo, 15 diciembre 2013 01:15:22 Carlos Linares Lopez (clinares)>
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
testing the autobot
"""

__version__  = '1.0'
__revision__ = '$Revision$'

import autobot
import logging

class Dummy:
    """
    Dummy class
    """

    def __init__ (self):
        pass

    def test_one (self):

        pass

    def test_two (self):
        pass


class TestCaseOne (autobot.BotTestCase):
    """
    Definition of an automated test case
    """

    def setUp (self):

        # parsing
        self._parser._optional.add_argument ('-M','--yujuju',action='store_true')
        newgroup = self._parser._parser.add_argument_group ('New group')
        newgroup.add_argument ('-I', '--be-imaginative',type=int, default=3)
        self.args = self._parser.parse_args ()

        # convert properly the memory allotted from Gb to bytes
        self.args.memory *= 1024**3

        # logging
        self.create_logger (level='DEBUG', logfile='kk')
        logger = logging.getLogger('TestCaseOne::setUp')
        self.debug (logger, "Esto es un mensaje de depuracion desde setUp")
        self.info (logger, "Esto es un mensaje de informacion desde setUp")

    def test_domains (self):

        logger = logging.getLogger ('TestCaseOne::test_domains')
        self.info (logger, "\t testing domains ... ")

        self.go (self.args.solver, self.args.tests, self.args.db, self.args.time,
                 self.args.memory, self.args.output, self.args.check, self.args.directory,
                 self.args.bz2, self.args.quiet)


    def test_planners (self):

        logger = logging.getLogger ('TestCaseOne::test_planners')
        self.info (logger, "\t testing planners ... ")


    def tearDown (self):

        logger = logging.getLogger ('TestCaseOne::tearDown')
        self.info (logger, "\t tearing down in test case #1")



# class TestCaseTwo (autobot.BotTestCase):
#     """
#     Definition of an automated test case
#     """

#     def test_suite (self):

#         print "\t Executing test suite ..."
#         autobot.BotTestCase ().go ()

#     def tearDown (self):

#         print "\t tearing down in the second test case"


if __name__ == '__main__':

    autobot.BotMain (module='testcase')


# Local Variables:
# mode:python
# fill-column:80
# End:
