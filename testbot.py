#!/usr/bin/python2.7
# -*- coding: iso-8859-1 -*-
#
# tester.py
# Description: automatically executes any program and records various data
# -----------------------------------------------------------------------------
#
# Started on  <Wed Dec 12 12:52:22 2012 Carlos Linares Lopez>
# Last update <Monday, 12 August 2013 00:18:48 Carlos Linares Lopez (clinares)>
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
automatically executes any program and records various data
"""

__version__  = '1.0.0'
__revision__ = '$Revision:$'
__date__     = '$Date:$'

# imports
# -----------------------------------------------------------------------------
import argparse         # parser for command-line options
import datetime         # date/time
import fnmatch          # filename matching
import getopt           # variable-length params
import getpass          # getuser
import logging          # loggers
import os               # path and process management
import pickle           # serialization
import re               # matching regex
import resource         # process resources
import shutil           # copy files and directories
import socket           # gethostname
import stat             # stat constants
import subprocess       # subprocess management
import sys              # argv, exit
import time             # time mgmt

from collections import defaultdict # finally, a smart way to handle dicts!
from string import Template     # to use placeholders in the logfile

import dbparser         # db parser specification
import dbtools          # database access & management
import sqltools         # sqlite3 database access
import systools         # IPC process management
import timetools        # IPC timing management
import tsttools         # test specifications

# -----------------------------------------------------------------------------

# globals
# -----------------------------------------------------------------------------
CHECK_INTERVAL = 1           # how often we query the process group status
KILL_DELAY = 5               # how long we wait between SIGTERM and SIGKILL

LOGDICT = {'node': socket.gethostname (),       # extra data to be passed
           'user': getpass.getuser ()}          # to loggers

OUTPUT = "output-"           # prefix of the output filenames

STATREGEXP = " >[\t ]*(?P<varname>[a-zA-Z ]+):[ ]+(?P<value>([0-9]+\.[0-9]+|[0-9]+))"

# -----------------------------------------------------------------------------

# funcs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# create_parser
#
# creates a command-line parser
#
# -----------------------------------------------------------------------------
def create_parser ():
    """
    creates a command-line parser
    """

    # create the parser
    parser = argparse.ArgumentParser (description="Automatically executes any program and records various data")

    # now, add the arguments

    # Group of mandatory arguments
    mandatory = parser.add_argument_group ("Mandatory arguments", "The following arguments are required")
    mandatory.add_argument ('-s', '--solver',
                            nargs='+',
                            required=True,
                            help="sets the solver to use for solving all cases. It is possible to provide as many as desired")
    mandatory.add_argument ('-f', '--test',
                            dest='tests',                            
                            required=True,
                            help="specification of the test cases")
    mandatory.add_argument ('-D', '--db',
                            dest='db',                            
                            required=True,
                            help="specification of the database tables with the information to record")
    mandatory.add_argument ('-t', '--time',
                            required=True,
                            type=int,
                            help="the maximum allowed time for solving a particular instance in seconds")
    mandatory.add_argument ('-m', '--memory',
                            required=True,
                            type=int,
                            help="the maximum allowed (overall) memory for solving a particular instance in Gigabytes")

    # Group of optional arguments
    optional = parser.add_argument_group ('Optional', 'The following arguments are optional')
    optional.add_argument ('-o', '--output',
                           default='$index-$subindex',
                           help="prefix of the output files generated by the solver. Placeholders can be used. For a description of the available placeholders type '--show-placeholders'. By default '$index-$subindex'")
    optional.add_argument ('-c', '--check',
                           default=5,
                           type=int,
                           help='delay between successive pings to the solver')
    optional.add_argument ('-d', '--directory',
                           default=os.getcwd (),
                           help="directory where the results of the tests are stored. By default, the current working directory. Relative directories are rooted in the current working directory")

    # Group of logging services
    logging = parser.add_argument_group ('Logging', 'The following arguments specify various logging settings')
    logging.add_argument ('-l', '--logfile',
                          help = "name of the logfile where the output of the whole process is recorded. The current date and time is appended at the end. It is left at the current working directory")
    logging.add_argument ('-L', '--level',
                          choices=['DEBUG', 'INFO', 'WARNING', 'CRITICAL'],
                          default='INFO',
                          help="level of log messages. Messages of the same level or above are shown. By default, INFO, i.e., all messages are shown")

    # Group of miscellaneous arguments
    misc = parser.add_argument_group ('Miscellaneous')
    misc.add_argument ('-S','--show-placeholders',
                       nargs=0,
                       action=ShowPlaceHolders,
                       help='shows a comprehensive list of the available placeholders for making substitutions in the output files generated by every solver')
    misc.add_argument ('-p', '--parse-tests',
                       dest='parse_tests',
                       action='store_true',
                       help="processes the test file, shows the resulting definitions and exits")
    misc.add_argument ('-b', '--parse-db',
                       dest='parse_db',
                       action='store_true',
                       help="processes the database specification file, shows the resulting definitions and exits")
    misc.add_argument ('-q', '--quiet',
                       action='store_true',
                       help="suppress headers")
    misc.add_argument ('-V', '--version',
                       action='version',
                       version=" %s %s %s %s" % (sys.argv [0], __version__, __revision__[1:-1], __date__[1:-1]),
                       help="output version information and exit")

    # and return the parser
    return parser


# -----------------------------------------------------------------------------
# ShowPlaceHolders
#
# shows a comprehensive list of the available place holders for making
# substitutions in the output files generated by every solver
# -----------------------------------------------------------------------------
class ShowPlaceHolders (argparse.Action):
    """
    shows a comprehensive list of the available place holders for making
    substitutions in the output files generated by every solver
    """

    def __call__(self, parser, namespace, values, option_string=None):
        print """
 placeholder   description
 %s+%s""" % ('-'*12, '-'*65)
        
        print """ $name       | name of the solver
 $index      | index of the current test case (defined in the test file)
 $subindex   | in case that the same test case is ran with different arguments
             | they are distinguished with the $subindex which is a number
             | starting with zero
 $date       | current date
 $time       | current time"""

        print """ %s+%s
 Also, every directive specified in the tests file can be used as a placeholder
 For example, if '--argument $enumerate' is used in the test file then 
 $argument can be used in '--output' to include its value in the output file
""" % ('-'*12, '-'*65)

        # and finally exit
        sys.exit (0)
        

# -----------------------------------------------------------------------------
# show_switches
#
# show a somehow beautified view of the current params
# -----------------------------------------------------------------------------
def show_switches (solver, filename, check, directory, time, memory):

    """
    show a somehow beautified view of the current params
    """

    # logger settings
    logger = logging.getLogger('testbot::show_switches')

    # compute the solvers' names
    solvernames = map (lambda x:os.path.basename (x), solver)

    logger.info ("""
-----------------------------------------------------------------------------
 * Solver               : %s
 * Tests                : %s

 * Check flag           : %i seconds

 * Directory            : %s
 * Time limit           : %i seconds
 * Memory bound         : %i bytes
-----------------------------------------------------------------------------\n""" % (solvernames, filename, check, directory, time, memory), extra=LOGDICT)


# -----------------------------------------------------------------------------
# check_flags
#
# check the parameters provided by the user
# -----------------------------------------------------------------------------
def check_flags (solver, filename, check, directory, timeout, memory):

    """
    check the parameters provided by the user
    """

    # logger settings
    logger = logging.getLogger('testbot::check_flags')

    # checks

    # verify that all solvers are accessible
    for isolver in solver:

        if (not os.access (isolver, os.F_OK) or 
            not os.access (os.path.dirname (isolver), os.X_OK)):
            print """
 The solver '%s' does not exist or it resides in an unreachable location
 Type '%s --help' for more information
""" % (isolver, PROGRAM_NAME)
            raise ValueError

    # verify also that the test cases are accessible as well
    if (filename and (not os.access (filename, os.F_OK) or 
                      not os.access (os.path.dirname (filename), os.R_OK))):
        print """
 The file specified with the cases does not exist or it resides in an unreachable location
 Type '%s --help' for more information
""" % PROGRAM_NAME
        raise ValueError

    # verify that check is not negative
    if (check < 0):
        logger.critical (" The check flag should be either zero or positive", 
                         extra=LOGDICT)

    # finally, verify the time and memory bounds
    if (timeout <= 0):
        logger.critical (" The timeout param shall be positive!", extra=LOGDICT)
        raise ValueError

    if (memory <= 0):
        logger.critical (" The memory param shall be positive!", extra=LOGDICT)
        raise ValueError


# -----------------------------------------------------------------------------
# version
#
# shows version info
# -----------------------------------------------------------------------------
def version (log=False):

    """
    shows version info
    """

    if (log):

        logger = logging.getLogger ("testbot::version")
        logger.info ("\n %s\n %s\n %s %s\n" % (__revision__[1:-2], __date__[1:-2], PROGRAM_NAME, __version__), 
                     extra=LOGDICT)

    else:
        print ("\n %s\n %s\n" % (__revision__[1:-1], __date__[1:-1]))
        print (" %s %s\n" % (PROGRAM_NAME, __version__))


# -----------------------------------------------------------------------------
# create_logger
#
# opens a file in write mode in the current working directory in case
# a logfile is given. If not, it creates a basic logger. Messages
# above the given level are issued.
#
# it returns the name of the logfile recording all logrecords. If none has been
# created it returns the empty string
# -----------------------------------------------------------------------------
def create_logger (logfile, level):

    """
    opens a file in write mode in the current working directory in
    case a logfile is given. If not, it creates a basic
    logger. Messages above the given level are issued.
    
    it returns the name of the logfile recording all logrecords. If
    none has been created it returns the empty string
    """

    # create the log file either as a file stream or to the stdout
    if (logfile):

        logging.basicConfig (filename=logfile, filemode = 'w', level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s") 

    else:
        logging.basicConfig (level=level, 
                             format="[%(asctime)s] [%(user)10s@%(node)s] [%(name)s] %(levelname)s\n%(message)s")

    # and return the logfilename
    return logfile


# -----------------------------------------------------------------------------
# fetch
#
# gather OS version info, cpu info, mem info and swap space info to be shown in
# different files located at the log dir
# -----------------------------------------------------------------------------
def fetch (logdir):
    """
    gather OS version info, cpu info, mem info and swap space info to be shown
    in different files located at the log dir
    """

    shutil.copy ("/proc/version", os.path.join (logdir, "ver-info.log"))
    shutil.copy ("/proc/cpuinfo", os.path.join (logdir, "cpu-info.log"))
    shutil.copy ("/proc/meminfo", os.path.join (logdir, "mem-info.log"))
    shutil.copy ("/proc/swaps"  , os.path.join (logdir, "swap-info.log"))


# -----------------------------------------------------------------------------
# process_results
#
# process the contents of the results file indicated which resides in the given
# directory and are relative to the instance qualified by the given index. The
# statistics are stored in a dictionary indexed by the variable name and the
# data consists of a list of tuples with the following information (problem
# index, value)
# -----------------------------------------------------------------------------
def process_results (directory, resultsfile, index, stats):
    """
    process the contents of the results file indicated which resides in the given
    directory and are relative to the instance qualified by the given index. The
    statistics are stored in a dictionary indexed by the variable name and the
    data consists of a list of tuples with the following information (problem
    index, value)
    """

    # logger settings
    logger = logging.getLogger ("testbot::process_results")

    # open the file
    with open (os.path.join (directory, resultsfile), 'r') as stream:

        # now, for each line in the output file
        for iline in stream.readlines ():

            # check whether this line contains a stat
            restat = re.match (STATREGEXP, iline)

            if (restat):

                # add this variable to the dictionary
                stats [restat.group ('varname').rstrip (" ")].append ((index, 
                                                                       float (restat.group ('value'))))


# -----------------------------------------------------------------------------
# setup
#
# this method just sets up all the necessary environment for executing all
# cases. It returns: the target directory where all output should be written;
# the directory where the results should be copied; the config dir where
# additional information (such as the test cases) should be written and the
# logdirectory where the logs should be stored. 
# -----------------------------------------------------------------------------
def setup (solvername, directory):
    """
    this method just sets up all the necessary environment for executing all
    cases. It returns: the target directory where all output should be written;
    the directory where the results should be copied; the config dir where
    additional information (such as the test cases) should be written and the
    logdirectory where the logs should be stored
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


    # logger settings
    logger = logging.getLogger ("testbot::setup")

    # compute the target directory 
    targetdir = os.path.join (directory, solvername)

    # the given directory should exist at this time, but not its
    # subdirectories. A couple of sanity checks follow:
    if (not os.access (directory, os.F_OK)):
        os.makedirs (directory)
        logger.debug (" The directory '%s' has been created!" % directory, extra=LOGDICT)
    if (os.access (targetdir, os.F_OK)):        # paranoid checking!!
        logger.critical (" The directory '%s' already exists!" % targetdir, extra=LOGDICT)
        raise ValueError

    # create the target directory
    os.mkdir (targetdir)
    
    # create another subdir to store the results. Note that the absolute path is
    # computed. Passing the absolute path to the results dir prevents a number
    # of errors
    resultsdir = _mksubdir (targetdir, "results")

    # and create also an additional directory to store additional information
    # such as the test cases
    configdir = _mksubdir (targetdir, "config")

    # and create also an additional directory to store different sorts of log
    # information
    logdir = _mksubdir (targetdir, "log")

    # return the directories to be used in the experimentation
    return (targetdir, resultsdir, configdir, logdir)


# -----------------------------------------------------------------------------
# test
#
# invokes the execution of the given solver *in the same directory where it
# resides* for solving all cases specified in 'cases' using the specified
# computational resources. The results are stored in 'resultsdir'; the solver is
# sampled every 'check' seconds and the different stats are stored in
# 'stats'. Output files are named after 'output'
# -----------------------------------------------------------------------------
def test (solver, cases, resultsdir, check, stats, output,
          timeout=1800, memory=6442450944):
    """
    invokes the execution of the given solver *in the same directory where it
    resides* for solving all cases specified in 'cases' using the specified
    computational resources. The results are stored in 'resultsdir'; the solver is
    sampled every 'check' seconds and the different stats are stored in
    'stats'. Output files are named after 'output'
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

    # initialization - the following dictionary contains the last subindex of
    # all test indices. This is necessary since every test case can result in
    # many different subcases if enum/range are used
    subindex = defaultdict (int)

    # logger settings
    logger = logging.getLogger ("testbot::test")

    # now, for each test case
    for itst in tsttools.TstIter (tsttools.TstFile (cases)):

        # initialize the dictionary with the value of the placeholders
        placeholders = {'index'   : itst.get_id (),
                        'subindex': str (subindex [itst.get_id ()]),
                        'name'    : os.path.basename (solver),
                        'date'    : datetime.datetime.now ().strftime ("%Y-%m-%d"),
                        'time'    : datetime.datetime.now ().strftime ("%H:%M:%S")}

        # and now, add the values of all the directives in this testcase
        placeholders.update (itst.get_values ())

        # finally, invoke the execution of this test case
        logger.info ('\t%s' % itst, extra=LOGDICT)

        run (os.path.abspath (solver), resultsdir, 
             itst.get_id (), itst.get_args (), 
             0, 
             _sub (output, placeholders),
             stats, check, timeout, memory)

        # and increment the subindex of this test index
        subindex [itst.get_id ()] += 1


# -----------------------------------------------------------------------------
# run
#
# executes the specified 'solver' *in the same directory where it resides* (this
# is fairly convenient in case the solver needs additional input files which are
# then extracted from a directory relative to the current location) for solving
# the particular test case (qualified by index). It copies the stdout and stderr
# of the solver in files named after output (plus .log or .err) which are then
# moved to the specified results directory. The forked process is pinged every
# 'check' seconds and it is launched with computational resources 'timeout' and
# 'memory'
# -----------------------------------------------------------------------------
def run (solver, resultsdir, index, spec, T, output, stats,
         check=5, timeout=1800, memory=6442450944):

    """
    executes the specified 'solver' *in the same directory where it resides*
    (this is fairly convenient in case the solver needs additional input files
    which are then extracted from a directory relative to the current location)
    for solving the particular test case (qualified by index). It copies the
    stdout and stderr of the solver in files named after output (plus .log or
    .err) which are then moved to the specified results directory. The forked
    process is pinged every 'check' seconds and it is launched with
    computational resources 'timeout' and 'memory'
    """

    def update_stats (index, data, key, stats):
        """
        update stats with the information in data. The result is a list of lists
        which are all preceded by index
        """

        stats[key] += (map (lambda x,y:tuple (x+y),
                            [[index]]*len (data), data))
        

    # logger settings
    logger = logging.getLogger ("testbot::run")

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
            logger.critical (" OSError raised when invoking the subprocess")
            raise OSError

        except ValueError:
            logger.critical (" Popen was invoked with invalid arguments")
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

            # store this information in the stats - note the leading
            # underscore. It means that this should not be treated as ordinary
            # data and it is considered to be system data instead
            stats ['_systime'].append ((index, real_time, total_time))
            stats ['_sysvsize'].append ((index, real_time, total_vsize))
            stats ['_sysprocs'].append ((index, real_time, num_processes))
            stats ['_systhreads'].append ((index, real_time, num_threads))

            # update the maximum memory usage
            max_mem = max (max_mem, total_vsize)

            # decide whether to kill the group or not
            try_term = (total_time > timeout or
                        real_time >= 1.5 * timeout or
                        max_mem > memory)
            try_kill = (total_time > timeout + KILL_DELAY or
                        real_time >= 1.5 * timeout + KILL_DELAY or
                        max_mem > memory)
            
            if try_term and not term_attempted:
                logger.debug (""" aborting children with SIGTERM ...
 children found: %s""" % timeline.pids (), extra=LOGDICT)
                timeline.terminate ()
                term_attempted = True
            elif term_attempted and try_kill:
                logger.debug (""" aborting children with SIGKILL ...
 children found: %s""" % timeline.pids (), extra=LOGDICT)
                timeline.terminate ()

        # record the exit status of this process
        stats ['_sysstatus'].append ((index, status))

        # Even if we got here, there may be orphaned children or something we
        # may have missed due to a race condition. Check for that and kill
        # properly for good measure. 
        logger.debug (""" aborting children with SIGKILL for the last time ...
 children found: %s""" % timeline.pids (), extra=LOGDICT)
        timeline.terminate ()

        # add the timeline of this execution to the stats - note the leading
        # underscore. It means that this should not be treated as ordinary data
        # and it is considered to be system data instead
        update_stats (index, timeline.get_processes (), '_systimeline', stats)

        # process the contents of the log files generated
        process_results (os.getcwd (), output + ".log", index, stats)

        # once it has been processed move the .log and .err files to the results
        # directory
        for ilogfile in ['.log', '.err']:
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
def wrapup (solver, filename, configdir):

    """
    wrapup all the execution performing the last operations
    """

    # logger settings
    logger = logging.getLogger ("testbot::wrapup")

    # copy the file with all the tests cases to the config dir
    shutil.copy (filename,
                 os.path.join (configdir, os.path.basename (filename)))


# -----------------------------------------------------------------------------
# insert_version_data
#
# saves the specified version data into the given database
# -----------------------------------------------------------------------------
def insert_version_data (progname, version, revision, date, databasename):

    """
    saves the specified version data into the given database
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_version_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing version data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the version table
    db.create_version_table ()

    # now, store all the version data
    db.insert_version_data (progname, version, revision, date)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_timeline_data
#
# saves the timeline computed in the execution into the given database
# -----------------------------------------------------------------------------
def insert_timeline_data (timeline, databasename):

    """
    saves the timeline computed in the execution into the given database
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_timeline_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing timeline into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the version table
    db.create_timeline_table ()

    # now, store all the timeline
    db.insert_timeline_data (timeline)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_status_data
#
# saves the return code of every test case into the given database
# -----------------------------------------------------------------------------
def insert_status_data (status, databasename):

    """
    saves the return code of every test case into the given database
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_status_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing status into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the version table
    db.create_status_table ()

    # now, store all the timeline
    db.insert_status_data (status)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_sys_data
#
# saves all the sys information given in the database
# -----------------------------------------------------------------------------
def insert_sys_data (D, databasename):

    """
    saves all the sys information given in the database
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_sys_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing sys data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create all the sys tables
    db.create_systime_table ()
    db.create_sysvsize_table ()
    db.create_sysprocs_table ()
    db.create_systhreads_table ()

    # and now, insert their contents into the database
    for isys in ['time', 'vsize', 'procs', 'threads']:
        db.insert_sysdata (isys, D['_sys' + isys])

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_admin_data
#
# saves the specified admin data into the given database
# -----------------------------------------------------------------------------
def insert_admin_data (filename, solver,
                       check, time, memory, databasename):

    """
    saves the specified admin data into the given database
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_admin_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing admin data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the admin table
    db.create_admin_table ()

    # now, store all the admin data
    db.insert_admin_data (filename, solver, check, time, memory)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_time_data
#
# saves the specified time data into the time table
# -----------------------------------------------------------------------------
def insert_time_data (starttime, endtime, databasename):

    """
    saves the specified time data into the time table
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_time_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing time data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the time table
    db.create_time_table ()

    # now, store all the admin data
    db.insert_time_data (starttime, endtime)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_test_data
#
# saves the specified tests data into the tests table
# -----------------------------------------------------------------------------
def insert_test_data (filename, databasename):

    """
    saves the specified tests data into the tests table
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_test_data")

    # retrieve the test cases
    cases = tsttools.TstFile (filename).get_defs ()

    # compute the filename
    dbfilename = databasename + '.db'
    logger.debug (" Writing test data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # create the time table
    db.create_test_table ()

    # now, store all the test data
    db.insert_test_data (cases)

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# insert_data
#
# saves the information given in the specified dictionary D into a sqlite3
# database. The primary key of the dictionary is the name of a variable whose
# value is a list of tuples with the following contents (problem id, value)
# -----------------------------------------------------------------------------
def insert_data (D, databasename):

    """
    saves the information given in the specified dictionary D into a sqlite3
    database. The primary key of the dictionary is the name of a variable whose
    value is a list of tuples with the following contents (problem id, value)
    """

    # logger settings
    logger = logging.getLogger ("testbot::insert_data")

    # compute the filename
    dbfilename = databasename + '.db'
    logger.info (" Writing data into '%s'" % dbfilename, extra=LOGDICT)

    # connect to the sql database
    db = sqltools.dbtest (dbfilename)

    # now, create the tables and populate them with data unless the name starts
    # with an underscore which means that it is not 'data'
    for ivar in [jvar for jvar in D if jvar[0] != '_']:

        # create this data table
        db.create_data_table (ivar)

        # store all tuples in this table
        db.insert_data (ivar, D[ivar])

    # close and exit
    db.close ()


# -----------------------------------------------------------------------------
# Dispatcher
#
# this class creates a dispatcher for automating the experiments. Besides, it
# creates specific __enter__ and __exit__ methods
# -----------------------------------------------------------------------------
class Dispatcher (object):
    """
    this class creates a dispatcher for automating the experiments. Besides, it
    creates specific __enter__ and __exit__ methods
    """

    # Default constructor
    def __init__ (self, solver, filename, dbspec, check, time, memory, 
                  directory, output, logfile, level, quiet):
        """
        Explicit constructor
        """
        
        # copy the attributes
        (self._solver, self._filename, self._dbspec, self._check, 
         self._time, self._memory, self._directory, 
         self._output, self._logfile, self._level,
         self._quiet) = \
         (solver, filename, dbspec, check, 
          time, memory, directory, 
          output, logfile, level, 
          quiet)


    # Execute the following body when entering the dispatcher
    def __enter__ (self):
        """
        Execute the following body when entering the dispatcher
        """

        # now, create the overall log file if anyone has been requested
        if (self._logfile):
            self._logstream = create_logger (self._logfile + '.' + 
                                             datetime.datetime.now ().strftime ("%y-%m-%d.%H:%M:%S"),
                                             self._level)
        else:
            self._logstream = create_logger (None, self._level)

        # before proceeding, check that all parameters are correct
        check_flags (self._solver, self._filename, self._check, 
                     self._directory, self._time, self._memory)


    # The following method sets up the environment for automating the experiments
    def tester (self):
        """
        The following method sets up the environment for automating the experiments
        """

        # logger settings
        logger = logging.getLogger("dispatcher::tester")

        # unless quiet has been explicitly requested
        if (not self._quiet):

            # show the current version
            version (log=True)

            # show the current params
            show_switches (self._solver, self._filename, 
                           self._check, self._directory, self._time, self._memory)

        # finally, run the experiments going solver by solver
        for isolver in self._solver:

            # create an empty dictionary of stats
            istats = defaultdict (list)

            solvername = os.path.basename (isolver)

            logger.info (" Starting experiments with solver '%s'" % solvername, 
                         extra=LOGDICT)

            # setup the necessary environment and retrieve the directories to be
            # used in the experimentation
            (targetdir, resultsdir, configdir, logdir) = setup (solvername, self._directory)

            # write all the log information in the logdir
            fetch (logdir)

            # record the start time
            self._starttime = datetime.datetime.now ()

            # now, invoke the execution of all tests with this solver
            test (isolver, self._filename, resultsdir, 
                  self._check, istats, self._output,
                  self._time, self._memory)

            # record the end time of this solver
            self._endtime = datetime.datetime.now ()

            # and wrapup
            wrapup (isolver, self._filename, configdir)

            # finally, write down all the information to a sqlite3 db
            insert_version_data (PROGRAM_NAME, __version__, __revision__[1:-1], __date__[1:-1],
                                 os.path.join (self._directory, solvername, solvername))
            insert_sys_data (istats, os.path.join (self._directory, solvername, solvername))
            insert_admin_data (self._filename, isolver, 
                               self._check, self._time, self._memory,
                               os.path.join (self._directory, solvername, solvername))
            insert_timeline_data (istats['_systimeline'], 
                                  os.path.join (self._directory, solvername, solvername))
            insert_status_data (istats['_sysstatus'], 
                                  os.path.join (self._directory, solvername, solvername))
            insert_time_data (self._starttime, self._endtime,
                              os.path.join (self._directory, solvername, solvername))
            insert_test_data (self._filename, 
                              os.path.join (self._directory, solvername, solvername))
            insert_data (istats, os.path.join (self._directory, solvername, solvername))


    # execute the following body before exiting
    def __exit__ (self, type, value, traceback):
        """
        execute the following body before exiting
        """

        # logger settings
        logger = logging.getLogger('dispatcher::__exit__')


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    PROGRAM_NAME = sys.argv[0]              # get the program name

    # parse the arguments
    PARSER = create_parser ()
    ARGS = PARSER.parse_args ()

    # convert the memory (currently in Gigabytes) to bytes
    ARGS.memory *= 1024**3

    # in case the user has requested just to parse and show the result of
    # processing either the test specification file or the db specification file
    if (ARGS.parse_tests or ARGS.parse_db):

        if (ARGS.parse_tests):
            print
            print " Contents of the test specification file:"
            print " ----------------------------------------"
            print tsttools.TstFile (ARGS.tests)

        if (ARGS.parse_db):
            print
            print " Contents of the database specification file:"
            print " --------------------------------------------"
            print dbtools.DBFile (ARGS.db)

        exit ()

    # Now, enclose all the process in a with statement and launch a dispatcher
    DISPATCHER = Dispatcher (ARGS.solver, ARGS.tests, ARGS.db,
                             ARGS.check, ARGS.time, ARGS.memory,
                             ARGS.directory, ARGS.output, ARGS.logfile, 
                             ARGS.level, ARGS.quiet)
    with DISPATCHER:
            
        # and request automating all the experiments
        DISPATCHER.tester ()



# Local Variables:
# mode:python
# fill-column:80
# End:
