#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# bottester.py
# Description: Base class of all testbots
# -----------------------------------------------------------------------------
#
# Started on  <Fri Sep 26 00:03:37 2014 Carlos Linares Lopez>
# Last update <viernes, 24 abril 2015 23:22:47 Carlos Linares Lopez (clinares)>
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
Base class of all testbots
"""

# imports
# -----------------------------------------------------------------------------
import bz2                      # bzip2 compression service
import datetime                 # date/time
import logging                  # loggers
import os                       # os services
import re                       # regular expressions
import shutil                   # shell utitilies such as copying files
import subprocess               # subprocess management
import string                   # rstrip
import time                     # time management

from collections import defaultdict

import dbparser                 # parsing of database specification files
import dbtools                  # database specification files
import namespace                # single and multi key attributes
import sqltools                 # sqlite3 database access
import systools                 # process management
import timetools                # timing management
import tsttools                 # test specification files


# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# -----------------------------------------------------------------------------
# BotTester
#
# Base class of all testbots.
#
# It automates the execution of any testbot and the automated extraction of
# information according to the specification of a database specification file
# -----------------------------------------------------------------------------
class BotTester (object):
    """
    Base class of all testbots

    It automates the execution of any testbot and the automated extraction of
    information according to the specification of a database specification file
    """

    # how long to wait between SIGTERM and SIGKILL
    # -----------------------------------------------------------------------------
    kill_delay = 5

    # default string used for tst/db files that are passed as verbatim strings
    # and thus, have no name
    # -----------------------------------------------------------------------------
    defaultname = "<processed>"

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
    # * param: it stores param and dirvar
    # * regexp : it stores the results of processing the standard output with
    #            the regexps found in the database specification
    #
    # These namespaces automatically use the different variables (most of them
    # defined in the dbparser) whose purpose is defined below:
    #
    # * sysvar: these are variables computed by autobot at every cycle of the
    #           execution of the solver. Every 'check' seconds the new contents
    #           of these variables is computed
    #
    # * mainvar: these are the flags given to the main script using autobot
    #            (ie., testbot) These variables can be used to create a template
    #            for the 'output' file
    #
    # * datavar: data processed from the stdout of the executable. These data is
    #            retrieved using the default regular expression and they are
    #            processed only once after the execution of the solver over
    #            every test case
    #
    # * filevar: these variables are given as filenames whose value are the
    #            contents of the file
    #
    # * param: these are the flags given to the executable. They are retrieved
    #          from the specification of the current test case under execution
    #
    # * dirvar: these are also the flags given to the executable but they are
    #           named after their position
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
    # dirvar           | 'dir.'
    # filevar          | 'file.'
    # mainvar          | "main.'
    # param            | 'param.'
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
    # param     | param, dirvar
    # regexp    | regexp
    # ----------+-----------------
    #
    # These associations are implemented in the poll method of the dbparser
    # -----------------------------------------------------------------------------
    _namespace = namespace.Namespace ()         # sysvar, mainvar
    _data      = namespace.Namespace ()         # datavar, filevar
    _user      = namespace.Namespace ()         # user space
    _param     = namespace.Namespace ()         # param, dirvar
    _regexp    = namespace.Namespace ()         # regexp

    # -----------------------------------------------------------------------------
    # check_flags
    #
    # check the parameters given to the automated execution of this instance
    # -----------------------------------------------------------------------------
    def check_flags (self, solver, tstfile, dbfile, timeout, memory, check, directory):

        """
        check the parameters given to the automated execution of this instance
        """

        # verify that all solvers are accessible
        for isolver in solver:

            if (not os.access (isolver, os.F_OK) or
                not os.access (os.path.dirname (isolver), os.X_OK)):
                self._logger.critical ("""
 The solver '%s' does not exist or it resides in an unreachable location
 Use '--help' for more information
""" % isolver)
                raise ValueError (" The solver is not accessible")

        # verify also that the test cases (been given as a str) are accessible
        # as well
        if (tstfile and tstfile != BotTester.defaultname and
            (not os.access (tstfile, os.F_OK) or
             not os.access (os.path.dirname (tstfile), os.R_OK))):
            self._logger.critical ("""
 The test cases specification file does not exist or it resides in an unreachable location
 Use '--help' for more information
""")
            raise ValueError (" The tests specification file is not accessible")

        # and perform the same validation with regard to the db file
        if (dbfile and dbfile != BotTester.defaultname and
            (not os.access (dbfile, os.F_OK) or
             not os.access (os.path.dirname (dbfile), os.R_OK))):
            self._logger.critical ("""
 The database specification file does not exist or it resides in an unreachable location
 Use '--help' for more information
""")
            raise ValueError (" The database specification file is not accessible")

        # verify that check is not negative
        if (check < 0):
            self._logger.critical (" The check flag should be non negative")
            raise ValueError (" Period between successive pings is negative")

        # finally, verify the timeout and memory bounds
        if (timeout <= 0):
            self._logger.critical (" The timeout param shall be positive!")
            raise ValueError (" Timeout is negative")

        if (memory <= 0):
            self._logger.critical (" The memory param shall be positive!")
            raise ValueError (" Memory allotted is negative")


    # -----------------------------------------------------------------------------
    # show_switches
    #
    # show a somehow beautified view of the current params
    # -----------------------------------------------------------------------------
    def show_switches (self, solver, tstfile, dbfile, timeout, memory, check, directory, compress):
        """
        show a somehow beautified view of the current params
        """

        # compute the solvers' names
        solvernames = map (lambda x:os.path.basename (x), solver)

        self._logger.info ("""
  %s %s %s
 -----------------------------------------------------------------------------
  * Solver               : %s
  * Tests                : %s
  * Database             : %s

  * Check flag           : %.2f seconds

  * Directory            : %s
  * Compression          : %s
  * Time limit           : %i seconds
  * Memory bound         : %i bytes
 -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-2], __version__, solvernames, tstfile, dbfile, check, directory, {False: 'disabled', True: 'enabled'}[compress], timeout, memory))


    # -----------------------------------------------------------------------------
    # setup
    #
    # sets up all the necessary environment. It returns: the directory where the
    # results should be copied (ie, stdout and stderr of the process); the
    # config dir where additional information (such as the test specification
    # and db specification) should be written and the logdirectory where the
    # logs should be stored.
    # -----------------------------------------------------------------------------
    def setup (self, solvername, directory):
        """
        sets up all the necessary environment. It returns: the directory where
        the results should be copied (ie, stdout and stderr of the process); the
        config dir where additional information (such as the test specification
        and db specification) should be written and the logdirectory where the
        logs should be stored.
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


        # compute the target directory
        targetdir = os.path.join (directory, solvername)

        # the given directory should exist at this time, but not its
        # subdirectories. A couple of sanity checks follow:
        if (not os.access (directory, os.F_OK)):
            os.makedirs (directory)
            self._logger.debug (" The directory '%s' has been created!" % directory)
        if (os.access (targetdir, os.F_OK)):        # paranoid checking!!
            self._logger.critical (" The directory '%s' already exists!" % targetdir)
            raise ValueError

        # create the target directory
        os.mkdir (targetdir)

        # create another subdir to store the results. Note that the absolute path is
        # computed. Passing the absolute path to the results dir prevents a number
        # of errors
        resultsdir = _mksubdir (targetdir, "results")

        # create also an additional directory to store additional information
        # such as the test cases
        configdir = _mksubdir (targetdir, "config")

        # and create also an additional directory to store different sorts of log
        # information
        logdir = _mksubdir (targetdir, "log")

        # return the directories to be used in the experimentation
        return (resultsdir, configdir, logdir)


    # -----------------------------------------------------------------------------
    # fetch
    #
    # gather OS version info, cpu info, mem info and swap space info to be shown in
    # different files located at the log dir
    # -----------------------------------------------------------------------------
    def fetch (self, logdir):
        """
        gather OS version info, cpu info, mem info and swap space info to be shown
        in different files located at the log dir
        """

        self._logger.debug (" Fetching OS info ...")

        shutil.copy ("/proc/version", os.path.join (logdir, "ver-info.log"))
        shutil.copy ("/proc/cpuinfo", os.path.join (logdir, "cpu-info.log"))
        shutil.copy ("/proc/meminfo", os.path.join (logdir, "mem-info.log"))
        shutil.copy ("/proc/swaps"  , os.path.join (logdir, "swap-info.log"))


    # -----------------------------------------------------------------------------
    # run_all_cases
    #
    # invokes the execution of the given solver *in the same directory where it
    # resides* for solving all cases specified in the current test specification
    # using the allotted timeout and memory. The results are stored in
    # 'resultsdir' and different stats are stored in 'stats'.
    #
    # This method computes the name given to all the output files which are
    # named after the given user specifcation where variable substitutions
    # specified in the current namespace are allowed.
    #
    # If a prologue/epilogue is given (they should be a subclass of BotAction )
    # then its __call__ method is invoked before/after the execution of the
    # solver with every test case
    # -----------------------------------------------------------------------------
    def run_all_cases (self, solver, resultsdir, stats):
        """
        invokes the execution of the given solver *in the same directory where
        it resides* for solving all cases specified in the current test
        specification using the allotted timeout and memory. The results are
        stored in 'resultsdir' and different stats are stored in 'stats'.

        This method computes the name given to all the output files which are
        named after the given user specifcation where variable substitutions
        specified in the current namespace are allowed.

        If a prologue/epilogue is given (they should be a subclass of BotAction
        ) then its __call__ method is invoked before/after the execution of the
        solver with every test case
        """

        def _sub (string):
            """
            substitute in string the ocurrence of every keyword in the namespace
            used in this instance of BotTester (BotTester._namespace) with
            its value if it appears preceded by '$' in string and it is a
            str. Similar to Template.substitute but it also allows the
            substitution of strings which do not follow the convention of python
            variable names

            Of course, other namespaces can be used but _sub is used only to
            compute the name of the output file so that only static information
            is used
            """

            result = string                                 # initialization

            # now, substitute every ocurrence of every single attribute in
            # namespace with its value only in case the value is a string
            for ikey in [jkey for jkey in BotTester._namespace
                         if not isinstance (BotTester._namespace [jkey], dict)]:

                # perform the substitution enforcing the type of value to be str
                result = re.sub ('\$' + ikey, str (BotTester._namespace [ikey]), result)

            # and return the result now return result
            return result


        # now, for each test case
        for itst in self._tstspec:

            # namespaces
            # -------------------------------------------------------------------------
            # initialize the contents of the namespaces that hold variables
            # whose value depends upon the output of the current execution
            BotTester._namespace.clear ()
            BotTester._data.clear ()
            BotTester._regexp.clear ()

            # - main (sys) namespace
            # -------------------------------------------------------------------------
            # initialize the namespace with the parameters passed to the main
            # script (ie., the testbot), mainvars. These are given in
            # self._argnamespace. Since the argparser automatically casts type
            # according to their type field, they are all converted into strings
            # here to allow a uniform treatment
            if self._argnamespace:
                for index, value in self._argnamespace.__dict__.items ():
                    BotTester._namespace [index] = str (value)

            # and also with the following sys variables
            #
            #   index         - index of this file in the range [0, ...)
            #   name          - name of this text file
            #   date          - current date
            #   time          - current time
            #   startdatetime - when the whole parsing started in date/time
            #                   format
            #   startruntime - when the whole parsing started in secs from
            #                  Epoch
            #
            # Note that other fields are added below to register the right
            # timings when every parsing started/ended
            BotTester._namespace.index = itst.get_id ()
            BotTester._namespace.name  = os.path.basename (solver)
            BotTester._namespace.date  = datetime.datetime.now ().strftime ("%Y-%m-%d")
            BotTester._namespace.time  = datetime.datetime.now ().strftime ("%H:%M:%S")

            # compute the right name of the output file using the information in
            # the current namespace
            outputprefix = _sub (self._output)

            # - param namespace
            # -------------------------------------------------------------------------
            # and now, add the values of all the directives in this testcase in
            # the namespace param. These are automatically casted to string for
            # the convenience of other functions
            for idirective, ivalue in itst.get_values ().items ():
                BotTester._param [idirective] = str (ivalue)

            # and also with the position of every argument (so that $1 can be
            # interpreted as the first parameter, $2 as the second, and so on)
            # ---note that these numerical indices are casted to strings for the
            # convenience of other functions
            counter = 0
            for iarg in itst.get_args ():
                BotTester._param [str (counter)] = str (iarg)
                counter += 1

            # running
            # -------------------------------------------------------------------------
            # if a prologue was given, execute it now passing all parameters
            # (including the start run time which is computed right now)
            startruntime = time.time ()
            if self._prologue:
                action = self._prologue (solver=solver,
                                         tstspec=self._tstspec,
                                         itest=itst,
                                         dbspec=self._dbspec,
                                         timeout=self._timeout,
                                         memory=self._memory,
                                         output=outputprefix,
                                         check=self._check,
                                         basedir=self._directory,
                                         resultsdir=resultsdir,
                                         compress=self._compress,
                                         namespace=BotTester._namespace,
                                         user=BotTester._user,
                                         param=BotTester._param,
                                         stats=stats,
                                         startruntime=startruntime)
                action (self._logger)

            # invoke the execution of this test case and record the start run
            # time and end run time
            self._logger.info ('\t%s' % itst)
            self.run_single_case (os.path.abspath (solver),
                                  resultsdir, itst, outputprefix, stats)

            # finally, if an epilogue was given, execute it now passing by also
            # the end run time
            if self._epilogue:
                action = self._epilogue (solver=solver,
                                         tstspec=self._tstspec,
                                         itest=itst,
                                         dbspec=self._dbspec,
                                         timeout=self._timeout,
                                         memory=self._memory,
                                         output=outputprefix,
                                         check=self._check,
                                         basedir=self._directory,
                                         resultsdir=resultsdir,
                                         compress=self._compress,
                                         namespace=BotTester._namespace,
                                         data=BotTester._data,
                                         user=BotTester._user,
                                         param=BotTester._param,
                                         regexp=BotTester._regexp,
                                         stats=stats,
                                         startruntime=startruntime,
                                         endruntime=time.time ())
                action (self._logger)


    # -----------------------------------------------------------------------------
    # run_single_case
    #
    # executes the specified 'solver' (qualified with its full path) *in the
    # same directory where it resides* (this is fairly convenient in case the
    # solver needs additional input files which are then extracted from a
    # directory relative to the current location) for solving the particular
    # test case qualified by itst. It copies the stdout and stderr of the solver
    # in files named after output (plus either .log or .err) which are then
    # moved to the specified results directory 'resultsdir'. The data generated
    # is stored in 'stats'
    #
    # The forked process is pinged every 'check' seconds and it is launched with
    # computational resources 'timeout' and 'memory'
    # -----------------------------------------------------------------------------
    def run_single_case (self, solver, resultsdir, itst, output, stats):
        """
        executes the specified 'solver' (qualified with its full path) *in the
        same directory where it resides* (this is fairly convenient in case the
        solver needs additional input files which are then extracted from a
        directory relative to the current location) for solving the particular
        test case qualified by itst. It copies the stdout and stderr of the
        solver in files named after output (plus either .log or .err) which are
        then moved to the specified results directory 'resultsdir'. The data
        generated is stored in 'stats'

        The forked process is pinged every 'check' seconds and it is launched
        with computational resources 'timeout' and 'memory'
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


        # Initialization
        total_vsize = 0

        # create a timer
        runtimer = timetools.Timer ()

        # Now, a child is created which will host the solver execution while this
        # process simply monitors the resource comsumption. If any is exceeded the
        # child along with all its processes are killed
        with runtimer:

            # redirect the log and standard output to different files so that the
            # whole output is recorded
            (fdlog, fderr) = (os.open (os.path.join (os.getcwd (), output + ".log"),
                                       os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                       0666),
                              os.open (os.path.join (os.getcwd (), output + ".err"),
                                       os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                       0666))

            # create the child and record its process identifier
            # atorralba: Added parameter preexec_fn=os.setsid to address issue
            # #20. This ensures the execution of os.setsid after fork() so that
            # the new process has its own process group and it is not anymore in
            # the same process group than invokeplanner
            try:
                child = subprocess.Popen ([solver] + itst.get_args (),
                                          stdout = fdlog,
                                          stderr = fderr,
                                          cwd=os.path.dirname (solver),
                                          preexec_fn=os.setsid)
            except OSError:
                self._logger.critical (" OSError raised when invoking the subprocess")
                raise OSError

            except ValueError:
                self._logger.critical (" Popen was invoked with invalid arguments")
                raise ValueError

            child_pid = child.pid

            # initialization
            max_mem   = 0                           # max mem ever used
            real_time = 0                           # real time (in seconds)
            term_attempted = False                  # no SIGTERM yet
            time0 = datetime.datetime.now ()        # current time

            timeline = systools.ProcessTimeline ()  # create a process timeline

            while True:

                time.sleep(self._check)

                # get info of all the processes executed with the process group id
                # of the child and its children and add them to the timeline
                group = systools.ProcessGroup(os.getpgid (child_pid))
                timeline += group

                # compute the wall-clock time
                time1 = datetime.datetime.now ()    # time after sleeping
                real_time = (time1-time0).total_seconds ()  # compute wall clock time accurately

                # Generate the children information before the waitpid call to avoid a
                # race condition. This way, we know that the child_pid is a descendant.
                (pid, status) = os.waitpid (child_pid, os.WNOHANG)
                if ((pid, status) != (0, 0)):
                    break

                # get the value of some sysvars such as total cpu time,
                # memory...
                total_time = timeline.total_time()
                total_vsize = group.total_vsize()
                num_processes = timeline.total_processes ()
                num_threads = timeline.total_threads ()

                # and store them in the corresponding namespace
                BotTester._namespace.cputime = timeline.total_time ()
                BotTester._namespace.wctime = real_time
                BotTester._namespace.vsize = timeline.total_vsize ()
                BotTester._namespace.numprocs = timeline.total_processes ()
                BotTester._namespace.numthreads = timeline.total_threads ()

                # poll all sys tables
                for itable in self._dbspec.get_db ():
                    if itable.sysp ():
                        stats [itable.get_name ()] += itable.poll (BotTester._namespace,
                                                                   BotTester._data,
                                                                   BotTester._user,
                                                                   BotTester._param,
                                                                   BotTester._regexp,
                                                                   self._logger)

                # update the maximum memory usage
                max_mem = max (max_mem, total_vsize)

                # decide whether to kill the group or not
                try_term = (total_time > self._timeout or
                            real_time >= 1.5 * self._timeout or
                            max_mem > self._memory)
                try_kill = (total_time > self._timeout + self.kill_delay or
                            real_time >= 1.5 * self._timeout + self.kill_delay or
                            max_mem > self._memory)

                if try_term and not term_attempted:
                    self._logger.debug (""" aborting children with SIGTERM ...
     children found: %s""" % timeline.pids ())
                    timeline.terminate ()
                    term_attempted = True
                elif term_attempted and try_kill:
                    self._logger.debug (""" aborting children with SIGKILL ...
     children found: %s""" % timeline.pids ())
                    timeline.terminate ()


            # Execution has been completed!
            # -----------------------------------------------------------------
            # record the exit status of this process
            stats ['admin_status'].append ((itst.get_id (), status))

            # Even if we got here, there may be orphaned children or something we
            # may have missed due to a race condition. Check for that and kill
            # properly for good measure.
            self._logger.debug (""" [Sanity check] aborting children with SIGKILL for the last time ...
 [Sanity check] children found: %s""" % timeline.pids ())
            timeline.terminate ()

            # add the timeline of this execution to the stats
            stats ['admin_timeline'] += (map (lambda x,y:tuple (x+y),
                                              [[itst.get_id ()]]*len (timeline.get_processes ()),
                                              timeline.get_processes ()))

            # process the contents of the standard output
            self.process_results (os.getcwd (), output + ".log", stats)

            # once it has been processed move the .log and .err files to the results
            # directory
            for ilogfile in ['.log', '.err']:

                # compute the input filename
                ifilename = os.path.join (os.getcwd (), output + ilogfile)

                # first, if compression was explicitly requested, then proceed to
                # compress data
                if (self._compress):
                    self._logger.debug (" Compressing the contents of file '%s'" % ifilename)

                    _bz2 (ifilename, remove=True)

                    # and now move it to its target location with the suffix 'bz2'
                    shutil.move (ifilename + '.bz2',
                                 os.path.join (resultsdir, output + ilogfile + '.bz2'))


                # if compression was not requested
                else:

                    # just move the file to its target location
                    shutil.move (os.path.join (os.getcwd (), output + ilogfile),
                                 resultsdir)

            # close the log and error file descriptors
            os.close (fdlog)
            os.close (fderr)


    # -----------------------------------------------------------------------------
    # process_results
    #
    # it processes the standard output generated by the executable which is
    # saved in 'resultsfile' in the given 'directory' and updates the dictionary
    # 'stats' with the value of all variables found in the current database
    # specification (either appearing in the standard output file or the
    # contents of files).
    #
    # This is done by updating the 'data' and 'regexp' namespaces and then
    # invoking the 'poll' method in every data table
    # -----------------------------------------------------------------------------
    def process_results (self, directory, resultsfile, stats):
        """
        it processes the standard output generated by the executable which is
        saved in 'resultsfile' in the given 'directory' and updates the
        dictionary 'stats' with the value of all variables found in the current
        database specification (either appearing in the standard output file or
        the contents of files).

        This is done by updating the 'data' and 'regexp' namespaces and then
        invoking the 'poll' method in every data table
        """

        # populate the namespace with the information retrieved from the
        # resultsfile (i.e., from the standard output of the executable)
        with open (os.path.join (directory, resultsfile), 'r') as stream:

            # now, for each line in the output file
            for iline in stream.readlines ():

                # data namespace - default regexp
                # -------------------------------------------------------------
                # check whether this line matches the default regexp
                restat = re.match (BotTester.statregexp, iline)
                if (restat):

                    # add this variable to the data namespace
                    BotTester._data [restat.group ('varname').rstrip (" ")] = \
                      restat.group ('value')

                # regexp namespace
                # -------------------------------------------------------------
                # for every regexp defined by the user
                for iregexp in self._dbspec.get_regexp ():

                    # check whether this line matches it
                    m = re.match (iregexp.get_specification (), iline)
                    if (m):

                        # add this variable to the regexp namespace as a
                        # multi-key attribute with as many keys as groups there
                        # are in the regexp. The multi-attribute should be named
                        # to allow projections later on. The key names are the
                        # group names themselves
                        keys = tuple ([igroup for igroup in m.groupdict ()])
                        BotTester._regexp.setkeynames (iregexp.get_name (), *keys)

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
                        if iregexp.get_name () in BotTester._regexp:

                            currvalues = BotTester._regexp.getattr (iregexp.get_name (),
                                                                      key = dict (zip (keys, keys)))
                            BotTester._regexp.setattr (iregexp.get_name (),
                                                         key = dict (zip (keys, keys)),
                                                         value = currvalues + [tuple (values)])

                        # otherwise, initialize the contents of this multi-key
                        # attribute to a list which contains a single tuple with
                        # the values of this match
                        else:
                            BotTester._regexp.setattr (iregexp.get_name (),
                                                         key = dict (zip (keys, keys)),
                                                         value = [tuple (values)])

        # data namespace - filevars
        # -------------------------------------------------------------
        # also, populate the data namespace with the contents of files
        # (filevars) if requested by any database table
        for itable in [jtable for jtable in self._dbspec.get_db () if jtable.datap ()]:
            for icolumn in [jcolumn for jcolumn in itable if jcolumn.get_vartype () == 'FILEVAR']:
                with open (icolumn.get_variable (), 'r') as stream:
                    BotTester._data [icolumn.get_variable ()] = stream.read ()

        # now, compute the next row to write in all the data tables, if any with
        # information from the namespace
        for itable in self._dbspec.get_db ():
            if itable.datap ():
                stats [itable.get_name ()] += itable.poll (BotTester._namespace,
                                                           BotTester._data,
                                                           BotTester._user,
                                                           BotTester._param,
                                                           BotTester._regexp,
                                                           self._logger)


    # -----------------------------------------------------------------------------
    # wrapup
    #
    # wrapup performing the last operations
    # -----------------------------------------------------------------------------
    def wrapup (self, tstspec, dbspec, configdir):

        """
        wrapup performing the last operations
        """

        # copy the file with all the tests cases to the config dir. In case that
        # an instance already processed was directly given then use default
        # names for the tb and db files
        if isinstance (tstspec, tsttools.TstVerbatim):
            with open (os.path.join (configdir, 'tests.tb'), 'w') as tests:
                tests.write (tstspec.data)

        elif isinstance (tstspec, tsttools.TstFile):
            shutil.copy (tstspec.filename,
                         os.path.join (configdir, os.path.basename (tstspec.filename)))
        else:
            raise ValueError (" Incorrect tstspec in wrapup")

        # and also the file with the database specification to the config dir
        if isinstance (dbspec, dbtools.DBVerbatim):
            with open (os.path.join (configdir, 'database.db'), 'w') as database:
                database.write (dbspec.data)

        elif isinstance (dbspec, dbtools.DBFile):
            shutil.copy (dbspec.filename,
                         os.path.join (configdir, os.path.basename (dbspec.filename)))
        else:
            raise ValueError (" Incorrect dbspec in wrapup")


    # -----------------------------------------------------------------------------
    # create_admin_tables
    #
    # The execution of every solver (with all test cases) shall generate a
    # number of admin tables. These are created by hand in the following method
    # -----------------------------------------------------------------------------
    def create_admin_tables (self):
        """
        The execution of every solver (with all test cases) shall generate a
        number of admin tables. These are created by hand in the following method
        """

        self._dbspec += dbparser.DBTable ("admin_params",
                                          [dbparser.DBColumn ('solver', 'text', 'ADMINVAR',
                                                              'solver', 'None'),
                                           dbparser.DBColumn ('tests', 'text', 'ADMINVAR',
                                                              'tstfile', 'None'),
                                           dbparser.DBColumn ('db', 'text', 'ADMINVAR',
                                                              'dbfile', 'None'),
                                           dbparser.DBColumn ('delay', 'real', 'ADMINVAR',
                                                              'check', 'None'),
                                           dbparser.DBColumn ('time', 'integer', 'ADMINVAR',
                                                              'time', 'None'),
                                           dbparser.DBColumn ('memory', 'integer', 'ADMINVAR',
                                                              'memory', 'None')])
        self._dbspec += dbparser.DBTable ("admin_tests",
                                          [dbparser.DBColumn ('id', 'text', 'ADMINVAR',
                                                              'index', 'None'),
                                           dbparser.DBColumn ('args', 'text', 'ADMINVAR',
                                                              'args', 'None')])
        self._dbspec += dbparser.DBTable ("admin_time",
                                          [dbparser.DBColumn ('starttime', 'text', 'ADMINVAR',
                                                              'starttime', 'None'),
                                           dbparser.DBColumn ('endtime', 'text', 'ADMINVAR',
                                                              'endtime', 'None'),
                                           dbparser.DBColumn ('elapsedseconds', 'real', 'ADMINVAR',
                                                              'elapsed', 'None')])
        self._dbspec += dbparser.DBTable ("admin_timeline",
                                          [dbparser.DBColumn ('id', 'integer', 'ADMINVAR',
                                                              'index', 'None'),
                                           dbparser.DBColumn ('pid', 'integer', 'ADMINVAR',
                                                              'pid', 'None'),
                                           dbparser.DBColumn ('cmdline', 'text', 'ADMINVAR',
                                                              'cmdline', 'None'),
                                           dbparser.DBColumn ('starttime', 'text', 'ADMINVAR',
                                                              'starttime', 'None'),
                                           dbparser.DBColumn ('endtime', 'text', 'ADMINVAR',
                                                              'endtime', 'None'),
                                           dbparser.DBColumn ('elapsedseconds', 'real', 'ADMINVAR',
                                                              'elapsedseconds', 'None')])
        self._dbspec += dbparser.DBTable ("admin_version",
                                          [dbparser.DBColumn ('program', 'text', 'ADMINVAR',
                                                              'program', 'None'),
                                           dbparser.DBColumn ('version', 'text', 'ADMINVAR',
                                                              'version', 'None'),
                                           dbparser.DBColumn ('revision', 'text', 'ADMINVAR',
                                                              'revision', 'None'),
                                           dbparser.DBColumn ('date', 'text', 'ADMINVAR',
                                                              'revdate', 'None')])
        self._dbspec += dbparser.DBTable ("admin_status",
                                          [dbparser.DBColumn ('id', 'text', 'ADMINVAR',
                                                              'index', 'None'),
                                           dbparser.DBColumn ('status', 'integer', 'ADMINVAR',
                                                              'status', 'None')])


    # -----------------------------------------------------------------------------
    # insert_data
    #
    # creates the table qualified by the instance of DBTable 'dbtable' in the given
    # databasename and writes the specified 'data' into it
    # -----------------------------------------------------------------------------
    def insert_data (self, databasename, dbtable, data):

        """
        creates the table qualified by the instance of DBTable 'dbtable' in the
        given databasename and writes the specified 'data' into it
        """

        # compute the filename
        dbfilename = databasename + '.db'
        self._logger.debug (" Populating '%s' in '%s'" % (dbtable.get_name (), dbfilename))

        # connect to the sql database
        db = sqltools.dbaccess (dbfilename)

        # create the table
        db.create_table (dbtable)

        # and write data
        db.insert_data (dbtable, data)

        # close and exit
        db.close ()


    # -----------------------------------------------------------------------------
    # go
    #
    # main service provided by this class. It automates the whole execution
    # according to the given parameters. Solver is either a list of strings that
    # contain paths to a number of solvers that are applied in succession or
    # just a single solver (given also as a string) each one creating a
    # different database according to the specification in dbfile. All
    # executions refer to the same test cases defined in tstfile and are
    # allotted the same computational resources (timeout and memory). To ease
    # integration with other software, both the db and the tests specification
    # file can be given in various formats: as a string (been interpreted as a
    # path to the file to parse); as a verbatim specification (which is an
    # instance of TstVerbatim/DBVerbatim) or as a file already parsed
    # (TstFile/DBFile).
    #
    # The argnamespace is the Namespace of the parser used (which should be an
    # instance of argparse or None). Other (optional) parameters are:
    #
    # output - prefix of the output files that capture the standard out and
    #          error
    # check - time (in seconds) between successive pings to the executable
    # directory - target directory where all output is recorded
    # compress - if true, the files containing the standard output and error are
    #            compressed with bzip2
    # logger - if a logger is given, autobot uses a child of it. Otherwise, it
    #          creates its own logger
    # logfilter - if the client code uses a logger that requires additional
    #             information, a logging.Filter should be given here
    # prologue - if a class is provided here then __call__ () is automatically
    #            invoked before every execution of the solver with every test
    #            case. This class should be a subclass of BotAction so that it
    #            automatically inherits the following attributes: solver,
    #            tstspec, itest, dbspec, timeout, memory, output, check,
    #            resultsdir, compress, namespace
    # epilogue - if a class is provided here then __call__ () is automatically
    #            invoked after every execution of the solver with every test
    #            case. This class should be a subclass of BotAction so that it
    #            automatically inherits the same attributes described in
    #            prologue
    # enter - much like prologue but __call__ is automatically invoked before
    #         the execution of the solver over the first test case
    # windUp - much like epilogue but __call__ is automatically invoked after
    #          the execution of the current solver with the last test instance
    # quiet - if given, some additional information is skipped
    # -----------------------------------------------------------------------------
    def go (self, solver, tstfile, dbfile, timeout, memory, argnamespace=None,
            output='$index', check=5, directory=os.getcwd (), compress=False,
            logger=None, logfilter=None, prologue=None, epilogue=None,
            enter=None, windUp=None, quiet=False):
        """
        main service provided by this class. It automates the whole execution
        according to the given parameters. Solver is either a list of strings
        that contain paths to a number of solvers that are applied in succession
        or just a single solver (given also as a string) each one creating a
        different database according to the specification in dbfile. All
        executions refer to the same test cases defined in tstfile and are
        allotted the same computational resources (timeout and memory). To ease
        integration with other software, both the db and the tests specification
        file can be given in various formats: as a string (been interpreted as a
        path to the file to parse); as a verbatim specification (which is an
        instance of TstVerbatim/DBVerbatim) or as a file already parsed
        (TstFile/DBFile).

        The argnamespace is the Namespace of the parser used (which should be an
        instance of argparse or None). Other (optional) parameters are:

        output - prefix of the output files that capture the standard out and
                 error
        check - time (in seconds) between successive pings to the executable
        directory - target directory where all output is recorded
        compress - if true, the files containing the standard output and error are
                   compressed with bzip2
        logger - if a logger is given, autobot uses a child of it. Otherwise, it
                 creates its own logger
        logfilter - if the client code uses a logger that requires additional
                    information, a logging.Filter should be given here
        prologue - if a class is provided here then __call__ () is automatically
                   invoked before every execution of the solver with every test
                   case. This class should be a subclass of BotAction so that it
                   automatically inherits the following attributes: solver,
                   tstspec, itest, dbspec, timeout, memory, output, check,
                   resultsdir, compress, namespace
        epilogue - if a class is provided here then __call__ () is automatically
                   invoked after every execution of the solver with every test
                   case. This class should be a subclass of BotAction so that it
                   automatically inherits the same attributes described in
                   prologue
        enter - much like prologue but __call__ is automatically invoked before
                the execution of the solver over the first test case
        windUp - much like epilogue but __call__ is automatically invoked after
                 the execution of the current solver with the last test instance
        quiet - if given, some additional information is skipped
        """

        # copy the attributes
        (self._solver, self._tstfile, self._dbfile, self._timeout, self._memory,
         self._argnamespace, self._output, self._check, self._directory, self._compress,
         self._prologue, self._epilogue, self._quiet) = \
         (solver, tstfile, dbfile, timeout, memory,
          argnamespace, output, check, directory, compress,
          prologue, epilogue, quiet)

        # logger settings - if a logger has been passed, just create a child of
        # it
        if logger:
            self._logger = logger.getChild ('bots.BotTester')

            # in case a filter has been given add it and finally set the log level
            if logfilter:
                self._logger.addFilter (logfilter)

        # otherwise, create a simple logger based on a stream handler
        else:
            self._logger = logging.getLogger(self.__class__.__module__ + '.' +
                                             self.__class__.__name__)
            handler = logging.StreamHandler ()
            handler.setLevel (BotTester._loglevel)
            handler.setFormatter (logging.Formatter (" %(levelname)-10s:   %(message)s"))
            self._logger.addHandler (handler)

            # not passing a logger does not mean that other loggers do not exist
            # so that make sure that the log messages generated here are not
            # propagated upwards in the logging hierarchy
            self._logger.propagate = False

        self._logger.debug(" Starting automated execution ...")

        # make the specification of solvers to be a list of solvers even if just
        # a single solver was given
        if type (self._solver) is str:
            self._solver = [self._solver]
        if type (self._solver) is not list:
            raise ValueError (" Incorrect specification of solvers")

        # check that all parameters are valid
        self.check_flags (self._solver, self._tstfile, self._dbfile,
                          timeout, memory, check, directory)

        # and now, create the test case and database specifications

        # process the test cases either as a string with a path to the file to
        # parse or just simply copy the specification in case it was given as a
        # verbatim string or as a file already parsed
        if type (self._tstfile) is str:
            self._logger.debug (" Parsing the tests specification file ...")
            self._tstspec = tsttools.TstFile (self._tstfile)
        elif isinstance (self._tstfile, tsttools.TstVerbatim):
            self._logger.debug (" The test cases were given as a verbatim specification")
            self._tstspec = self._tstfile
            self._tstfile = BotTester.defaultname
        elif isinstance (self._tstfile, tsttools.TstFile):
            self._logger.debug (" The test cases were given as a file already parsed")
            self._tstspec = self._tstfile
            self._tstfile = self._tstfile.filename
        else:
            raise ValueError (" Incorrect specification of the test cases")

        # proceed similarly in case of the database specification file
        if type (self._dbfile) is str:
            self._logger.debug (" Parsing the database specification file ...")
            self._dbspec  = dbtools.DBFile (self._dbfile)
        elif isinstance (self._dbfile, dbtools.DBVerbatim):
            self._logger.debug (" The database was given as a verbatim specification")
            self._dbspec = self._dbfile
            self._dbfile = BotTester.defaultname
        elif isinstance (self._dbfile, dbtools.DBFile):
            self._logger.debug (" The database was given as a file already parsed")
            self._dbspec = self._dbfile
            self._dbfile = self._dbfile.filename
        else:
            raise ValueError (" Incorrect specification of the database")

        # and now, unless quiet is enabled, show the flags
        if (not self._quiet):

            self.show_switches (solver, self._tstfile, self._dbfile, timeout, memory,
                                check, directory, compress)

        # is the user overriding the definition of the data regexp?
        for iregexp in self._dbspec.get_regexp ():

            # if so, override the current definition and show an info message
            if iregexp.get_name () == 'default':
                self.statregexp = iregexp.get_specification ()
                self._logger.warning (" The data regexp has been overridden to '%s'" % iregexp.get_specification ())

        # at last, run the experiments going through every solver
        if not solver:
            self._logger.warning (" No solver was given")

        for isolver in self._solver:

            # create an empty dictionary of stats
            istats = defaultdict (list)

            solvername = os.path.basename (isolver)

            self._logger.info (" Starting experiments with solver '%s'" % solvername)

            # setup the necessary environment and retrieve the directories to be
            # used in the experimentation
            (resultsdir, configdir, logdir) = self.setup (solvername, self._directory)

            # write all the log information in the logdir
            self.fetch (logdir)

            # in case it is requested to execute an *enter* action do it now
            if enter:
                action = enter (solver=isolver,
                                tstspec=self._tstspec,
                                dbspec=self._dbspec,
                                timeout=self._timeout,
                                memory=self._memory,
                                check=self._check,
                                basedir=self._directory,
                                resultsdir=resultsdir,
                                compress=self._compress,
                                namespace=BotTester._namespace,
                                user=BotTester._user,
                                stats=istats)
                action (self._logger)

            # record the start time
            self._starttime = datetime.datetime.now ()

            # now, invoke the execution of all tests with this solver
            self.run_all_cases (isolver, resultsdir, istats)

            # record the end time of this solver
            self._endtime = datetime.datetime.now ()

            # and wrapup
            self.wrapup (self._tstspec, self._dbspec, configdir)

            # finally, write down all the information to a sqlite3 db
            databasename = os.path.join (self._directory, solvername, solvername)
            self._logger.info (" Writing data into '%s.db'" % databasename)

            # admin tables are not populated using the poll method in every
            # dbtable. Instead, their contents are inserted manually in either
            # "run" or here
            istats ['admin_params'] = [(isolver, self._tstfile, self._dbfile, self._check, self._timeout, self._memory)]
            istats ['admin_tests'] = self._tstspec.get_defs ()
            istats ['admin_time'] = [(self._starttime, self._endtime,
                                      (self._endtime - self._starttime).total_seconds ())]
            istats ['admin_version'] = [('autobot', __version__, __revision__[1:-1], __date__ [1:-1])]

            # now, create the admin tables and populate all data tables
            self.create_admin_tables ()
            for itable in self._dbspec.get_db ():
                self.insert_data (databasename, itable, istats[itable.get_name ()])

            # similarly to *enter*, in case a *windUp* action is given, execute
            # it now before moving to the next solver
            if windUp:
                action = windUp (solver=isolver,
                                 tstspec=self._tstspec,
                                 dbspec=self._dbspec,
                                 timeout=self._timeout,
                                 memory=self._memory,
                                 check=self._check,
                                 basedir=self._directory,
                                 resultsdir=resultsdir,
                                 compress=self._compress,
                                 namespace=BotTester._namespace,
                                 data=BotTester._data,
                                 user=BotTester._user,
                                 regexp=BotTester._regexp,
                                 stats=istats)
                action (self._logger)

        self._logger.debug (" Exiting from the automated execution ...")



# Local Variables:
# mode:python
# fill-column:79
# End:
