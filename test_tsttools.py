#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# test_tsttools.py
# Description: unittest of tsttools
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 14 17:03:21 2013 Carlos Linares Lopez>
# Last update <Friday, 21 June 2013 15:55:48 Carlos Linares Lopez (clinares)>
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
import string                   # direct access to string sets
import tsttools                 # unit to test
import unittest                 # unit test facilities

import testutils                # parametrized unit tests

# globals
# -----------------------------------------------------------------------------
NBCASES = 50                    # number of command lines to try
MAXID   = 10000                 # maximum test id

# -----------------------------------------------------------------------------
# TestTstCase
#
# tests that TstCase is usable in precisely the same way it is intended. _param
# should consist of a tuple whose first item is the length of the command line;
# the second is the probability (expressed as a percentage) of a particular
# index to be included in the command line; and the third and fourth are the mu
# and sigma used to produce a fake value according to a gauss distribution (mu,
# sigma)
# -----------------------------------------------------------------------------
class TestTstCase(testutils.ParametrizedTestCase):

    """
    tests that TstCase is usable in precisely the same way it is
    intended. _param should consist of a tuple whose first item is the length of
    the command line; the second is the probability (expressed as a percentage)
    of a particular index to be included in the command line; and the third and
    fourth are the mu and sigma used to produce a fake value according to a
    gauss distribution (mu, sigma)
    """

    def setUp (self):
        """
        define a particular test case
        """

        def _quote (S):
            """
            in case S contains the blank space quote the whole string with
            either single or double quotes
            """

            if (' ' in S):
                if (not int (random.uniform (0,1))):
                    return '"' + S + '"'
                else:
                    return "'" + S + "'"
            return S


        # parameters
        self._length = self._param [0]          # number of indexes to consider
        self._p      = self._param [1]          # probability to include an index
        self._mu     = self._param [2]          # mu
        self._sigma  = self._param [3]          # sigma

        # initialization
        self._values = dict ()

        # next, the index of this test case is randomly generated and the args
        # are None unless some are randomly picked up
        self._caseid = "%04i" % random.randrange (0, MAXID)
        self._caseargs = ['']

        # compute the args and its values and store them in a dictionary for
        # future reference
        for iindex in range (0,1+self._length):

            # throw a coin to decide with prob = self._p wether this index is
            # included and reorder its values randomly
            if (random.uniform (0,100) <= self._p):

                self._values ["index%i" % iindex] = \
                    [_quote (''.join (random.choice(string.ascii_uppercase + string.digits + ' ') 
                                      for x in range(int(random.gauss (self._mu, self._sigma)))))
                     for jdef in range (1, 1+iindex)]
                random.shuffle (self._values ["index%i" % iindex])

        # compute also the canonical representation of a test case as a tuple:
        # (case id, case args) both for future reference in case that any
        # indexes have been selected
        if (self._values):
            self._caseargs = reduce (lambda x,y:x+y,
                                     [['--%s' % index] + value 
                                      for index, value in self._values.iteritems ()])
            
        # compute the synthetic representation of this test case
        self._tstcase = tsttools.TstCase (self._caseid, self._caseargs)


    def test_id (self):
        """
        verifies that the ids are correctly computed
        """

        # check the returned ids are indeed the first value in every
        # tuple
        self.assertEqual (self._tstcase.get_id (),
                          self._caseid,
                          "The ids were not properly computed")


    def test_args (self):
        """
        verifies that the args are correctly computed
        """

        # check the returned args are indeed the second item in every
        # tuple
        
        self.assertEqual (self._tstcase.get_args (),
                          self._caseargs,
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

        def _sep (x):
            """
            returns a blank to separate x with an incoming item if it is not
            null and '' otherwise
            """

            return ' ' if x else ''

        # compute a dictionary with the values of all args as they should be
        # returned by get_values ---take especial care of null args which are
        # just represented with the null string; otherwise, the args are
        # computed inserting the right separators even if one argument is null
        values = dict ([(index, '' if not value else reduce (lambda x,y: x + _sep (x) + y, value))
                        for index, value in self._values.iteritems ()])

        # and now, run the test verifying that the values returned are
        # exactly the expected ones
        self.assertDictContainsSubset (self._tstcase.get_values (),
                                       values,
                                       "The values were not properly computed")

    def tearDown (self): pass



# -----------------------------------------------------------------------------
# TestTstSpec
#
# tests that TstSpec is usable in precisely the same way it is intended. The
# first param is the number of specification lines; the second one is the number
# of data lines per specification line
# -----------------------------------------------------------------------------
class TestTstSpec(testutils.ParametrizedTestCase):

    """
    """

    def setUp (self):
        """
        define a particular test case specification
        """

        # parameters
        self._nbspecs = self._param [0]
        self._nbdata  = self._param [1]

        # initialization
        self._spec = str ()

        # create a random test specification
        for itstspec in range (0, self._nbspecs):

            self._spec += '@ '                  # prefix of specification lines
            

            for itstdata in range (0, self._nbdata):

                


    def test_id (self):
        """
        verifies that the ids are correctly computed
        """

        # check the returned ids are indeed the first value in every
        # tuple
        self.assertEqual (self._tstcase.get_id (),
                          self._caseid,
                          "The ids were not properly computed")


    def tearDown (self): pass



# Main body
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # declare a test suite
    suite = unittest.TestSuite()

    # start by adding a single test case with up to 50 different arguments, half
    # of which should be inserted in the cmd line but most likely with no values
    # at all (according to a gauss distribution (0,1))
    suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                             50, 50, 0, 1))

    # and now, run a number of test cases just incrementing the length of the
    # command line in each case and the probability of including new indexes (so
    # that making the command lines larger) - this test automatically includes
    # (with a non-zero probability) null command lines
    for length in range (0, NBCASES):
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                                 length, 10, 10, 1))
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                                 length, 30, 10, 1))
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                                 length, 50, 10, 1))
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                                 length, 70, 10, 1))
        suite.addTest(testutils.ParametrizedTestCase.parametrize(TestTstCase, 
                                                                 length, 90, 10, 1))

    # and execute the suite
    unittest.TextTestRunner(verbosity=1).run(suite)


# Local Variables:
# mode:python
# fill-column:80
# End:
