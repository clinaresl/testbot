#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# test_timetools.py
# Description: unittest of timetools
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 14 15:50:25 2013 Carlos Linares Lopez>
# Last update <viernes, 03 enero 2014 19:58:22 Carlos Linares Lopez (clinares)>
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
.. module:: test_timetools
   :platform: Linux
   :synopsis: unittest of timetools

.. moduleautor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

from __future__ import with_statement

__version__  = '1.0'
__revision__ = '$Revision$'

# imports
# -----------------------------------------------------------------------------
import time                     # time management
import timetools                # timers ---unit to test
import unittest                 # unit test facilities

# -----------------------------------------------------------------------------
# TestTimeTools
#
# test that timetools are usable in precisely the same way they are
# intended and that they return non negative values
# -----------------------------------------------------------------------------
class TestTimeTools(unittest.TestCase):

    """
    test that timetools are usable in precisely the same way they are
    intended and that they return non negative values
    """

    def setUp (self):
        """
        set up the test environment just by creating a time counter
        """

        self._timer = timetools.Timer ()


    def test_timer (self):
        """
        executes the timer within a block of time which just sleeps
        for a second to awake
        """

        waitfor = 1                     # elapsed time

        with self._timer:

            time.sleep (waitfor)

        self.assertNotEqual (self._timer.elapsed (), 
                             waitfor, 
                             "Time elapsed is not a second!")


    def tearDown (self): pass


# Main body
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    unittest.main (module='test_timetools',
                   verbosity=2,
                   failfast=True)



# Local Variables:
# mode:python
# fill-column:80
# End:
