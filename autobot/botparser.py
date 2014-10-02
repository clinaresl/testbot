#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# botparser.py
# Description: Base class of all parsebots
# -----------------------------------------------------------------------------
#
# Started on  <Fri Sep 26 00:39:36 2014 Carlos Linares Lopez>
# Last update <miércoles, 01 octubre 2014 17:35:45 Carlos Linares Lopez (clinares)>
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

"""
Base class of all parsebots
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import bz2                      # bzip2 compression service
import datetime                 # date/time
import logging                  # loggers
import os                       # os services
import re                       # regular expressions
import shutil                   # shell utitilies such as copying files
import string                   # rstrip
import time                     # time management

import dbparser                 # database parser
import dbexpression             # evaluation of database exprsesions
import dbtools                  # database specification files
import namespace                # single and multi key attributes
import sqltools                 # sqlite3 database access


# -----------------------------------------------------------------------------
# BotParser
#
# Base class of all parsebots
#
# It automates the parsing of any text file and the automatic extraction of
# information according to the specification of a database specification file
# -----------------------------------------------------------------------------
class BotParser (object):
    """
    Base class of all parsebots

    It automates the parsing of any text file and the automatic extraction of
    information according to the specification of a database specification file
    """

    # regular epression for recognizing pairs (var, val)
    # -----------------------------------------------------------------------------
    # the following regexp is used by default: first, the user can provide its
    # own regexps (see below) or it can overwrite the current regexp which is
    # distinguished with the special name 'data'
    #
    # the following regexp correctly matches strings with two groups 'varname'
    # and 'value' such as:
    #
    # > Cost     : 359
    # > CPU time : 16.89311
    #
    # since these fields are written into the data namespace (see below) they
    # can be accessed by the user in the database specification file with the
    # format data.Cost and data.'CPU time'
    statregexp = r" >[\t ]*(?P<varname>[a-zA-Z ]+):[ ]+(?P<value>([0-9]+\.[0-9]+|[0-9]+))"

    # logging services
    # -----------------------------------------------------------------------------
    _loglevel = logging.INFO            # default logging level

    # namespaces - a common place to exchange data in the form of single and
    # multi key attributes. The following namespaces are mapped (in the
    # comments) with the type of variables recognized by the dbparser (see
    # dbparser.py)
    #
    # the purpose of every namespace is described below:
    #
    # * namespace: denoted also as the main namespace. It contains sys
    #              information and main variables
    # * data: It contains datavar and filevar
    # * user: this namespace is never used by autobot and it is created only for
    #         user specifics
    # * regexp : it stores the results of processing the contents of a file with
    #            the regexps found in the database specification
    #
    # These namespaces automatically use the different variables (most of them
    # defined in the dbparser) whose purpose is defined below:
    #
    # * sysvar: these are variables computed by autobot with additional info
    #           such as the index of the current file, current date and time and
    #           the name of the file been currently processed
    #
    # * mainvar: these are the flags given to the main script using autobot
    #            (ie., parsebot) These variables can be used to create a template
    #            for the 'output' file
    #
    # * datavar: data processed from the stdout of the executable. These data is
    #            retrieved using the default regular expression
    #
    # * filevar: these variables are given as filenames whose value are the
    #            contents of the file
    #
    # * regexp: regexps are defined separately in the database specification
    #           file and can be used in the specification of database tables to
    #           refer to the various groups that result every time a match is
    #           found
    #
    # to make these relationships more apparent, the variables given in the
    # database specification file can be preceded by a prefix that provide
    # information about the namespace they are written to:
    #
    # type of variable   prefix
    # -----------------+-----------
    # sysvar           | 'sys.'
    # datavar          | 'data.'
    # filevar          | 'file.'
    # mainvar          | "main.'
    # -----------------+-----------
    #
    # the case of regexp variables is a bit particular. They have their own
    # statements of the form:
    #
    # regexp <name> <specification-string>
    #
    # where <specification-string> should contain at least one <group> defined
    # with the directive (?P<group>...). This way, any column in the
    # specification of a database can use the format <name>.<group> to refer to
    # the value parsed in group <group> with regexp <name>
    #
    # Namespaces are populated with information with the following variable
    # types:
    #
    # namespace   variable type
    # ----------+-----------------
    # namespace | sysvar mainvar
    # data      | datavar filevar
    # user      | --
    # regexp    | regexp
    # ----------+-----------------
    #
    # These associations are implemented in the poll method of the dbparser
    # -----------------------------------------------------------------------------
    _namespace = namespace.Namespace ()         # sysvar, mainvar
    _data      = namespace.Namespace ()         # datavar, filevar
    _user      = namespace.Namespace ()         # user space
    _regexp    = namespace.Namespace ()         # regexp


    # -----------------------------------------------------------------------------
    # _sub
    #
    # substitute in string the ocurrence of every keyword in the namespace used
    # in this instance of BotParser (BotParser._namespace) with its value if it
    # appears preceded by '$' in string and it is a str. Similar to
    # Template.substitute but it also allows the substitution of strings which
    # do not follow the convention of python variable names
    #
    # Of course, other namespaces can be used but _sub is used only to compute
    # the name of the output file so that only static information is used
    # -----------------------------------------------------------------------------
    def _sub (self, string):
        """
        substitute in string the ocurrence of every keyword in the namespace
        used in this instance of BotParser (BotParser._namespace) with its value
        if it appears preceded by '$' in string and it is a str. Similar to
        Template.substitute but it also allows the substitution of strings which
        do not follow the convention of python variable names

        Of course, other namespaces can be used but _sub is used only to compute
        the name of the output file so that only static information is used
        """

        result = string                                 # initialization

        # now, substitute every ocurrence of every single attribute in
        # namespace with its value only in case the value is a string
        for ikey in [jkey for jkey in BotParser._namespace
                     if not isinstance (BotParser._namespace [jkey], dict)]:

            # perform the substitution enforcing the type of value to be str
            result = re.sub ('\$' + ikey, str (BotParser._namespace [ikey]), result)

        # and return the result now return result
        return result


    # -----------------------------------------------------------------------------
    # check_flags
    #
    # check the parameters given
    # -----------------------------------------------------------------------------
    def check_flags (self, txtfile, dbfile, directory):

        """
        check the parameters given
        """

        # verify that all text files are accessible
        for itxtfile in txtfile:

            if not os.access (itxtfile, os.F_OK):
                self._logger.critical ("""
 The text file '%s' is not accessible
 Use '--help' for more information
""" % itxtfile)
                raise ValueError (" The text file is not accessible")

        # verify also that the db file is accessible
        if not os.access (dbfile, os.F_OK):
            self._logger.critical ("""
 The database specification file does not exist or it resides in an unreachable location
 Use '--help' for more information
""")
            raise ValueError (" The database specification file is not accessible")


    # -----------------------------------------------------------------------------
    # show_switches
    #
    # show a somehow beautified view of the current params
    # -----------------------------------------------------------------------------
    def show_switches (self, txtfile, dbfile, directory):
        """
        show a somehow beautified view of the current params
        """

        self._logger.info ("""
  %s %s %s
 -----------------------------------------------------------------------------
  * Files                : %s
  * Database             : %s

  * Directory            : %s
 -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-2], __version__, txtfile, dbfile, directory))


    # -----------------------------------------------------------------------------
    # setup
    #
    # sets up all the necessary environment. It returns: the directory where the
    # parsed files should be copied and the config dir where additional
    # information (such as the db specification) should be written
    # -----------------------------------------------------------------------------
    def setup (self, directory):
        """
        sets up all the necessary environment. It returns: the directory where
        the parsed files should be copied and the config dir where additional
        information (such as the db specification) should be written
        """

        def _mksubdir (parent, subdir):
            """
            create the given subdirectory from the parent and returns it. Note that
            the absolute path is computed. Passing the absolute path prevents a
            number of errors
            """
            newdir = os.path.abspath (os.path.join (parent, subdir))
            os.mkdir (newdir)

            return newdir


        # the given directory should exist at this time, but not its
        # subdirectories. A couple of sanity checks follow:
        if (not os.access (directory, os.F_OK)):
            os.makedirs (directory)
            self._logger.debug (" The directory '%s' has been created!" % directory)

        # create another subdir to store the results. Note that the absolute path is
        # computed. Passing the absolute path to the results dir prevents a number
        # of errors
        resultsdir = _mksubdir (directory, "results")

        # create also an additional directory to store additional information
        # such as the database specification
        configdir = _mksubdir (directory, "config")

        # return the directories to be used in the experimentation
        return (resultsdir, configdir)


    # -----------------------------------------------------------------------------
    # parse_all_files
    #
    # starts the automated parsing of all text files given in txtfiles. All
    # these files are copied to the results directory given in resultsdir.
    #
    # if prologue/epilogue actions are specified then its __call__ method is
    # invoked before/after parsing every text file.
    # -----------------------------------------------------------------------------
    def parse_all_files (self, txtfiles, resultsdir):
        """
        starts the automated parsing of all text files given in txtfiles. All
        these files are copied to the results directory given in resultsdir.

        if prologue/epilogue actions are specified then its __call__ method is
        invoked before/after parsing every text file.
        """

        # before parsing all the text files, initialize the current file to the
        # empty string. This will enforce the creation of a first database that
        # will contain the results of the parsing
        currdbname = str ()

        # processing files
        # -------------------------------------------------------------------------
        # keep track of the file id as an integer
        idx = 0

        # now, process every text file
        for itxtfile in txtfiles:

            # namespaces
            # -------------------------------------------------------------------------
            # initialize the contents of the main namespace, data and regexp
            # namespace
            BotParser._namespace.clear ()
            BotParser._data.clear ()
            BotParser._regexp.clear ()

            # initialize the namespace with the parameters passed to the main
            # script (ie., the parsebot), mainvars. These are given in
            # self._argnamespace. Since the argparser automatically casts type
            # according to their type field, they are all converted into strings
            # here to allow a uniform treatment
            if self._argnamespace:
                for index, value in self._argnamespace.__dict__.items ():
                    BotParser._namespace [index] = str (value)

            # initialize the namespace with the value of some sysvar attributes:
            #
            #   index     - index of this file as an integer in the range [0, ...)
            #   name      - name of this text file
            #   date      - current date
            #   time      - current time
            #   starttime - time the whole parsing started
            #   currtime  - current time
            #
            # Note that other fields are added below to register the right
            # timings when every parsing started/ended
            BotParser._namespace.index = idx
            BotParser._namespace.name  = itxtfile
            BotParser._namespace.date  = datetime.datetime.now ().strftime ("%Y-%m-%d")
            BotParser._namespace.time  = datetime.datetime.now ().strftime ("%H:%M:%S")
            BotParser._namespace.starttime = self._starttime
            BotParser._namespace.currtime  = datetime.datetime.now ()

            self._logger.info (" Starting the automated parsing of file '%s'" % itxtfile)

            # parsing
            # -------------------------------------------------------------------------
            # execute the prologue in case any was given (note that the run time
            # is computed right now) and register also the exact time when the
            # processing of this file started (including the prologue)
            BotParser._namespace.startruntime = time.time ()
            if self._prologue:
                action = self._prologue (textfile=itxtfile,
                                         dbfile=self._dbfile,
                                         directory=self._directory,
                                         startruntime=BotParser._namespace.startruntime,
                                         namespace=BotParser._namespace,
                                         user=BotParser._user)
                action (self._logger)

            # now, invoke the automated parsing of this particular text file
            self.parse_single_file (itxtfile, resultsdir)

            # now, before processing the next text file, invoke the epilogue in
            # case any was given
            if self._epilogue:
                action = self._epilogue (textfile=itxtfile,
                                         dbfile=self._dbfile,
                                         directory=self._directory,
                                         startruntime = BotParser._namespace.startruntime,
                                         endruntime = time.time (),
                                         namespace=BotParser._namespace,
                                         data=BotParser._data,
                                         user=BotParser._user)
                action (self._logger)

            # and register the exact time when the whole parsing of this file
            # ended including processing the epilogue
            BotParser._namespace.endruntime = time.time ()

            # filevars
            # -------------------------------------------------------------------------
            # also, populate the data namespace with the contents of
            # files (filevars) as specified in the database
            # specification file
            for itable in [jtable for jtable in self._dbspec.get_db ()]:
                for icolumn in [jcolumn for jcolumn in itable if jcolumn.get_vartype () == 'FILEVAR']:
                    with open (icolumn.get_variable (), 'r') as stream:
                        BotParser._data [icolumn.get_variable ()] = stream.read ()

            # database
            # -------------------------------------------------------------------------
            # now, write data to the database. Note that we do this after
            # invoking the epilogue so that the user gets a finer control on the
            # data that is about to be inserted into the database

            # First. compute the name of the database
            dbname = self._sub (self._dbname)

            # create a new SQLITE3 database connection
            dbhandler = sqltools.dbaccess (dbname)

            # in case we get a different database
            if dbname != currdbname:

                # create the tables
                for itable in self._dbspec.get_db ():
                    dbhandler.create_table (itable)

                # and remember the name of the current database
                currdbname = dbname

            # now, populate the datatase
            self._logger.debug (" Inserting data into '%s'" % currdbname)
            for itable in self._dbspec.get_db ():
                self._logger.debug (" Populating '%s'" % itable.get_name ())
                dbhandler.insert_data (itable,
                                       itable.poll (namespace = BotParser._namespace,
                                                    data = BotParser._data,
                                                    user = BotParser._user,
                                                    param=None,
                                                    regexp = BotParser._regexp,
                                                    logger = self._logger))

            # and close the database
            dbhandler.close ()

            # update the index
            idx += 1


    # -----------------------------------------------------------------------------
    # parse_single_file
    #
    # looks for all matches of all regular expressions defined in the database
    # specification in the given text file. The results of all matches are
    # written to the regexp namespace. Also, the data namespace is populated
    # with the results of the matches of the default regexp
    #
    # Also, the textfile is backed up to the resultsdir
    # -----------------------------------------------------------------------------
    def parse_single_file (self, txtfile, resultsdir):
        """
        looks for all matches of all regular expressions defined in the database
        specification in the given text file. The results of all matches are
        written to the regexp namespace. Also, the data namespace is populated
        with the results of the matches of the default regexp

        Also, the textfile is backed up to the resultsdir
        """

        def _bz2 (filename, remove=False):
            """
            compress the contents of the given filename and writes the results to a
            file with the same name + '.bz2'. If remove is enabled, the original
            filename is removed
            """

            # open the original file in read mode
            with open(filename, 'r') as input:

                # create a bz2file to write compressed data
                with bz2.BZ2File(filename+'.bz2', 'w', compresslevel=9) as output:

                    # and just transfer data from one file to the other
                    shutil.copyfileobj(input, output)

            # if remove is enabled, remove the original filename
            if (remove):
                os.remove (filename)



        # processing regular expressions
        # ---------------------------------------------------------------------
        # process the default regular expression in this textfile

        # open the file in read mode
        with open (txtfile, "r") as stream:

            # default regexp
            # ---------------------------------------------------------------------
            # read all contents of the input file - yep, this might take a lot
            # of memory but the alternative, to process each line separately
            # would not allow to match various lines simultaneously
            contents = stream.read ()

            # for all matches of this regexp in the current text file
            for imatch in re.finditer (BotParser.statregexp, contents):

                # and store every match in the data namespace
                BotParser._data [imatch.group ('varname').rstrip (' ')] = \
                  imatch.group ('value')

            # data tables
            # ---------------------------------------------------------------------
            # eval all regular expressions appearing in any database table (so
            # that we are implicitly skipping those that are defined but never
            # used) that apply to the contents of this file ---again, we are
            # implicitly skipping those that apply to other *contexts*. In case
            # a regular expression is given with an arbitrary number of
            # contexts, evaluate only the first one in case it is a regexp.

            # The regexp is fully processed so that the value of all its groups
            # is computed

            # for all database tables (ie, implicitly ignoring regexps) within
            # the current database specification
            for itable in [itable for itable in self._dbspec
                           if isinstance (itable, dbparser.DBTable)]:

                # now, for all regular expressions mentioned in any column of
                # this table
                for icolumn in [icolumn for icolumn in  itable
                                if icolumn.get_vartype () == "REGEXP"]:

                    # create a dbexpression for this particular definition
                    expression = dbexpression.DBExpression (icolumn.get_vartype (),
                                                            icolumn.get_variable (),
                                                            self._logger,
                                                            self._logfilter)

                    # compute the regular expression to evaluate. If it has no
                    # contexts, then use it directly. Otherwise, consider only
                    # the first context and evaluate it only in case it is a
                    # regexp
                    if not expression.has_context ():

                        # then copy its definition from the database
                        # specification table which is always of the form
                        # <prefix>.<suffix>. 'index' is intentionally used to
                        # let Python raise an exception in case a dot is missing
                        regexp = icolumn.get_variable () [0:string.index (icolumn.get_variable (),
                                                                          '.')]

                    else:

                        # take the first context which is always of the form
                        # <prefix>.<suffix>. 'index' is intentionally used to
                        # let Python raise an exception in case a dot is missing
                        prefix = expression.get_context () [0] [0:string.index (expression.get_context () [0], '.')]

                        # in case this prefix exists as the name of a regular
                        # expression then go ahead with it,
                        if self._dbspec.get_regexp (prefix):
                            regexp = prefix
                        else:

                            # otherwise, skip it
                            continue

                    # and now, access the instance of the regexp with the name
                    # we computed above
                    iregexp = self._dbspec.get_regexp (regexp)

                    # in case this is the default regexp, then skip it since
                    # they've been all already processed above
                    if iregexp.get_name () == 'default':
                        continue

                    # also, in case that this regular expression was already
                    # processed, then skip it now (we can do this since the
                    # groups of all regexp are processed at once)
                    if iregexp.get_name () in self._regexp:
                        continue

                    self._logger.info (" Processing %s" % iregexp)

                    # for all matches of this regexp in the current text file
                    for m in re.finditer (iregexp.get_specification (), contents):

                        # add this variable to the regexp namespace as a
                        # multi-key attribute with as many keys as groups there
                        # are in the regexp. The multi-attribute should be named
                        # to allow projections later on. The key names are the
                        # group names themselves
                        keys = tuple ([igroup for igroup in m.groupdict ()])
                        BotParser._regexp.setkeynames (iregexp.get_name (), *keys)

                        # now, compute the value of this multi-key attribute
                        # which is a tuple with the matches of the regexp. Note
                        # that blank spaces are stripped of at the right of the
                        # match. This makes it easier for users to define
                        # regexps that can include the blank space in between
                        # without worrying for the trailing blank spaces
                        values = [string.rstrip (m.group (igroup), ' ')
                                  for igroup in m.groupdict ()]

                        # the policy is to accumulate values so that read the
                        # current value of this multi-key attribute in case it
                        # exists
                        if iregexp.get_name () in BotParser._regexp:

                            currvalues = BotParser._regexp.getattr (iregexp.get_name (),
                                                                    key = dict (zip (keys, keys)))
                            BotParser._regexp.setattr (iregexp.get_name (),
                                                       key = dict (zip (keys, keys)),
                                                       value = currvalues + [tuple (values)])

                        # otherwise, initialize the contents of this multi-key
                        # attribute to a list which contains a single tuple with
                        # the values of this match
                        else:
                            BotParser._regexp.setattr (iregexp.get_name (),
                                                       key = dict (zip (keys, keys)),
                                                       value = [tuple (values)])


                    # and now perform the evaluation
                    result = expression.eval (self._dbspec, self._namespace, self._data, None,
                                              self._regexp, self._user)

        # results/
        # -------------------------------------------------------------------------
        # once this file has been processed, copy it to the results directory
        # after applying the substitution specified in the output directive.

        # take care of the compress flag. If bzip2 compression was
        # requested apply it
        if (self._compress):
            self._logger.debug (" Compressing the contents of file '%s'" % txtfile)

            _bz2 (txtfile, remove=False)

            # and now, move it to its target location with the suffix
            # 'bz2' taking care of the substitution provided with the
            # output flag
            shutil.move (txtfile + '.bz2',
                         os.path.join (resultsdir, self._sub (self._output) + '.bz2'))

        # otherwise, just perform a backup copy of the parsed file
        else:
            shutil.copy (txtfile, os.path.join (resultsdir, self._sub (self._output)))


    # -----------------------------------------------------------------------------
    # wrapup
    #
    # wrapup performing the last operations
    # -----------------------------------------------------------------------------
    def wrapup (self, dbspec, configdir):

        """
        wrapup performing the last operations
        """

        # copy the database specification to the config dir
        if isinstance (dbspec, dbtools.DBVerbatim):
            with open (os.path.join (configdir, 'database.db'), 'w') as database:
                database.write (dbspec.data)

        elif isinstance (dbspec, dbtools.DBFile):
            shutil.copy (dbspec.filename,
                         os.path.join (configdir, os.path.basename (dbspec.filename)))
        else:
            raise ValueError (" Incorrect dbspec in wrapup")


    # -----------------------------------------------------------------------------
    # go
    #
    # main service provided by this class. It automates the whole parsing
    # process. It parses the contents of all files specified in txtfile (which
    # is a list of strings) according to the specification given in dbfile. It
    # writes down the results in the database whose name is given in dbname
    #
    # The argnamespace is the Namespace of the parser used (which should be an
    # instance of argparse or None). Other (optional) parameters are:
    #
    # directory - target directory where all output is recorded
    # output - filenames given to the backup copies of the parsed files
    # logger - if a logger is given, autobot uses a child of it. Otherwise, it
    #          creates its own logger
    # logfilter - if the client code uses a logger that requires additional
    #             information, a logging.Filter should be given here
    # prologue - if a class is provided here then __call__ () is automatically
    #            invoked before parsing every text file. This class should
    #            be a subclass of BotAction so that it automatically inherits
    #            all the attributes
    # epilogue - if a class is provided here then __call__ () is automatically
    #            invoked after parsing every text file. This class should be a
    #            subclass of BotAction so that it automatically inherits all
    #            the attributes
    # enter - much like prologue but __call__ is automatically invoked before
    #         parsing the first text file
    # windUp - much like epilogue but __call__ is automatically invoked after
    #          parsing the last text file
    # quiet - if given, some additional information is skipped
    # -----------------------------------------------------------------------------
    def go (self, txtfile, dbfile, dbname="$name.db", directory=os.getcwd (),
            compress=False, argnamespace=None, output="$name", logger=None, logfilter=None,
            prologue=None, epilogue=None, enter=None, windUp=None,
            quiet=False):
        """
        main service provided by this class. It automates the whole parsing
        process. It parses the contents of all files specified in txtfile (which
        is a list of strings) according to the specification given in dbfile. It
        writes down the results in the database whose name is given in dbname

        The argnamespace is the Namespace of the parser used (which should be an
        instance of argparse or None). Other (optional) parameters are:

        directory - target directory where all output is recorded
        output - filenames given to the backup copies of the parsed files
        logger - if a logger is given, autobot uses a child of it. Otherwise, it
                 creates its own logger
        logfilter - if the client code uses a logger that requires additional
                    information, a logging.Filter should be given here
        prologue - if a class is provided here then __call__ () is automatically
                   invoked before parsing every text file. This class should
                   be a subclass of BotAction so that it automatically inherits
                   all the attributes
        epilogue - if a class is provided here then __call__ () is automatically
                   invoked after parsing every text file. This class should be a
                   subclass of BotAction so that it automatically inherits all
                   the attributes
        enter - much like prologue but __call__ is automatically invoked before
                parsing the first text file
        windUp - much like epilogue but __call__ is automatically invoked after
                 parsing the last text file
        quiet - if given, some additional information is skipped
        """

        # copy the attributes
        (self._txtfile, self._dbfile, self._dbname, self._directory,
         self._compress, self._argnamespace, self._output,
         self._prologue, self._epilogue, self._quiet) = \
         (txtfile, dbfile, dbname, directory,
          compress, argnamespace, output,
          prologue, epilogue, quiet)

        # logger settings - if a logger has been passed, just create a child of
        # it
        self._logfilter = logfilter
        if logger:
            self._logger = logger.getChild ('bots.BotParser')

            # in case a filter has been given add it and finally set the log level
            if logfilter:
                self._logger.addFilter (logfilter)

        # otherwise, create a simple logger based on a stream handler
        else:
            self._logger = logging.getLogger(self.__class__.__module__ + '.' +
                                             self.__class__.__name__)
            handler = logging.StreamHandler ()
            handler.setLevel (BotParser._loglevel)
            handler.setFormatter (logging.Formatter (" %(levelname)-10s:   %(message)s"))
            self._logger.addHandler (handler)

            # not passing a logger does not mean that other loggers do not exist
            # so that make sure that the log messages generated here are not
            # propagated upwards in the logging hierarchy
            self._logger.propagate = False

        self._logger.debug (" Starting automated parsing ...")

        # check that all parameters are valid
        self.check_flags (self._txtfile, self._dbfile, self._directory)

        # and now, create the database specification

        # process the database either as a string with a path to the file to
        # parse or just simply copy the specification in case it was given as a
        # verbatim string or as a file already processed
        # proceed similarly in case of the database specification file
        if type (self._dbfile) is str:
            self._logger.debug (" Parsing the database specification file ...")
            self._dbspec  = dbtools.DBFile (self._dbfile)
        elif isinstance (self._dbfile, dbtools.DBVerbatim):
            self._logger.debug (" The database was given as a verbatim specification")
            self._dbspec = self._dbfile
            self._dbfile = BotParser.defaultname
        elif isinstance (self._dbfile, dbtools.DBFile):
            self._logger.debug (" The database was given as a file already parsed")
            self._dbspec = self._dbfile
            self._dbfile = self._dbfile.filename
        else:
            raise ValueError (" Incorrect specification of the database")

        # and now, unless quiet is enabled, show the flags
        if (not self._quiet):

            self.show_switches (self._txtfile, self._dbfile, self._directory)

        # setup the necessary environment and retrieve the directores to be
        # used
        (resultsdir, configdir) = self.setup (self._directory)

        # is the user overridden the definition of the data regexp?
        for iregexp in self._dbspec.get_regexp ():

            # if so, override the current definition and show an info message
            if iregexp.get_name () == 'default':
                self.statregexp = iregexp.get_specification ()
                self._logger.warning (" The data regexp has been overridden to '%s'" % iregexp.get_specification ())

        # in case it is requested to execute an *enter* action do it now
        if enter:
            action = enter (dbfile=self._dbfile,
                            directory=self._directory,
                            namespace=BotParser._namespace,
                            user=BotParser._user)
            action (self._logger)

        # record the start time
        self._starttime = datetime.datetime.now ()

        # now, invoke the automated parsing of this particular text file
        self.parse_all_files (self._txtfile, resultsdir)

        # record the end time
        self._endtime = datetime.datetime.now ()

        # and wrapup
        self.wrapup (self._dbspec, configdir)

        # before leaving, execute a windup action in case it was requested
        if windUp:
            action = windUp (dbfile=self._dbfile,
                             directory=self._directory,
                             namespace=BotParser._namespace,
                             data=BotParser._data,
                             user=BotParser._user)
            action (self._logger)



# Local Variables:
# mode:python
# fill-column:80
# End:
