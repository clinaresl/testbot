testbot Version 2.0


# Introduction #

Testbot is a Ptyhon package that has been designed and implemented to
assist in various tasks related to scientific experimentation. It
consists of a package that provides various services both for parsing
text files (which should typically record the output of an executable)
and running (hopefully) any executable under any OS that supports the
`/proc` filesystem (e.g., Linux). Additionally, Testbot is capable of
storing various data in a sqlite3 database.

The following paragraphs provide basic information that introduces the
main concepts. For a full description refer to the manual.

It consists of three main components:

1. Package `autobot`: it provides the main services for programmers to
automate/monitor the execution of their programs and to parse text
files.

2. Script `parsebot.py`: it uses the services provided by `autobot` to
parse and manipulate data extracted from any text file.

3. Script `testbot.py`: it uses the services provided by `autobot` to be
run under simple scenarios.

Both scripts parse the contents of a db file that defines the schema
of all tables to be stored by `autobot`. These are defined with a
(very simple) language, and can contain a bunch of data including data
retrieved from the standard output/error generated by an executable or
regular expressions parsed in a text file. In particular, the db
language recognizes the following variables:

* *Sys variables*: these variables are computed at every cycle (i.e.,
  immediately after the underlying process is pinged). They are
  preceded by the character `:` or the prefix `sys.`

* *Main variables*: the value of any directive passed to any script
  (either `testbot.py` or `parsebot.py`). They are preceded by the
  character `_` or the prefix `main.`

* *Data variables*: strings (either single or doubled quoted just in
  case they contain blank characters) that are matched in the standard
  output/error of the process given to `testbot.py` or the file given
  to `parsebot.py`. In case they are found, the value appearing
  immediately after is used as its value. They are preceded by the
  character `?` or the prefix `data.`

* *File variables*: strings (either single or doubled quoted just in
  case they contain blank characters) that identify files whose
  contents are copied as their value. They are preceded by the
  character `<` or the prefix `file.`

* *Directive variables*: the value of any directive passed to the
  executable (which are specified in the test specification file)
  identified by the directive name. They are used only by
  `testbot`. They are preceded by the character `@` or the prefix
  `dir.`

* *Parameters*: the value of any directive passed to the executable
  (which are specified in the test specification file) identified by
  their location. They are used only by `testbot`. They are preceded
  by the character `$` or the prefix `param.`

* *User variables*: strings (either single or doubled quoted just in
  case they contain blank characters) that contain information
  specific to third-party software. They are preceded by the character
  `~` or the prefix `user.`

* *Regular expressions*: regexps are defined separately in the
  database specification file and can be used in the specification of
  database tables to refer to the value of any group defined in the
  regexp. Importantly, regexps can be compound to create *contexts*
  where the output of one regular expression is given to the next
  one. The head of a context can be any variable (or a snippet defined
  below), but a regexp.

* *Snippets*: (Python) snippets are also defined separately in the
  database specification file and can be used in the specification of
  database tables to refer to the different output variables that are
  computed by the (Python) snippet.

While `parsebot.py` accepts an arbitrary selection of text files,
`testbot.py` accepts an arbitrary selection of executables specified
with regular expressions. The information retrieved from either script
is then available in sqlite3 databases that can be used later to
access data or to plot figures directly (e.g., using pipelines in
gnuplot).

Depending upon the information stored in every table, they can be of
different types:

* *Sys tables*: they store *only* sys variables. Sys tables are
  populated with information extracted in every cycle of the
  execution. They have to be preceded by the prefix `sys_`

* *Data tables*: they hold any type of variable (and also sys
  variables). They are populated with information extracted after the
  execution of a particular solver or the parsing of a specific
  file. Thus, if sys variables are included then the last value they
  take is inserted into the database. They have to be preceded by the
  prefix `data_`

* *User tables*: they are never used by `autobot`. They are just
  defined for giving third-party software the possibility to store
  private information. They have to be preceded by the prefix `user_`

Additionally, `testbot.py` creates also *Admin tables* with
administrative information of the whole process. They are
distinguished with the prefix `admin_`.


# Installation #

Download the software cloning the git repository with the following command:

    $ git clone https://github.com/clinaresl/testbot.git

a directory called `testbot` will be automatically created. Go to that
directory and execute the script `setup.py` as indicated below:

    $ cd testbot
    $ sudo python2 ./setup.py install

In case this software is being reinstalled, make sure to add `--force`
to overwrite the previous package.


# How to use #

The following subsections provide basic information to execute
`testbot.py` or `parsebot.py`. For more details refer to the manual.

## parsebot.py ##

The simplest usage of `autobot` is exemplified with the script
`parsebot.py`. It takes the following mandatory arguments:

* *file*: regular expressions that identify all files to parse

* *dbspec*: db specification file in the db language

Other optional parameters are:

* *dbname*: name of the sqlite3 database to be generated. Placeholders
   can be used. To see a comprehensive list of the available
   placeholders type: `$ parsebot.py --show-placeholders`

* *directory*: target directory where various additional data are
   recorded ---by default, the current working directory. Two
   directories are created under the specified directory: `config/`
   and `results/`. While the first contains configuration information
   used during the parsing process (such as the database specification
   file), the latter contains a copy of the files that have been
   processed.

* *output*: prefix used for naming the files stored in the `results/`
   directory. Placeholders can be used. To see a comprehensive list of
   the available placeholders type: `$ parsebot.py
   --show-placeholders`

* *bz2*: if given, the text files copied into the given directory are
   compressed using `bzip2`.

It also provides additional services for configuring the logging
services or to test whether the db file is correctly parsed. In
particular, to see the results of parsing the database specification
file type:

    $ parsebot.py --parse-db

All of this information can be accessed with:

    $ parsebot.py --help

Configuration files are provided under `examples/`. For instance, try:

```
#!bash

    $ parsebot.py --file examples/population/case-0/population.data
                  --dbspec examples/population/case-0/population.dbspec 
                  --dbname population.db
```

and examine the contents of the sqlite3 database `population.db`. This
example uses regular expressions (discussed above) to extract various
data from a text file. Another more involved example is given as a
separate case:

```
#!bash
    $ cp examples/population/case-1/regions.py .
    $ parsebot.py --file examples/population/case-1/population.data
                  --dbspec examples/population/case-1/population.dbspec
                  --dbname population.db
```

and examine the contents of the sqlite3 database `population.db`. This
example shows how to retrieve data from a text file, to give it to a
Python module (regions.py which should then be copied to the current
working directory) and to store the resulting data in a database.


## testbot.py ##

It takes the following mandatory arguments:

* *solver*: regular expression that identifies all executables to
  monitor

* *test*: test specification file in the tb language. It contains the
  description of the command line arguments to be passed to the
  executable. Every command line consists of a single execution of the
  executable. tb files are encoded in a specific (very simple)
  language which adheres to the recommendations made by the GNU coding
  standards for command-line interfaces, though others are also
  recognized. In addition, it supports the stdin redirection operator
  `<`.

* *db*: db specification file in the db language. For a gentle
   introduction to the contents of the db language see the
   Introduction.

* *timeout*: maximum allotted time in seconds

* *memory*: maximum allotted memory in gigabytes

Other optional parameters that affect the behaviour of testbot are:

* *check*: seconds elapsed between successive pings to the running
  executable. `autobot` will gather the values of all sys variables at
  every ping.

* *output*: prefix used in the name of the files that record the
  standard output and standard error of every execution. Placeholders
  can be used. To see a comprehensive list of the available
  placeholders type: `$ testbot.py --show-placeholders`

* *directory*: target directory where all information is
  recorded. `autobot` automatically creates a subdirectory per
  executable and stores: config information, system information and
  the standard output and standard error generated

* *bz2*: in case the standard output/error might be huge, it is
  feasible to compress it with `bzip2`.

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

Configuration files are provided under `examples/`. For instance, try:

```
#!bash

    $ testbot.py --solver /usr/bin/find --test examples/find/find.tb 
                 --db examples/find/find.db --timeout 5 --memory 2 --check 0
```

and examine the contents of the directory `find/` just created. In
particular, examine the data generated in the sqlite3 database
`find.db`.


# Requirements #

`autobot` requires [PLY 3.4](http://www.dabeaz.com/ply/) or
greater. It is currently designed for Python 2.7.

Additionally, `testbot.py` only executes in GNU/Linux OSs.


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
