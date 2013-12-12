#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# testcase.py
# Description: testing the autobot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 22:09:24 2013 Carlos Linares Lopez>
# Last update <jueves, 12 diciembre 2013 14:38:25 Carlos Linares Lopez (clinares)>
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

        myBot = autobot.BotTestCase ()

        # parsing
        self._parser = myBot._parser
        self._parser.parse_args ()

        # logging
        myBot.create_logger (level='DEBUG')
        logger = logging.getLogger('testcase::setUp')
        myBot.debug (logger, "Esto es un mensaje de depuracion")
        myBot.info (logger, "Esto es un mensaje de informacion")
        myBot.warning (logger, "Esto es un mensaje de aviso")
        myBot.error (logger, "Esto es un mensaje de error")
        myBot.critical (logger, "Esto es un mensaje de error critico")


    def test_domains (self):

        print "\t testing domains ... "
        autobot.BotTestCase ().go ()


    def test_planners (self):

        print "\t testing planners ..."


    def tearDown (self):

        print "\t tearing down in test case #1"

        for i in range(0,10):
            print i, ' ',


class TestCaseTwo (autobot.BotTestCase):
    """
    Definition of an automated test case
    """

    def test_suite (self):

        print "\t Executing test suite ..."
        autobot.BotTestCase ().go ()

    def tearDown (self):

        print "\t tearing down in the second test case"


if __name__ == '__main__':

    autobot.BotMain (module='testcase')


# Local Variables:
# mode:python
# fill-column:80
# End:
