#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# testutils.py
# Description: unit test utils
# -----------------------------------------------------------------------------
#
# Started on  <Mon Jun 17 16:39:39 2013 Carlos Linares Lopez>
# Last update <Monday, 17 June 2013 22:55:55 Carlos Linares Lopez (clinares)>
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
unit test utils
"""

__version__  = '1.0'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import unittest

# -----------------------------------------------------------------------------
# ParametrizedTestCase
#
# enables subclasses of it to receive parameters when running unit
# tests
#
# Source: Eli Bendersky's website
# http://eli.thegreenplace.net/2011/08/02/python-unit-testing-parametrized-test-cases/
# -----------------------------------------------------------------------------
class ParametrizedTestCase(unittest.TestCase):
    """ 
    enables subclasses of it to receive parameters when running unit
    tests
    """
    def __init__(self, methodName='runTest', *param):
        super(ParametrizedTestCase, self).__init__(methodName)
        self._param = param

    @staticmethod
    def parametrize(testcase_klass, *param):
        """ 
        Create a suite containing all tests taken from the given
        subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, *param))
        return suite


# Local Variables:
# mode:python
# fill-column:80
# End:
