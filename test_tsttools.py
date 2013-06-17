#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# test_tsttools.py
# Description: unittest of tsttools
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 14 17:03:21 2013 Carlos Linares Lopez>
# Last update <Monday, 17 June 2013 22:53:31 Carlos Linares Lopez (clinares)>
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
.. module:: test_tsttools
   :platform: Linux
   :synopsis: unittest of tsttools

.. moduleautor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import random                   # shuffling lists
import tsttools                 # unit to test
import unittest                 # unit test facilities

import testutils                # parametrized unit tests

# globals
# -----------------------------------------------------------------------------
NBCASES = 5                   # number of command lines to try
MAXID   = 10000                 # maximum test id

# -----------------------------------------------------------------------------
# TestTstCase
#
# tests that TstCase is usable in precisely the same way it is intended. _param
# should consist of a tuple whose first item is the length of the command line
# and the second divided by the third item is the probability that a particular
# index gets into the cmd line
# -----------------------------------------------------------------------------
class TestTstCase(testutils.ParametrizedTestCase):

    """
    tests that TstCase is usable in precisely the same way it is
    intended. _param should consist of a tuple whose first item is the length of
    the command line and the second divided by the third item is the probability
    that a particular index gets into the cmd line
    """

    def setUp (self):
        """
        define a particular test case
        """

        # initialization
        self._values = dict ()

        print self._param

        # parameters
        self._length = self._param [0]
        self._p      = self._param [1]
        self._whole  = self._param [2]

        # compute the args and its values and store them in a dictionary for
        # future reference
        for iindex in range (0,1+self._length):

            # throw a coin to decide with prob = self._p/self._whole wether this
            # index is included
            if (random.randrange (0,self._whole) < self._p):

                self._values ["index%i" % iindex] = \
                    ["val%i" % jdef for jdef in range (1, 1+iindex)]

        # compute also the canonical representation of a test case as a tuple:
        # (case id, case args) both for future reference
        self._def = ("%04i" % random.randrange (0, MAXID), 
                     reduce (lambda x,y:x+y,
                             [['--%s' % index] + value 
                              for index, value in self._values.iteritems ()]))

        print self._def

        # compute the synthetic representation of this test case
        self._tstcase = tsttools.TstCase (self._def[0], self._def[1])


    def test_id (self):
        """
        verifies that the ids are correctly computed
        """

        # check the returned ids are indeed the first value in every
        # tuple
        self.assertEqual (self._tstcase.get_id (),
                          self._def[0],
                          "The ids were not properly computed")


    def test_args (self):
        """
        verifies that the args are correctly computed
        """

        # check the returned args are indeed the second item in every
        # tuple
        self.assertEqual (self._tstcase.get_args (),
                          self._def[1],
                          "The args were not properly computed")


    def test_value (self):
        """
        verifies that the values of every argument are properly
        computed
        """

        # and the directives present in
        # WARNING - the following service is not tested!
        for idirective in self._tstcase.get_directives ():
            
            # compose a list with all the values of this directive as
            # computed by get_values and compare them with the values stored
            # in this test case
            self.assertEqual ([ivalue for ivalue in self._tstcase.get_value (idirective)],
                              self._values [idirective],
                              "Values were not properly computed")


    def test_values (self):
        """
        verifies that the values of every directive are properly
        computed
        """

        # compute a dictionary with the values of all args as they
        # should be returned by get_values
        values = dict ([(index, ' '.join (value)) 
                        for index, value in self._values.iteritems ()])

        # and now, run the test verifying that the values returned are
        # exactly the expected ones
        self.assertDictContainsSubset (self._tstcase.get_values (),
                                       values,
                                       "The values were not properly computed")

    def tearDown (self): pass



# Main body
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # declare a test suite
    suite = unittest.TestSuite()

    # and now, run a number of test cases just incrementing the length of the
    # command line in each case
    for length in range (0, NBCASES):
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, length))

    # and execute the suite
    unittest.TextTestRunner(verbosity=1).run(suite)


# Local Variables:
# mode:python
# fill-column:80
# End:
