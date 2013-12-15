#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# testcase.py
# Description: testing the autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 22:09:24 2013 Carlos Linares Lopez>
# Last update <domingo, 15 diciembre 2013 15:40:04 Carlos Linares Lopez (clinares)>
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
    Dummy class that should not be invoked by autobot
    """

    def __init__ (self):
        pass

    def test_one (self):

        pass

    def test_two (self):
        pass


class TestCaseOne (autobot.BotTestCase):
    """
    Definition of an automated test case. It modifies the default parser
    provided by autobot and it also invokes its main service: go
    """

    def setUp (self):

        # parsing - add a new option to the parser and create a new group with a
        # new action
        self._parser._optional.add_argument ('-M','--think!',action='store_true')
        newgroup = self._parser._parser.add_argument_group ('New group')
        newgroup.add_argument ('-I', '--be-imaginative',type=int, default=3)
        self.args = self._parser.parse_args ()

        # convert properly the memory allotted from Gb to bytes
        self.args.memory *= 1024**3

        # logging
        logger = logging.getLogger('TestCaseOne::setUp')
        self.info (logger, " Info message issued from setUp")

    def test_firstcase (self):

        logger = logging.getLogger ('TestCaseOne::test_firstcase')
        self.info (logger, " Testing the first case ... ")

        # invoke the main service provided by autobot
        self.go (self.args.solver, self.args.tests, self.args.db, self.args.time,
                 self.args.memory, self.args.output, self.args.check, self.args.directory,
                 self.args.bz2, self.args.quiet)


    def test_secondcase (self):

        logger = logging.getLogger ('TestCaseOne::test_secondcase')
        self.info (logger, " Testing the second case ... ")


    def tearDown (self):

        logger = logging.getLogger ('TestCaseOne::tearDown')
        self.info (logger, " Info message issued from tearDown")


class TestCaseTwo (autobot.BotTestCase):
    """
    Definition of an automated test case that should absolutely nothing but
    printing messages
    """

    def test_dummy (self):

        logger = logging.getLogger ('TestCaseTwo::test_dummy')
        self.info (logger, " Doing nothing ...")

    def tearDown (self):

        pass


def _cmplen (methodA, methodB):
    
    if   len (methodA.__name__) < len(methodB.__name__): return -1
    elif len (methodA.__name__) > len(methodB.__name__): return +1
    return 0



# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    autobot.BotMain (module='testexample', cmp=_cmplen)


# Local Variables:
# mode:python
# fill-column:80
# End:
