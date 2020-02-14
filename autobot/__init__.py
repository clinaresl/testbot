#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# __init__.py
# Description: Init file for the automated testing facility
# -----------------------------------------------------------------------------
#
# Started on  <Sat May 25 19:22:08 2013 Carlos Linares Lopez>
# Last update <viernes, 11 marzo 2016 00:00:29 Carlos Linares Lopez (clinares)>
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
.. module:: testbot
   :platform: Linux
   :synopsis: Init file for the automated testing facility

.. moduleauthor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

__version__  = '2.0'
__revision__ = '$Revision$'

__all__ = ["bots",
           "botparser",
           "bottester",
           "colors",
           "dbexpression",
           "dbparser",
           "dbtools",
           "logutils",
           "namespace",
           "parsetools",
           "sqltools",
           "systools",
           "tbparser",
           "timetools",
           "tsttools"]


from bottester import BotTester
from botparser import BotParser
from bots import BotAction
from bots import BotMain
from . import parsetools



# Local Variables:
# mode:python
# fill-column:79
# End:
