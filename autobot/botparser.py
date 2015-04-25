#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# botparser.py
# Description: Base class of all parsebots
# -----------------------------------------------------------------------------
#
# Started on  <Fri Sep 26 00:39:36 2014 Carlos Linares Lopez>
# Last update <sábado, 25 abril 2015 13:05:52 Carlos Linares Lopez (clinares)>
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
    # * namespace: denoted also as the main or sys namespace. It contains sys
    #              information and main variables
    # * data: It contains datavar and filevar
    # * user: this namespace is never used by autobot and it is created only for
    #         user specifics
    # * param: it stores param and dirvar. It is not used by botparser but by
    #          bottester
    # * regexp : it stores the results of processing the contents of a file with
    #            the regexps found in the database specification
    # * snippet: saves the values of variables computed with external Python
    #            code that can be initialized with variables in autobot
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
    # * snippet: snippets are also defined separately in the database
    #            specification file and can be used in the specification of
    #            database tables to refer to the different output variables that
    #            are computed by the snippet
    #
    # Importantly, all these variables can be qualified with contexts which have
    # to be regexps. When contexts are used, the final value results of applying
    # the next regexp to the previous value until all contexts have been
    # processed.
    #
    # to make these relationships more apparent, the variables given in the
    # database specification file can be preceded by a prefix that provides
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
    # Likewise, snippets are defined with the syntax:
    #
    # snippet <name>
    #    input-var1 = <autobot-variable>
    #          ...  = ...
    #    input-varn = <autobot-variable>
    #    return output-var1
    #      ...      ...
    #    return output-varn
    #    code <python-file>
    #
    # This way, any column in the specification of a database can use the
    # variables computed by the execution of the <python-file> with the syntax
    # <name>.<output-var>
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
    # snippet   | snippet
    # ----------+-----------------
    #
    # These associations are implemented in the evaluation of dbexpressions
    # -----------------------------------------------------------------------------
    _namespace = namespace.Namespace ()         # sysvar, mainvar
    _data      = namespace.Namespace ()         # datavar, filevar
    _param     = namespace.Namespace ()         # param, dirvar (to be used in BotTester)
    _user      = namespace.Namespace ()         # user space
    _regexp    = namespace.Namespace ()         # regexp
    _snippet   = namespace.Namespace ()         # snippets of python code


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
 -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-1], __version__, txtfile, dbfile, directory))


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
    # copy_file
    #
    # copy the contents of src to the directory given in target and give it the
    # name specified in dst. If move is given, the file is moved to the target
    # directory, otherwise, it is copied
    #
    # If compression was requested it compresses the
    # copied file
    # -----------------------------------------------------------------------------
    def copy_file(self, src, target, dst, move=False):
        """
        copy the contents of src to the directory given in target and give it
        the name specified in dst. If compression was requested it compresses the
        copied file
        """

        # take care of the compress flag. If bzip2 compression was requested
        # apply it
        if (self._compress):
            self._logger.debug(" Compressing file '%s'" % src)

            _bz2(src, remove=False)

            # and now, move it to its target location with the suffix 'bz2'
            # taking care of the substitution provided with the output flag
            shutil.move(src + '.bz2',
                        os.path.join(target, dst + '.bz2'))

        # otherwise, just perform a backup copy of the parsed file
        else:

            # if move was requested, then just move this file
            if move:
                shutil.move(src, target)

            # otherwise, copy it
            else:
                shutil.copy(src, os.path.join(target,dst))

            
    # -----------------------------------------------------------------------------
    # eval_regexp
    #
    # compute the value of the regexp defined in the specified struct with the
    # contents specified in the second argument. Legal structs are either the
    # column of a database table or the definition of an input statement in a
    # snippet, ie., the only places where regexps can be used.  As a result, it
    # writes in the regexp namespace its final value
    # -----------------------------------------------------------------------------
    def eval_regexp(self, struct, contents):
        """compute the value of the regexp defined in the specified struct with the
        contents specified in the second argument. Legal structs are either the
        column of a database table or the definition of an input statement in a
        snippet, ie., the only places where regexps can be used.  As a result,
        it writes in the regexp namespace its final value

        """

        self._logger.critical(" Invoking eval_regexp!")

        # create a dbexpression for this particular definition
        expression = dbexpression.DBExpression (struct.get_vartype (),
                                                struct.get_variable (),
                                                self._logger,
                                                self._logfilter)

        # compute the regular expression to evaluate. If it has no contexts,
        # then use it directly. Otherwise, consider only the first context and
        # evaluate it only in case it is a regexp
        if not expression.has_context ():

            # then copy its definition from the database specification table
            # which is always of the form <prefix>.<suffix>. 'index' is
            # intentionally used to let Python raise an exception in case a dot
            # is missing
            prefix = struct.get_variable () [0:string.index (struct.get_variable (),
                                                              '.')]

        else:

            # take the first context which is always of the form
            # <prefix>.<suffix>. 'index' is intentionally used to let Python
            # raise an exception in case a dot is missing
            prefix = expression.get_context()[0][0:string.index (expression.get_context () [0],
                                                                 '.')]

        # in case this prefix exists as the name of a regular expression then go
        # ahead with it.
        #
        # Strange, huh? the reason is that a prefix might result from the first
        # part of a context and that's not necessarily a regexp!!
        iregexp = self._dbspec.get_regexp (prefix)
        if not iregexp:
            return

        # if this regexp has been already processed or if it is the default
        # regexp (which has been already processed above), then skip it
        if iregexp.get_name () == 'default' or iregexp.get_name () in self._regexp:
            return

        self._logger.info (" Processing %s" % iregexp)

        # for all matches of this regexp in the current text file
        for m in re.finditer (iregexp.get_specification (), contents):

            # add this variable to the regexp namespace as a multi-key attribute
            # with as many keys as groups there are in the regexp. The
            # multi-attribute should be named to allow projections later on. The
            # key names are the group names themselves
            keys = tuple ([igroup for igroup in m.groupdict ()])
            BotParser._regexp.setkeynames (iregexp.get_name (), *keys)

            # now, compute the value of this multi-key attribute which is a
            # tuple with the matches of the regexp. Note that blank spaces are
            # stripped of at the right of the match. This makes it easier for
            # users to define regexps that can include the blank space in
            # between without worrying for the trailing blank spaces
            values = [string.rstrip (m.group (igroup), ' ')
                      for igroup in m.groupdict ()]

            # the policy is to accumulate values so that read the current value
            # of this multi-key attribute in case it exists
            if iregexp.get_name () in BotParser._regexp:

                currvalues = BotParser._regexp.getattr (iregexp.get_name (),
                                                        key = dict (zip (keys, keys)))
                BotParser._regexp.setattr (iregexp.get_name (),
                                           key = dict (zip (keys, keys)),
                                           value = currvalues + [tuple (values)])

            # otherwise, initialize the contents of this multi-key attribute to
            # a list which contains a single tuple with the values of this match
            else:
                BotParser._regexp.setattr (iregexp.get_name (),
                                           key = dict (zip (keys, keys)),
                                           value = [tuple (values)])

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
    def parse_single_file(self, txtfile, resultsdir):
        """looks for all matches of all regular expressions defined in the database
        specification in the given text file. The results of all matches are
        written to the regexp namespace. Also, the data namespace is populated
        with the results of the matches of the default regexp

        Also, the textfile is backed up to the resultsdir
        """

        def _eval_snippet(variable):
            """creates a dbexpression that consists of a snippet and requests its
            evaluation, thus updating the snippet namespace
            """

            # botparser is responsible only for making sure that data necessary
            # to evaluate expressions is available in the corresponding
            # namespaces. Thus, if this snippet is volatile (ie, if any of its
            # output variables has been declared as volatile) then it is not
            # evaluated here. Instead, it should be evaluated when the system
            # is ready for downloading data to the database
            snippetname = string.split(variable, '.')[0]
            snippet = self._dbspec.get_snippet(snippetname)
            if snippet.get_keyword() == 'volatile':
                return

            # now, in case it is static, it is evaluated never more than once
            if snippetname in BotParser._snippet:
                return

            # otherwise, to evaluate this snippet create an expression with
            # this snippet
            expression = dbexpression.DBExpression(dbparser.SNIPPETNST,
                                                   variable,
                                                   self._logger,
                                                   self._logfilter)

            # and request its evaluation
            expression.eval_snippet(dbspec=self._dbspec,
                                    sys=BotParser._namespace,
                                    data=BotParser._data,
                                    param=None,
                                    regexp=BotParser._regexp,
                                    snippet=BotParser._snippet,
                                    user=BotParser._user)

        def _eval_filevar(variable):
            """creates a dbexpression that consists of a filevar and requests its
            evaluation, thus updating the data namespace
            """

            # create a dbexpression and require its evaluation updating
            # the data namespace
            dbexpression.DBExpression(dbparser.FILENST,
                                      variable,
                                      self._logger,
                                      self._logfilter).eval_filevar(data=BotParser._data)

        def _bz2(filename, remove=False):
            """compress the contents of the given filename and writes the results to a
            file with the same name + '.bz2'. If remove is enabled, the
            original filename is removed
            """

            # open the original file in read mode
            with open(filename, 'r') as input:

                # create a bz2file to write compressed data
                with bz2.BZ2File(filename+'.bz2', 'w', compresslevel=9) as output:

                    # and just transfer data from one file to the other
                    shutil.copyfileobj(input, output)

            # if remove is enabled, remove the original filename
            if (remove):
                os.remove(filename)

        # default regexp
        # ---------------------------------------------------------------------
        # read all contents of the input file - yep, this might take a lot
        # of memory but the alternative, to process each line separately
        # would not allow to match various lines simultaneously

        # open the file in read mode
        with open(txtfile, "r") as stream:

            # for all matches of the default regexp in the current text file
            for imatch in re.finditer(BotParser.statregexp, stream.read()):

                # and store every match in the data namespace
                BotParser._data[imatch.group('varname').rstrip(' ')] = \
                    imatch.group('value')

        # for all database tables (ie, implicitly ignoring snippets) within the
        # current database specification
        for itable in [itable for itable in self._dbspec
                       if isinstance(itable, dbparser.DBTable)]:

            # snippets
            # ---------------------------------------------------------------------
            # now, for all snippets mentioned in any column of this table
            for icolumn in [icolumn for icolumn in itable
                            if icolumn.get_vartype() == dbparser.SNIPPETNST]:

                _eval_snippet(icolumn.get_variable())

            # filevars
            # -------------------------------------------------------------------------
            # populate the data namespace with the contents of files (filevars)
            # as specified in the database specification file
            for icolumn in [icolumn for icolumn in itable
                            if icolumn.get_vartype() == dbparser.FILENST]:

                _eval_filevar(icolumn.get_variable())

            # regexps
            # ---------------------------------------------------------------------
            # also, for all regular expressions that start with either a
            # snippet or a file
            for icolumn in [icolumn for icolumn in itable
                            if icolumn.get_vartype() == dbparser.REGEXPNST]:

                # create an expression with this regular expression
                expression = dbexpression.DBExpression(icolumn.get_vartype(),
                                                       icolumn.get_variable(),
                                                       self._logger,
                                                       self._logfilter)

                # retrieve the first context
                head = expression.get_context()[0]

                # and retrieve its prefix and variable name
                (prefix, variable) = string.split(head, '.')

                # verify whether this is a snippet ...
                if self._dbspec.get_snippet(prefix):

                    _eval_snippet(head)

                # ... or a file variable
                elif string.upper(prefix) == dbparser.FILENST:

                    _eval_filevar(variable)

                    
    # -----------------------------------------------------------------------------
    # parse_all_files
    #
    # starts the automated parsing of all text files given in txtfiles. All
    # these files are copied to the results directory given in resultsdir.
    #
    # if prologue/epilogue actions are specified then its __call__ method is
    # invoked before/after parsing every text file.
    # -----------------------------------------------------------------------------
    def parse_all_files(self, txtfiles, resultsdir):
        """
        starts the automated parsing of all text files given in txtfiles. All
        these files are copied to the results directory given in resultsdir.

        if prologue/epilogue actions are specified then its __call__ method is
        invoked before/after parsing every text file.
        """

        # before parsing all the text files, initialize the current file to the
        # empty string. This will enforce the creation of a first database that
        # will contain the results of the parsing
        currdbname = str()

        # processing files
        # -------------------------------------------------------------------------
        # keep track of the file id as an integer
        idx = 0

        # now, process every text file
        for itxtfile in txtfiles:

            # namespaces
            # -------------------------------------------------------------------------
            # initialize the contents of the namespaces that hold variables
            # whose value is dependent upon the contents of the current file
            BotParser._namespace.clear()
            BotParser._data.clear()
            BotParser._regexp.clear()
            BotParser._snippet.clear()

            # - main (sys) namespace
            # -------------------------------------------------------------------------
            # initialize the main namespace with the parameters passed to the
            # main script (ie., the parsebot), mainvars. These are given in
            # self._argnamespace. Since the argparser automatically casts type
            # according to their type field, they are all converted into
            # strings here to allow a uniform treatment
            if self._argnamespace:
                for index, value in self._argnamespace.__dict__.items():
                    BotParser._namespace[index] = str(value)

            # also, with the contents of this file
            with open(itxtfile, "r") as stream:
                BotParser._namespace.stdout = stream.read()
            stream.close()

            # and also with the following sys variables
            #
            #   index         - index of this file in the range [0, ...)
            #   filename      - name of this text file
            #   date          - current date
            #   time          - current time
            #   startfullparsedatetime - when the whole parsing started in
            #                            date/time format
            #   startfullparsetime - when the whole parsing started in secs
            #                        from Epoch
            #
            # Note that other fields are added below to register the right
            # timings when every parsing started/ended
            BotParser._namespace.index = idx
            BotParser._namespace.filename = os.path.basename(itxtfile)
            BotParser._namespace.date = datetime.datetime.now().strftime("%Y-%m-%d")
            BotParser._namespace.time = datetime.datetime.now().strftime("%H:%M:%S")
            BotParser._namespace.startfullparsedatetime = datetime.datetime.now()
            BotParser._namespace.startfullparsetime = time.time()

            self._logger.info(" Starting the automated parsing of file '%s'" % itxtfile)

            # parsing
            # -------------------------------------------------------------------------
            # execute the prologue in case any was given (note that the run
            # time is computed right now) and register also the exact time when
            # the processing of this file started (including the prologue)
            if self._prologue:
                action = self._prologue(textfile=itxtfile,
                                        dbfile=self._dbfile,
                                        directory=self._directory,
                                        startfullparsetime=BotParser._namespace.startfullparsetime,
                                        namespace=BotParser._namespace,
                                        data=BotParser._data,
                                        user=BotParser._user)
                action(self._logger)

            # now, invoke the automated parsing of this particular text file
            # after recording the exact timings before and after (ie, this do
            # not take the time of the prologue/epilogue into account)
            BotParser._namespace.startparsedatetime = datetime.datetime.now()
            BotParser._namespace.startparsetime = time.time()

            self.parse_single_file(itxtfile, resultsdir)

            BotParser._namespace.endparsedatetime = datetime.datetime.now()
            BotParser._namespace.endparsetime = time.time()

            # now, before processing the next text file, invoke the epilogue in
            # case any was given
            if self._epilogue:
                action = self._epilogue(textfile=itxtfile,
                                        dbfile=self._dbfile,
                                        directory=self._directory,
                                        startparsetime = BotParser._namespace.startparsetime,
                                        endparsetime = BotParser._namespace.endparsetime,
                                        namespace=BotParser._namespace,
                                        data=BotParser._data,
                                        user=BotParser._user)
                action(self._logger)

            # and register the exact time when the whole parsing of this file
            # ended including processing the epilogue both in seconds from Epoc
            # (endruntime) and in date/time format (enddatetime)
            BotParser._namespace.endfullparsetime = time.time()
            BotParser._namespace.endfullparsedatetime = datetime.datetime.now()

            # results/
            # -------------------------------------------------------------------------
            # once this file has been processed, copy it to the results directory
            # after applying the substitution specified in the output directive.
            self.copy_file(itxtfile, resultsdir, self._sub(self._output))

            # database
            # -------------------------------------------------------------------------
            # now, write data to the database. Note that we do this after
            # invoking the epilogue so that the user gets a finer control on
            # the data that is about to be inserted into the database

            # First. compute the name of the database
            dbname = self._sub(self._dbname)

            # create a new SQLITE3 database connection
            dbhandler = sqltools.dbaccess(dbname)

            # in case we get a different database
            if dbname != currdbname:

                # create the tables
                for itable in self._dbspec.get_db():
                    dbhandler.create_table(itable)

                # and remember the name of the current database
                currdbname = dbname

            # now, populate the datatase
            self._logger.debug(" Inserting data into '%s'" % currdbname)
            for itable in self._dbspec.get_db():
                self._logger.debug(" Populating '%s'" % itable.get_name())
                dbhandler.insert_data(itable,
                                      itable.poll(dbspec=self._dbspec,
                                                  namespace=BotParser._namespace,
                                                  data=BotParser._data,
                                                  param=None,
                                                  regexp=BotParser._regexp,
                                                  snippet=BotParser._snippet,
                                                  user=BotParser._user,
                                                  logger=self._logger,
                                                  logfilter=self._logfilter))

            # and close the database
            dbhandler.close()

            # update the index
            idx += 1

    # -----------------------------------------------------------------------------
    # wrapup
    #
    # wrapup performing the last operations
    # -----------------------------------------------------------------------------
    def wrapup(self, dbspec, configdir):
        """wrapup performing the last operations
        """

        # copy the database specification to the config dir
        if isinstance(dbspec, dbtools.DBVerbatim):
            with open(os.path.join(configdir, 'database.db'), 'w') as database:
                database.write(dbspec.data)

        elif isinstance(dbspec, dbtools.DBFile):
            shutil.copy(dbspec.filename,
                        os.path.join(configdir, os.path.basename(dbspec.filename)))
        else:
            raise ValueError(" Incorrect dbspec in wrapup")

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
        # it and save the log filter since it might be given to other methods
        # invoked from this class
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

        # is the user overriding the definition of the default data regexp?
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
# fill-column:79
# End:
