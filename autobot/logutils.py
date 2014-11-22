#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# logutils.py
# Description: Different logging utilities used to configure the behaviour of
#              loggers in the scripts
# -----------------------------------------------------------------------------
#
# Started on  <Fri Sep 19 16:34:26 2014 Carlos Linares Lopez>
# Last update <jueves, 20 noviembre 2014 14:05:31 Carlos Linares Lopez (clinares)>
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
Different logging utilities used to configure the behaviour of loggers in the
scripts
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'

# imports
# -----------------------------------------------------------------------------
import datetime                         # date and time services
import getpass                          # getuser
import logging                          # loggers
import os                               # path mgmt
import socket                           # gethostname

import colors

# -----------------------------------------------------------------------------
# configure_logger
#
# opens a file in write mode in the specified directory in case a logfile is
# given. If not, it creates a basic logger. Messages above the given level are
# issued.
# -----------------------------------------------------------------------------
def configure_logger (directory, logfile, level):

    """
    opens a file in write mode in the specified directory in case a logfile is
    given. If not, it creates a basic logger. Messages above the given level are
    issued
    """

    # create the log file either as a file stream or a stream handler
    if (logfile):

        # if a filename is specified, append the current date and time
        logfilename = logfile + '.' + datetime.datetime.now ().strftime ("%y-%m-%d.%H:%M:%S")
        logging.basicConfig (filename=os.path.abspath (os.path.join (directory, logfilename)),
                             filemode = 'w', level=level,
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s\n")

    else:
        logfilename = ''
        logging.basicConfig (level=level,
                             format="%(color)s[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s\n")


# -----------------------------------------------------------------------------
# ContextFilter
#
# creates contextual information to be used in all the log messages issued in
# this module
# -----------------------------------------------------------------------------
class ContextFilter(logging.Filter):
    """
    defines contextual information to be passed to other modules
    """

    def filter(self, record):
        """
        Defines the additional information (color, node and user) that is set up
        in the logger configuration
        """

        record.node = socket.gethostname ()
        record.user = getpass.getuser ()

        if record.levelname == 'DEBUG':
            record.color = colors.darkwhite
        elif record.levelname == 'INFO':
            record.color = colors.bluesea
        elif record.levelname == 'WARNING':
            record.color = colors.yellow
        elif record.levelname == 'ERROR':
            record.color = colors.red
        elif record.levelname == 'CRITICAL':
            record.color = colors.red
        else:
            record.color = colors.white

        return True


# Local Variables:
# mode:python
# fill-column:79
# End:
