#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# test_tsttools.py
# Description: unittest of tsttools
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 14 17:03:21 2013 Carlos Linares Lopez>
# Last update <Monday, 17 June 2013 00:41:27 Carlos Linares Lopez (clinares)>
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

# -----------------------------------------------------------------------------
# TestTstCase
#
# tests that TstCase is usable in precisely the same way it is
# intended
# -----------------------------------------------------------------------------
class TestTstCase(unittest.TestCase):

    """
    tests that TstCase is usable in precisely the same way it is
    intended
    """

    def setUp (self):
        """
        define a collection of definitions of test cases
        """

        # constants
        nbargs = 5                  # #args to simulate

        # initialization
        args = list ()
        self._defs = list ()
        self._values = dict ()

        # compute the args and its values and store them in a
        # dictionary
        for idef in range (0,nbargs):
            self._values ["index%i" % idef] = ["val%i" % jdef for jdef in range (1, 1+idef)]

        # define the collection of arbitrary data with the args and
        # its values in random order
        items = self._values.items ()
        random.shuffle (items)
        for (iindex, ivalue) in items:

            self._defs += [("%04i" % random.randrange (0, nbargs), 
                            args + ['--' + iindex] + ivalue)]
            args += ['--' + iindex] + ivalue
        
        # and make the test a little bit more robust just by shuffling
        # data
        random.shuffle (self._defs)

        # compute the synthetic representation of these tests cases
        self._tstcases = map (lambda x:tsttools.TstCase (x[0], x[1]), self._defs)


    def test_id (self):
        """
        verifies that the ids are correctly computed
        """

        # check the returned ids are indeed the first value in every
        # tuple
        self.assertEqual (map (lambda x:x.get_id (), self._tstcases),
                          map (lambda x:x[0], self._defs),
                          "The ids were not properly computed")


    def test_args (self):
        """
        verifies that the args are correctly computed
        """

        # check the returned args are indeed the second item in every
        # tuple
        self.assertEqual (map (lambda x:x.get_args (), self._tstcases),
                          map (lambda x:x[1], self._defs),
                          "The args were not properly computed")


    def test_value (self):
        """
        verifies that the values of every argument are properly
        computed
        """

        # for all test cases
        for itstcase in self._tstcases:

            # and the directives present in
            # WARNING - the following service is not tested!
            for idirective in itstcase.get_directives ():

                # compose a list with all the values of this directive as
                # computed by get_values and compare them with the values stored
                # in this test case
                self.assertEqual ([ivalue for ivalue in itstcase.get_value (idirective)],
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
        for itstcase in self._tstcases:

            self.assertDictContainsSubset (itstcase.get_values (),
                                           values,
                                           "The values were not properly computed")

    def tearDown (self): pass



# Main body
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    unittest.main (module='test_tsttools',
                   verbosity=2,
                   failfast=True)
    


# Local Variables:
# mode:python
# fill-column:80
# End:
