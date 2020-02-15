#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# timetools.py
# Description: time management
# -----------------------------------------------------------------------------
#
# Started on  <Tue Mar  8 11:54:22 2011 Carlos Linares Lopez>
# -----------------------------------------------------------------------------
# Made by Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
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
.. module:: timetools
   :platform: Linux
   :synopsis: time management

.. moduleauthor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

from __future__ import with_statement


# imports
# -----------------------------------------------------------------------------
import time                     # time management


# -----------------------------------------------------------------------------
# Timer
#
# this class creates a block to be used within a with statement. It
# exactly measures the time between the entry and exit points of the
# with block
# -----------------------------------------------------------------------------
class Timer(object):

    """
    this class creates a block to be used within a with statement. It exactly
    measures the time between the entry and exit points of the with block
    """

    def __enter__(self):
        """
        Sets the entry point to the block. It just annotates the current time in
        a private attribute
        """

        self.__start = time.time()

    def __exit__(self, type, value, traceback):
        """
        Sets the exit point to the block. It just annotates the current time in
        a private attribute
        """

        self.__finish = time.time()

    def elapsed (self):
        """
        Return the elapsed time since the block was started until it ended
        """

        return self.__finish - self.__start


# Local Variables:
# mode:python
# fill-column:79
# End:
