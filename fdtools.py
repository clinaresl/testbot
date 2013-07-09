#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# fdtools.py
# Description: filesystem management
# -----------------------------------------------------------------------------
#
# Started on  <Wed Jul  3 17:46:48 2013 Carlos Linares Lopez>
# Last update <Friday, 05 July 2013 17:51:28 Carlos Linares Lopez (clinares)>
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
.. module:: fdtools
   :platform: Linux
   :synopsis: filesystem management

.. moduleauthor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

__version__  = '1.0'
__revision__ = '$Revision$'


# imports
# -----------------------------------------------------------------------------
import os               # process handling
import re               # regular expressions
import time             # time management


# globals
# -----------------------------------------------------------------------------
UIDREGEXP   = "st_uid=(?P<uid>\d+)"
GIDREGEXP   = "st_gid=(?P<gid>\d+)"
SIZEREGEXP  = "st_size=(?P<size>\d+)"
ATIMEREGEXP = "st_atime=(?P<atime>\d+)"
MTIMEREGEXP = "st_mtime=(?P<mtime>\d+)"
CTIMEREGEXP = "st_ctime=(?P<ctime>\d+)"


def extract (group, pattern, text):
    """
    retrieves the value of the given group that matches the given pattern in
    text or None if pattern never matches
    """

    m = re.search (pattern, text)
    if (m):
        return m.group (group)

    return None
    

# -----------------------------------------------------------------------------
# FileInfo
#
# Accesses the /proc filesystem to retrieve various stats of a
# particular file identified by its path
# -----------------------------------------------------------------------------
class FileInfo(object):
    """
    Accesses the /proc filesystem to retrieve various stats of a
    particular file identified by its path
    """

    def __init__(self, path):
        """
        stat (following symlinks) the specified path

        :param path: path to stat
        :type pid: str
        """

        # initialization
        self._path = path                               # original path

        # access the stat info
        stat = self.stat ()

        # update the correct name of this path following the symlink if any exists
        self._path = {False: path,
                      True : os.readlink (path)}[os.path.islink (path)]

        # and now process all fields of interest
        self._uid   = extract ('uid',   UIDREGEXP,   stat)
        self._gid   = extract ('gid',   GIDREGEXP,   stat)
        self._atime = [extract ('atime', ATIMEREGEXP, stat)]
        self._mtime = [extract ('mtime', MTIMEREGEXP, stat)]
        self._ctime = [extract ('ctime', CTIMEREGEXP, stat)]

        # including time ---note that the current time is used
        self._size  = [(time.time (), extract ('size',  SIZEREGEXP,  stat))]


    def __eq__ (self, other):
        """
        returns true if this fileinfo and other refer to the same file
        """

        return (self._path == other.get_path ())


    def __ne__ (self, other):
        """
        returns false if this fileinfo and other refer to the same file
        ---defined only for consistency with __eq__
        """

        return (self._path != other.get_path ())


    def get_path (self):
        """
        returns the path of this instance
        """

        return self._path
        

    def get_uid (self):
        """
        returns the uid of this instance
        """

        return self._uid
        

    def get_gid (self):
        """
        returns the gid of this instance
        """

        return self._gid
        

    def get_size (self):
        """
        returns the size of this instance
        """

        return self._size
        

    def get_time (self, attr):
        """
        returns the time attr specified of this instance. Legal choices are
        ['atime', 'mtime', 'ctime']
        """

        if (attr == 'atime'):
            return self._atime
        elif (attr == 'mtime'):
            return self._mtime
        elif (attr == 'ctime'):
            return self._ctime
        else:
            raise ValueError
        

    def stat (self):
        """
        returns the result of stat on this file instance
        """

        stat = str ()                                   # initialization
        try:
            stat = str (os.stat (self._path))           # stat the path

        except:
            pass

        return stat


    def update (self):
        """
        adds new information if any is available
        """

        def _insert_ (field, regexp, txt, attr):
            """
            adds the value of the given field to the specified attr (which is
            retrieved parsing txt with regexp) if it did not exist
            """

            value = extract (field, regexp, txt)
            if (value not in attr):
                attr.append (value)
            return attr

        # access the stat info
        stat = self.stat ()

        # and now update the various fields of this instance
        self._atime = _insert_ ('atime', ATIMEREGEXP, stat, self._atime)
        self._mtime = _insert_ ('mtime', MTIMEREGEXP, stat, self._mtime)
        self._ctime = _insert_ ('ctime', CTIMEREGEXP, stat, self._ctime)

        # also, update the information on size in case it changed ---note that
        # current time is used
        size = extract ('size', SIZEREGEXP, stat)
        if size not in [isize for itime, isize in self._size]:
            self._size.append ((time.time (), size))


# Local Variables:
# mode:python
# fill-column:80
# End:
