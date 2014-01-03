#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# autobot.py
# Description: General framework for starting services from the testbot
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 11 21:27:32 2013 Carlos Linares Lopez>
# Last update <viernes, 03 enero 2014 02:15:11 Carlos Linares Lopez (clinares)>
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
General framework for starting services from the testbot
"""

__version__  = '2.0'
__revision__ = '$Revision$'
__date__     = '$Date:$'


# imports
# -----------------------------------------------------------------------------
import bz2                      # bzip2 compression service
import datetime                 # date/time
import getpass                  # getuser
import importlib                # importing modules
import inspect                  # inspect live objects
import logging                  # loggers
import os                       # os services
import re                       # regular expressions
import shutil                   # shell utitilies such as copying files
import socket                   # gethostname
import subprocess               # subprocess management
import time                     # time management

from collections import defaultdict

import dbparser                 # parsing of database specification files
import dbtools                  # database specification files
import sqltools                 # sqlite3 database access
import systools                 # process management
import timetools                # timing management
import tsttools                 # test specification files


# -----------------------------------------------------------------------------
# BotAction
#
# It is feasible to invoke a prologue and an epilogue before and after every
# invocation of the executable in the BotTestCase. To enable further flexibility
# these actions are implemented as subclasses of BotAction which have to
# implement __call__. If these functions are provided then the corresponding
# subclass is invoked with all the variables that define the current environment
# of the execution: solver, tstspec, itest, dbspec, time, memory, output (with
# its placeholders substituted), check, resultsdir, compress and placeholders
# -----------------------------------------------------------------------------
class BotAction (object):
    """
    It is feasible to invoke a prologue and an epilogue before and after every
    invocation of the executable in the BotTestCase. To enable further
    flexibility these actions are implemented as subclasses of BotAction which
    have to implement __call__. If these functions are provided then the
    corresponding subclass is invoked with all the variables that define the
    current environment of the execution: solver, tstspec, itest, dbspec, time,
    memory, output (with its placeholders substituted), check, resultsdir,
    compress and placeholders
    """

    def __init__ (self, solver, tstspec, itest, dbspec, time, memory, output,
                  check, resultsdir, compress, placeholders):
        """
        stores the values of all variables that define the current environment
        """

        # copy the attributes
        (self.solver, self.tstspec, self.itest, self.dbspec, self.time,
         self.memory, self.output, self.check, self.resultsdir,
         self.compress, self.placeholders) = \
        (solver, tstspec, itest, dbspec, time,
         memory, output, check, resultsdir,
         compress, placeholders)


    def __call__(self, itest):
        raise NotImplementedError ('__call__() not defined')



# -----------------------------------------------------------------------------
# BotTestCase
#
# Base class of all testbots. This class is equipped with an argument
# parser that can be reused/extended and it also provides various
# logging services
# -----------------------------------------------------------------------------
class BotTestCase (object):
    """
    Base class of all testbots. This class is equipped with an
    argument parser that can be reused/extended and it also provides
    various logging services
    """

    # how long to wait between SIGTERM and SIGKILL
    # -----------------------------------------------------------------------------
    kill_delay = 5

    # regular epression for recognizing pairs (var, val) in the stdout
    # -----------------------------------------------------------------------------
    statregexp = " >[\t ]*(?P<varname>[a-zA-Z ]+):[ ]+(?P<value>([0-9]+\.[0-9]+|[0-9]+))"

    # logging services
    # -----------------------------------------------------------------------------
    _loglevel = logging.INFO            # default logging level


    # -----------------------------------------------------------------------------
    # check_flags
    #
    # check the parameters given to the automated execution of this instance
    # -----------------------------------------------------------------------------
    def check_flags (self, solver, tstfile, dbfile, time, memory, check, directory):

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
    """ % (isolver))
                raise ValueError

        # verify also that the test cases are accessible as well
        if (tstfile and (not os.access (tstfile, os.F_OK) or
                          not os.access (os.path.dirname (tstfile), os.R_OK))):
            self._logger.critical ("""
     The test cases specification file does not exist or it resides in an unreachable location
     Use '--help' for more information
    """)
            raise ValueError

        # and also the database specification
        if (dbfile and (not os.access (dbfile, os.F_OK) or
                        not os.access (os.path.dirname (dbfile), os.R_OK))):
            self._logger.critical ("""
     The database specification file does not exist or it resides in an unreachable location
     Use '--help' for more information
    """)
            raise ValueError

        # verify that check is not negative
        if (check < 0):
            self._logger.critical (" The check flag should be non negative")
            raise ValueError

        # finally, verify the time and memory bounds
        if (time <= 0):
            self._logger.critical (" The time param shall be positive!")
            raise ValueError

        if (memory <= 0):
            self._logger.critical (" The memory param shall be positive!")
            raise ValueError


    # -----------------------------------------------------------------------------
    # show_switches
    #
    # show a somehow beautified view of the current params
    # -----------------------------------------------------------------------------
    def show_switches (self, solver, tstfile, dbfile, time, memory, check, directory, compress):

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

  * Check flag           : %i seconds

  * Directory            : %s
  * Compression          : %s
  * Time limit           : %i seconds
  * Memory bound         : %i bytes
 -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-2], __version__, solvernames, tstfile, dbfile, check, directory, {False: 'disabled', True: 'enabled'}[compress], time, memory))


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
    # test
    #
    # invokes the execution of the given solver *in the same directory where it
    # resides* for solving all cases specified in 'tstspec' using the allotted
    # time and memory. The results are stored in 'resultsdir'; the solver is
    # sampled every 'check' seconds and different stats are stored in
    # 'stats'. Output files are named after 'output' and variable substitutions
    # specified in mainplaceholders are allwoed. 'dbspec' contains the database
    # specification used to store different data. If a prologue/epilogue is
    # given (they should be a subclass of BotAction ) then its __call__ method
    # is invoked before/after the execution of the solver with regard to every
    # test case
    # -----------------------------------------------------------------------------
    def test (self, solver, tstspec, dbspec, time, memory, output, check,
              resultsdir, compress, mainplaceholders, stats, prologue, epilogue):
        """
        invokes the execution of the given solver *in the same directory where
        it resides* for solving all cases specified in 'tstspec' using the
        allotted time and memory. The results are stored in 'resultsdir'; the
        solver is sampled every 'check' seconds and different stats are stored
        in 'stats'. Output files are named after 'output' and variable
        substitutions specified in mainplaceholders are allwoed. 'dbspec'
        contains the database specification used to store different data. If a
        prologue/epilogue is given (they should be a subclass of BotAction )
        then its __call__ method is invoked before/after the execution of the
        solver with regard to every test case
        """

        def _sub (string, D):
            """
            substitute in string the ocurrence of every keyword in D with its value
            if it appears preceded by '$' in string. Similar to Template.substitute
            but it also allows the substitution of strings which do not follow the
            convention of python variable names
            """

            result = string                                 # initialization
            for (ire, isub) in D.items ():                  # for all keys
                result = re.sub ('\$'+ire, isub, result)    # substitute
            return result                                   # and return


        # now, for each test case
        for itst in tstspec:

            # initialize the dictionary with the value of the placeholders
            placeholders = {'index'   : itst.get_id (),
                            'name'    : os.path.basename (solver),
                            'date'    : datetime.datetime.now ().strftime ("%Y-%m-%d"),
                            'time'    : datetime.datetime.now ().strftime ("%H:%M:%S")}

            # and now, add the values of all the directives in this testcase and
            # all the arguments given to the main script
            placeholders.update (itst.get_values ())
            placeholders.update (mainplaceholders)

            # and also with the position of every argument (so that $1 can be
            # interpreted as the first parameter, $2 as the second, and so on)
            # ---note that these numerical indices are casted to strings for the
            # convenience of other functions
            placeholders.update (dict (zip([str(i) for i in range(0,len(itst.get_args ()))],
                                           itst.get_args ())))

            # compute the right name of the output file using the placeholders
            # if any was given there
            outputprefix = _sub (output, placeholders)

            # if a prologue was given, execute it now
            if prologue:
                action = prologue (solver, tstspec, itst, dbspec, time,
                                   memory, outputprefix, check, resultsdir,
                                   compress, placeholders)
                action (self._logger)

            # invoke the execution of this test case
            self._logger.info ('\t%s' % itst)
            self.run (os.path.abspath (solver), resultsdir,
                      itst.get_id (), itst.get_args (), dbspec,
                      outputprefix, placeholders,
                      stats, check, time, memory, compress)

            # finally, if an epilogue was given, execute it now
            if epilogue:
                action = epilogue (solver, tstspec, itst, dbspec, time,
                                   memory, outputprefix, check, resultsdir,
                                   compress, placeholders)
                action (self._logger)


    # -----------------------------------------------------------------------------
    # process_results
    #
    # it processes the given resultsfile (which is expected to have the standard
    # output of the process) which resides at the given directory and updates
    # the dictionary stats with the value of all variables found in all the data
    # tables in dbspec (either appearing in the standard output file or the
    # contents of files). This is done by updating the placeholders and then
    # invoking the 'poll' method in every data table
    # -----------------------------------------------------------------------------
    def process_results (self, directory, resultsfile, dbspec, placeholders, stats):
        """
        it processes the given resultsfile (which is expected to have the
        standard output of the process) which resides at the given directory and
        updates the dictionary stats with the value of all variables found in
        all the data tables in dbspec (either appearing in the standard output
        file or the contents of files). This is done by updating the
        placeholders and then invoking the 'poll' method in every data table
        """

        # populate the placeholders with the information retrieved from the
        # resultsfile (i.e., from the standard output of the executable)
        with open (os.path.join (directory, resultsfile), 'r') as stream:

            # now, for each line in the output file
            for iline in stream.readlines ():

                # check whether this line contains a stat
                restat = re.match (self.statregexp, iline)

                if (restat):

                    # add this variable to the dictionary
                    placeholders [restat.group ('varname').rstrip (" ")] = restat.group ('value')

        # also, populate the placeholders with the contents of files if requested by
        # any database table
        for itable in [jtable for jtable in dbspec if jtable.datap ()]:
            for icolumn in [jcolumn for jcolumn in itable if jcolumn.get_vartype () == 'FILEVAR']:
                with open (icolumn.get_variable (), 'r') as stream:
                    placeholders [icolumn.get_variable ()] = stream.read ()

        # now, compute the next row to write in all the data tables, if any
        for itable in dbspec:
            if itable.datap ():
                stats [itable.get_name ()].append (itable.poll (placeholders))


    # -----------------------------------------------------------------------------
    # run
    #
    # executes the specified 'solver' *in the same directory where it resides*
    # (this is fairly convenient in case the solver needs additional input files
    # which are then extracted from a directory relative to the current
    # location) for solving the particular test case (qualified by index). It
    # copies the stdout and stderr of the solver in files named after output
    # (plus either .log or .err) which are then moved to the specified results
    # directory. The forked process is pinged every 'check' seconds and it is
    # launched with computational resources 'timeout' and 'memory'. 'dbspec'
    # contains the database specification used to store sys and data information
    # where placeholders specify the variable substitutions to be performed
    # -----------------------------------------------------------------------------
    def run (self, solver, resultsdir, index, spec, dbspec, output, placeholders, stats,
             check, timeout, memory, compress):

        """
        executes the specified 'solver' *in the same directory where it resides*
        (this is fairly convenient in case the solver needs additional input
        files which are then extracted from a directory relative to the current
        location) for solving the particular test case (qualified by index). It
        copies the stdout and stderr of the solver in files named after output
        (plus either .log or .err) which are then moved to the specified results
        directory. The forked process is pinged every 'check' seconds and it is
        launched with computational resources 'timeout' and 'memory'. 'dbspec'
        contains the database specification used to store sys and data
        information where placeholders specify the variable substitutions to be
        performed
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
            try:
                child = subprocess.Popen ([solver] + spec,
                                          stdout = fdlog,
                                          stderr = fderr,
                                          cwd=os.path.dirname (solver))
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

                time.sleep(check)

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

                # get some stats such as total cpu time, memory, ...
                total_time = timeline.total_time()
                total_vsize = timeline.total_vsize()
                num_processes = timeline.total_processes ()
                num_threads = timeline.total_threads ()

                placeholders ['cputime'] = timeline.total_time ()
                placeholders ['wctime'] = real_time
                placeholders ['vsize'] = timeline.total_vsize ()
                placeholders ['numprocs'] = timeline.total_processes ()
                placeholders ['numthreads'] = timeline.total_threads ()

                # poll all sys tables
                for itable in dbspec:
                    if itable.sysp ():
                        stats [itable.get_name ()].append (itable.poll (placeholders))

                # update the maximum memory usage
                max_mem = max (max_mem, total_vsize)

                # decide whether to kill the group or not
                try_term = (total_time > timeout or
                            real_time >= 1.5 * timeout or
                            max_mem > memory)
                try_kill = (total_time > timeout + self.kill_delay or
                            real_time >= 1.5 * timeout + self.kill_delay or
                            max_mem > memory)

                if try_term and not term_attempted:
                    self._logger.debug (""" aborting children with SIGTERM ...
     children found: %s""" % timeline.pids ())
                    timeline.terminate ()
                    term_attempted = True
                elif term_attempted and try_kill:
                    self._logger.debug (""" aborting children with SIGKILL ...
     children found: %s""" % timeline.pids ())
                    timeline.terminate ()

            # record the exit status of this process
            stats ['admin_status'].append ((index, status))

            # Even if we got here, there may be orphaned children or something we
            # may have missed due to a race condition. Check for that and kill
            # properly for good measure.
            self._logger.debug (""" [Sanity check] aborting children with SIGKILL for the last time ...
 [Sanity check] children found: %s""" % timeline.pids ())
            timeline.terminate ()

            # add the timeline of this execution to the stats
            stats ['admin_timeline'] += (map (lambda x,y:tuple (x+y),
                                              [[index]]*len (timeline.get_processes ()),
                                              timeline.get_processes ()))

            # process the contents of the standard output
            self.process_results (os.getcwd (), output + ".log", dbspec, placeholders, stats)

            # once it has been processed move the .log and .err files to the results
            # directory
            for ilogfile in ['.log', '.err']:

                # compute the input filename
                ifilename = os.path.join (os.getcwd (), output + ilogfile)

                # first, if compression was explicitly requested, then proceed to
                # compress data
                if (compress):
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
    # wrapup
    #
    # wrapup all the execution performing the last operations
    # -----------------------------------------------------------------------------
    def wrapup (self, tstfile, dbfile, configdir):

        """
        wrapup all the execution performing the last operations
        """

        # copy the file with all the tests cases to the config dir
        shutil.copy (tstfile,
                     os.path.join (configdir, os.path.basename (tstfile)))

        # and also the file with the database specification to the config dir
        shutil.copy (dbfile,
                     os.path.join (configdir, os.path.basename (dbfile)))


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
                                           dbparser.DBColumn ('delay', 'integer', 'ADMINVAR',
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
        db = sqltools.dbtest (dbfilename)

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
    # according to the given parameters. Solver is a list of solvers that are
    # applied in succession each one creating a different database according to
    # the specification in dbfile. All executions refer to the same test cases
    # defined in tstfile and are allotted the same computational resources (time
    # and memory). The argnamespace is the Namespace of the parser used (which
    # should be an instance of argparse or None). Other (optional) parameters
    # are:
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
    #            tstspec, itest, dbspec, time, memory, output, check,
    #            resultsdir, compress, placeholders
    # epilogue - if a class is provided here then __call__ () is automatically
    #            invoked after every execution of the solver with every test
    #            case. This class should be a subclass of BotAction so that it
    #            automatically inherits the same attributes described in
    #            prologue
    # quiet - if given, some additional information is skipped
    # -----------------------------------------------------------------------------
    def go (self, solver, tstfile, dbfile, time, memory, argnamespace=None,
            output='$index', check=5, directory=os.getcwd (), compress=False,
            logger=None, logfilter=None, prologue=None, epilogue=None,
            quiet=False):
        """
        main service provided by this class. It automates the whole execution
        according to the given parameters. Solver is a list of solvers that are
        applied in succession each one creating a different database according to
        the specification in dbfile. All executions refer to the same test cases
        defined in tstfile and are allotted the same computational resources (time
        and memory). The argnamespace is the Namespace of the parser used (which
        should be an instance of argparse or None). Other (optional) parameters
        are:
        
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
                   tstspec, itest, dbspec, time, memory, output, check,
                   resultsdir, compress, placeholders
        epilogue - if a class is provided here then __call__ () is automatically
                   invoked after every execution of the solver with every test
                   case. This class should be a subclass of BotAction so that it
                   automatically inherits the same attributes described in
                   prologue
        quiet - if given, some additional information is skipped
        """

        # copy the attributes
        (self._solver, self._tstfile, self._dbfile, self._time, self._memory,
         self._output, self._check, self._directory, self._compress,
         self._quiet) = \
         (solver, tstfile, dbfile, time, memory,
          output, check, directory, compress,
          quiet)

        # logger settings - if a logger has been passed, just create a child of
        # it
        if logger:
            self._logger = logger.getChild ('autobot.BotTestCase')

            # in case a filter has been given add it and finally set the log level
            if logfilter:
                self._logger.addFilter (logfilter)

        # otherwise, create a simple logger based on a stream handler
        else:
            self._logger = logging.getLogger(self.__class__.__module__ + '.' +
                                             self.__class__.__name__)
            handler = logging.StreamHandler ()
            handler.setLevel (BotTestCase._loglevel)
            handler.setFormatter (logging.Formatter (" %(levelname)-10s:   %(message)s"))
            self._logger.addHandler (handler)

            # not passing a logger does not mean that other loggers do not exist
            # so that make sure that the log messages generated here are not
            # propagated upwards in the logging hierarchy
            self._logger.propagate = False

        self._logger.debug (" Starting automated execution ...")

        # check that all parameters are valid
        self.check_flags (solver, tstfile, dbfile, time,
                          memory, check, directory)

        # and now, unless quiet is enabled, show the flags
        if (not self._quiet):

            self.show_switches (solver, tstfile, dbfile, time, memory, check,
                                directory, compress)

        # and now, create the test case and database specifications from their
        # filenames
        self._logger.debug (" Parsing the tests specification file ...")
        self._tstspec = tsttools.TstFile (self._tstfile)

        self._logger.debug (" Parsing the database specification file ...")
        self._dbspec  = dbtools.DBFile (self._dbfile)

        # at last, run the experiments going through every solver
        for isolver in self._solver:

            # create an empty dictionary of stats
            istats = defaultdict (list)

            solvername = os.path.basename (isolver)

            self._logger.info (" Starting experiments with solver '%s'" % solvername)

            # initialize the placeholders with the parameters passed to the main
            # script. These are given in argnamespace. Since the argparser
            # automatically casts type according to their type field, they are
            # all converted into strings here to allow a uniform treatment
            placeholders = {}
            if argnamespace:
                for index, value in argnamespace.__dict__.items ():
                    placeholders [index] = str (value)

            # setup the necessary environment and retrieve the directories to be
            # used in the experimentation
            (resultsdir, configdir, logdir) = self.setup (solvername, self._directory)

            # write all the log information in the logdir
            self.fetch (logdir)

            # record the start time
            self._starttime = datetime.datetime.now ()

            # now, invoke the execution of all tests with this solver
            self.test (isolver, self._tstspec, self._dbspec, self._time, self._memory,
                       self._output, self._check, resultsdir, self._compress,
                       placeholders, istats, prologue, epilogue)

            # record the end time of this solver
            self._endtime = datetime.datetime.now ()

            # and wrapup
            self.wrapup (self._tstfile, self._dbfile, configdir)

            # finally, write down all the information to a sqlite3 db
            databasename = os.path.join (self._directory, solvername, solvername)
            self._logger.info (" Writing data into '%s.db'" % databasename)

            # admin tables are not populated using the poll method in every
            # dbtable. Instead, their contents are inserted manually in either
            # "run" or here
            istats ['admin_params'] = [(isolver, self._tstfile, self._dbfile, self._check, self._time, self._memory)]
            istats ['admin_tests'] = self._tstspec.get_defs ()
            istats ['admin_time'] = [(self._starttime, self._endtime,
                                      (self._endtime - self._starttime).total_seconds ())]
            istats ['admin_version'] = [('autobot', __version__, __revision__[1:-1], __date__ [1:-1])]

            # now, create and populate all the admin datatables
            self.create_admin_tables ()
            for itable in self._dbspec:
                if not itable.datap () and not itable.sysp ():
                    self.insert_data (databasename, itable, istats[itable.get_name ()])

            # user data and sys data
            for itable in self._dbspec:
                if itable.datap () or itable.sysp ():
                    self.insert_data (databasename, itable, istats[itable.get_name ()])

        self._logger.debug (" Exiting from the automated execution ...")


# -----------------------------------------------------------------------------
# BotLoader
#
# This class is responsible of processing all classes in the given
# module and to return all of those that are children of BotTestCase
# along with the methods that should be executed
# -----------------------------------------------------------------------------
class BotLoader:
    """
    This class is responsible of processing all classes in the given
    module and to return all of those that are children of BotTestCase
    along with the methods that should be executed
    """

    _botTestre = 'test_'

    def loadTestsFromModule (self, module):
        """
        Browse all the definitions in the given module and process those classes
        that are descendants of BotTestCase. 'module' is the module object
        properly imported. It returns a tuple with a couple of dictionaries. The
        first one provides the definition of all classes that contain methods to
        execute. The second one contains the (unbound) methods that have to be
        executed within every class
        """

        # initialization
        classDict = {}
        methodsDict = defaultdict (list)

        # Retrieve all classes defined in the given module. getmembers
        # return tuples of the form (name, value) so that all values
        # are processed to preserve only those that are inherited from
        # BotTestCase
        self._classes = filter (lambda x:issubclass (x[1], BotTestCase),
                                inspect.getmembers (module,
                                                    lambda x:inspect.isclass (x)))

        # process every class looking for methods matching botTestre and create
        # a dictionary which stores the methods to execute (value) of every
        # class (key)
        for classname, classdef in self._classes:

            # get its members
            for member, methoddef in inspect.getmembers (classdef):

                if (re.match (self._botTestre, member)):
                    classDict [classname] = classdef
                    methodsDict [classname].append (methoddef)

        # and return both dictionaries
        return (classDict, methodsDict)


# -----------------------------------------------------------------------------
# BotMain
#
# This class provides the main definitions for accessing the services
# provided by testbot
# -----------------------------------------------------------------------------
class BotMain:
    """
    This class provides the main definitions for accessing the
    services provided by the testbot
    """

    def __init__ (self, module='__main__', cmp=None):
        """
        Process the parameters of this session retrieving the test functions to
        execute. Test functions are sorted according to cmp. If it equals None
        then they are sorted in ascending order of the lexicographical order
        """

        def _cmp (methodA, methodB):
            """
            Returns -1, 0 or +1 if depending on whether the first argument is
            smaller, equal or larger than the second argument. 'methodA' and
            'methodB' are method implementations so that their names are accessed
            through __name__
            """

            if methodA.__name__ < methodB.__name__: return -1
            elif methodA.__name__ > methodB.__name__:   return +1
            return 0


        # retrieve the module to process
        self._module = importlib.import_module (module)

        # get all the test cases to execute --- classes is a dictionary of names
        # to defs and methods is another dictionary of class names to method
        # implementations
        (self._classes, self._methods) = BotLoader ().loadTestsFromModule (self._module)

        # and execute all methods
        for classname, methodList in self._methods.items ():

            # create an instance of this class so that methods will be
            # bounded
            instance = self._classes [classname] ()

            # first, execute the setUp method if any was defined
            setUp = getattr (self._classes [classname], 'setUp', False)
            if setUp:
                instance.setUp ()

            # sort the methods in ascending order according to cmp. If no
            # comparison is function is given then sort them lexicographically
            # in ascending order
            if (not cmp):
                cmp = _cmp
            methodList = sorted (methodList, cmp=lambda x,y: cmp (x, y))

            # now execute all methods in this class
            for method in methodList:

                # we go through the descriptors of our instance to bind the
                # method to our instance and then to execute it
                method.__get__ (instance, self._classes [classname]) ()

            # tearing down, if given
            tearDown = getattr (self._classes [classname], 'tearDown', False)
            if tearDown:
                instance.tearDown ()



# Local Variables:
# mode:python
# fill-column:80
# End:
