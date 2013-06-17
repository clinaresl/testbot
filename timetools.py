#!/usr/bin/python2.7
#
# timetools.py
# Description: time management
# -----------------------------------------------------------------------------
#
# Started on  <Tue Mar  8 11:54:22 2011 Carlos Linares Lopez>
# Last update <Friday, 14 June 2013 17:01:20 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: timetools.py 306 2011-11-11 22:25:37Z clinares                       $
# $Date:: 2011-11-11 23:25:37 +0100 (Fri, 11 Nov 2011)                       $
# $Revision:: 306                                                            $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@korf.plg.inf.uc3m.es>
#

"""
.. module:: timetools
   :platform: Linux
   :synopsis: time management

.. moduleauthor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

from __future__ import with_statement

__version__  = '1.2'
__revision__ = '$Revision: 306 $'

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
# fill-column:80
# End:
