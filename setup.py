#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# setup.py
# Description: distribution script
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 21:27:32 2013 Carlos Linares Lopez>
# Last update <domingo, 05 enero 2014 01:27:28 Carlos Linares Lopez (clinares)>
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
distribution script
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '2.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import os
from distutils.core import setup

# -----------------------------------------------------------------------------
# read
#
# Utility function to read the README file.
#
# Used for the long_description.  It's nice, because now 1) we have a
# top level README file and 2) it's easier to type in the README file
# than to put a raw string in below ...
#
# [Taken from http://pythonhosted.org/an_example_pypi_project/setuptools.html]
# -----------------------------------------------------------------------------
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# setup
# -----------------------------------------------------------------------------
setup(name='testbot',
      version='2.0',
      author='Carlos Linares Lopez',
      author_email='carlos.linares@uc3m.es',
      maintainer='Carlos Linares Lopez',
      maintainer_email='carlos.linares@uc3m.es',
      license='GPLv3+',
      platforms=['Linux'],
      url='http://www.plg.inf.uc3m.es/~clinares/investigacion.php',
      description='automates the tests of (hopefully) any executable under Linux OSs',
      long_description=read ('README'),
      packages = ['autobot'],
      scripts = ['scripts/testbot.py'],
      requires = ['ply (>=3.4)'],
      provides = ['autobot', 'testbot'],
      classifiers = [
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Topic :: Scientific/Engineering',
          'Topic :: System :: Monitoring'],
      data_files=[('db', ['examples/db/example.db']),
                  ('tests', ['examples/tests/8puzzle.tb']),
                  ('solvers', ['examples/solvers/eperimeter'])]
     )



# Local Variables:
# mode:python
# fill-column:80
# End:
