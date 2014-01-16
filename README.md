testbot Version 2.0


# Introduction #

Testbot is a Python package that monitors the execution of (hopefully)
any executable under OSs that provide a /proc filesystem ---i.e.,
Linux. Testbot is mainly intended to be used for scientific
experimentation.

It consists of two components:

1. Package autobot: it provides the main services for programmers to
automate/monitor the execution of their programs.

2. Script testbot: it uses the services provided by autobot to be run
under simple scenarios.

autobot parses two input files:

* tb file: it contains the description of the command line arguments
  to be passed to the executable. Every command line consists of a
  single execution of the executable

* db file: it defines the schema of all tables to be stored by autobot
  as a result of the experimentation. These tables can contain a bunch
  of data including data retrieved from the standard output generated
  by the executable or other particular data accessed by other Python
  modules. In particular, the db language recognizes the following
  variables:

	+ Sys variables: these variables are computed at every cycle
	(i.e., immediately after the underlying process is
	pinged). They are preceded by the character `:`

	+ Data variables: strings (either single or doubled quoted
	just in case they contain blank characters) that are matched
	in the standard output of the process. In case they are found
	the value appearing immediately after is used as its
	value. They are preceded by the character `?`

	+ Directive variables: the value of any directive passed to
	the executable (which are specified in the test specification
	file). They are preceded by the character `@`

	+ File variables: strings (either single or doubled quoted
	just in case they contain blank characters) that identify
	files whose contents are copied as their value. They are
	preceded by the character `<`

	+ Main variables: the value of any directive passed to the
	testbot script. They are preceded by the character `_`

Autobot accepts an arbitrary selection of *solvers* specified with
regular expressions. This is useful to compare algorithms. Every
executable generates a different sqlite3 database that can be used
later to access data or to plot figures directly (e.g., using
pipelines in gnuplot).


# Installation #

Download the software cloning the Mercurial repository with the
following command:

    $ hg clone ssh://hg@bitbucket.org/clinares/testbot

a directory called `testbot` will be automatically created. Go to that
directory and execute the script `setup.py` as indicated below:

    $ cd testbot
    $ sudo ./setup.py install

In case this software is being reinstalled, make sure to add `--force`
to overwrite the previous package.


# How to use #

The simplest usage of autobot is exemplified with the script
testbot. It takes the following mandatory arguments:

* solver: regular expression that identifies all executables to
  monitor

* test: test specification file in the tb language

* db: db specification file in the db language

* timeout: maximum allotted time in seconds

* memory: maximum allotted memory in gigabytes

Other optional parameters that affect the behaviour of testbot are:

* check: seconds elapsed between successive pings to the running
  executable. Autobot will gather some statistics at every ping (sys
  variables)

* output: prefix used in the name of the files that record the
  standard output and standard error of every execution. Placeholders
  can be used. To see a comprehensive list of the available
  placeholders type:

    $ testbot.py --show-placeholders

* directory: target directory where all information is
  recorded. autobot automatically creates a subdirectory per
  executable and stores: config information, system information and
  the standard output and standard error generated

* bz2: in case the standard output/error might be huge, it is feasible
  to compress it with bzip2.

It also provides additional services for configuring the logging
services or to test whether the db/tb files are correctly parsed. In
particular, to see the results of parsing the test specification file
type:

    $ testbot.py --parse-tests

Analagously, to see the results of parsing the database specification
file type the following:

    $ testbot.py --parse-db

All of this information can be accessed with:

    $ testbot.py --help

Configuration files are provided under examples/ For instance, try:

    $ testbot.py --solver examples/solvers/eperimeter 
    --test examples/tests/8puzzle.tb 
    --db examples/db/example.db 
    --timeout 5 --memory 2 --check 0 --bz2

and examine the contents of the directory eperimeter/ just created

Further information is offered at the User's Manual and the
Programmer's Guide of testbot


# Requirements #

autobot requires [PLY 3.4](http://www.dabeaz.com/ply/) or greater. It
is currently designed for Python 2.7.


# License #

testbot is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

testbot is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with testbot.  If not, see <http://www.gnu.org/licenses/>.


# Author #

Carlos Linares Lopez <carlos.linares@uc3m.es>