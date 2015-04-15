#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# condorize.py
# Description: create condor description files which can be directly
# submitted to the condor queue
# -----------------------------------------------------------------------------
#
# Started on  <Wed Apr 15 10:29:48 2015 Carlos Linares Lopez>
# Last update <miércoles, 15 abril 2015 18:01:13 Carlos Linares Lopez (clinares)>
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
create condor description files which can be directly submitted to the
condor queue
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
from autobot import parsetools          # command line parser
from autobot import logutils            # logging utils

import logging                          # loggers
import os                               # operating system utilities
import string                           # string services: find
import subprocess                       # services to launch other execs

# -----------------------------------------------------------------------------
# CondorDescriptionFile
#
# registers information and provides means for creating condor submission
# description files
# -----------------------------------------------------------------------------
class CondorDescriptionFile(object):

    """
    registers information and provides means for creating condor submission
    description files
    """

    def __init__(self, solver, tstfile, dbfile, timeout, memory,
                 output, check, directory, compress, 
                 jobname, nonice, notify, copyfiles, submit,
                 logfile, loglevel,
                 quiet):
        """
        creates an instance of a new Condor Description File which is used to
        run testbot with the given parameters considering only a single solver
        """

        # copy the attributes - note that both the directory and the logfile are
        # normalizedq
        (self._solver, self._tstfile, self._dbfile, self._timeout, self._memory,
         self._output, self._check, self._directory, self._compress, 
         self._jobname, self._nonice, self._notify, self._copyfiles, self._submit,
         self._logfile, self._loglevel,
         self._quiet) = \
        (solver, tstfile, dbfile, timeout, memory,
         output, check, os.path.normpath(directory), compress,
         jobname, nonice, notify, copyfiles, submit,
         os.path.normpath(logfile), loglevel,
         quiet)

        # set up a logger
        logutils.configure_logger (os.getcwd (), None, args.level)
        self._logger = logging.getLogger ("Main")
        self._logger.addFilter (logutils.ContextFilter ())

        # check that the given parameters are correct ---this is just done for the
        # sake of consistency but all that this function does is to show a warning
        # in case no-nice has been specified
        self.check_flags ()

        # give this job a meaningful name if the user did not provide one - by
        # default, condor jobs are named after the executable. In case the user
        # provided a job name, it is appended to the exec name; otherwise,
        # '.condor' is added to it
        self._jobname = os.path.basename(self._solver)
        if jobname:
            self._jobname += '.' + jobname
        else:
            self._jobname += '.condor'

        
        # show the parameters provided by the command line on the console
        self.show_switches ()

            
        self._logger.debug (" A Condor submission description file for executable '%s' has been created" % self._solver)


    # -----------------------------------------------------------------------------
    # check_flags
    #
    # check the parameters given
    # -----------------------------------------------------------------------------
    def check_flags (self):
        """
        check the parameters given
        """

        # issue an error if logfile refers to a directory different than the
        # current one
        if(self._logfile and os.path.dirname(self._logfile)):
            self._logger.fatal(" The logfile (%s) should be local to the current working directory" % self._logfile)
            raise ValueError(" The logfile should be local to the current working directory")

        # likewise, check that the given (output) directory is not different
        # than the current working directory
        if(self._directory and
           os.path.dirname(self._directory)
           and not os.path.samefile(os.getcwd(), self._directory)):
            self._logger.fatal(" The directory (%s) should be local to the current working directory" % self._directory)
            raise ValueError(" The directory should be local to the current working directory")

        # also, verify that the user did not unadvertendly introduced a slash in
        # the job name (so that the resulting job name would look like a
        # directory). This is important since the condor submission description
        # file is named after the job name
        if(self._jobname and string.find(self._jobname, os.path.sep)>=0):
            self._logger.fatal(" The job name can not contain the character '%s'" % os.path.sep)
            raise ValueError(" The job name can not contain the character '%s'" % os.path.sep)
        
        # show a warning in case nonice is enabled
        if self._nonice:
            self._logger.warning("""
    No nice user has been requested! 
    Be aware that this option add privileges to this job over other users in the same condor pool
""")


    # -----------------------------------------------------------------------------
    # show_switches
    #
    # show a somehow beautified view of the current params using the given
    # logger
    # -----------------------------------------------------------------------------
    def show_switches (self):
        """
        show a somehow beautified view of the current params using the
        given logger
        """

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

      * Job name             : %s
      * Nice user            : %s
      * Notify               : %s
     -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-2], __version__, self._solver, self._tstfile, self._dbfile, self._check, self._directory, {False: 'disabled', True: 'enabled'}[self._compress], self._timeout, self._memory * 1024**3, self._jobname, {False: 'True', True: 'False'}[self._nonice], {False: 'disabled', True: self._notify}[self._notify!=None]))


    # -----------------------------------------------------------------------------
    # generate
    #
    # generates a condor submission description file which is named after
    # jobname and which runs testbot with the given parameter for the solver
    # specified in this instance. If a similar description file is found, an
    # error is raised.
    #
    # It returns the name of the condor submission description file generated
    # -----------------------------------------------------------------------------
    def generate (self):
        """
        generates a condor submission description file which is named after
        jobname and which runs testbot with the given parameter for the solver
        specified in this instance

        It returns the name of the condor submission description file generated
        """

        # initialization
        spec = str()

        # First block
        #
        # specify various options such as the universe, nice user, notification
        # settings and env variables handling
        # ---------------------------------------------------------------------
        spec += "universe = vanilla\n"
        spec += "getenv = True\n"
        spec += "nice_user = %s\n" % {False: 'True', True:'False'} [self._nonice]

        # in case e-mail notification was required, add it here
        spec += "notification = %s\n" % {False: "Never", True: "Always"} [self._notify!=None]
        if self._notify:
            spec += "notify_user = %s\n" % self._notify
        spec += '\n'

        # Second block
        #
        # specify the executable, its arguments, requested memory and the log
        # files
        # ---------------------------------------------------------------------
        # if it was requested to copy the files of testbot here, then they
        # should be copied to a local directory (testbot)and then to the backend
        # node
        spec += "executable = "
        if self._copyfiles:
            spec += "testbot/testbot.py\n"

        # otherwise, it is assumed that testbot.py is available in the backend
        # node
        else:
            spec += "testbot.py\n"

        # the arguments are a literal copy of the arguments given to this
        # instance. Note however, that condor is never used for parsing dbs,
        # test files or showing placeholders

        # first, consider those parameters that are just passed by to testbot
        spec += "arguments ="
        spec += " --solver %s" % self._solver
        spec += " --test %s" % self._tstfile
        spec += " --db %s" % self._dbfile
        spec += " --timeout %s" % self._timeout
        spec += " --memory %s" % self._memory
        spec += " --check %s" % self._check
        spec += " --directory '%s'" % self._directory
        spec += " --output '%s'" % self._output
        spec += " --logfile '%s'" % self._logfile
        spec += " --loglevel %s" % self._loglevel

        # second, other optional parameters that might affect its behaviour
        if self._compress:
            spec += " --bz2"
        if self._logfile:
            spec += " --logfile '%s'" % self._logfile
        if self._quiet:
            spec += " --quiet"
        spec += '\n'
            
        # memory
        spec += "request_memory = %i\n" % (self._memory * 1024)

        # log files - to keep the current directory as clean as possible, these
        # are written in a subdirectory
        spec += "output = logs/test.$(Cluster).$(Process).out\n"
        spec += "log = logs/test.$(Cluster).$(Process).log\n"
        spec += "error = logs/test.$(Cluster).$(Process).err\n"
        
        spec += '\n'

        # Third block
        #
        # specify the files to transfer
        # ---------------------------------------------------------------------
        # files to transfer to the backend node: the solver, and the tests and
        # db specification files and the directory testbot in case copyfiles was
        # requested
        spec += "transfer_input_files = %s, %s, %s" % (self._solver, self._tstfile, self._dbfile)
        if self._copyfiles:
            spec+= ", testbot"
        spec += '\n'

        # files to transfer from the backend node - just the output directory
        # given to testbot and the logfile in case any was specified
        spec += "transfer_output_files = %s" % self._directory
        if self._logfile:
            spec += ", %s" % self._logfile
        spec += '\n'

        spec += '\n'
        
        # Fourth block
        #
        # enqueue this job
        # ---------------------------------------------------------------------
        spec += "queue 1\n"

        # Generate the condor submission description file
        # ---------------------------------------------------------------------

        # the condor submission description file is named after the job name (so
        # that condor_q would return exactly the job name provided by the user)
        with open(self._jobname, 'w') as output:
            output.write(spec)

        # and return the name of the file generated
        return self._jobname
    

    # -----------------------------------------------------------------------------
    # submit
    #
    # this function submits the specified condor submission description file to
    # the condor queue
    # -----------------------------------------------------------------------------
    def submit (self, condordesc):
        """
        this function submits the specified condor submission description file to
        the condor queue
        """

        # redirect the log and standard output to different files so that the
        # whole output is recorded
        (fdlog, fderr) = (os.open (os.path.join (os.getcwd (), condordesc + "_q.log"),
                                   os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                   0666),
                          os.open (os.path.join (os.getcwd (), condordesc + "_q.err"),
                                   os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                   0666))

        # create a child and invoke the execution of condor_q with the given
        # condor submission description file. The standard output and standard
        # error are written to specific files.
        try:
            child = subprocess.Popen (["condor_q", condordesc],
                                      stdout = fdlog,
                                      stderr = fderr,
                                      cwd=os.getcwd())
        except OSError:
            self._logger.critical (" OSError raised when invoking the subprocess")
            raise OSError

        except ValueError:
            self._logger.critical (" Popen was invoked with invalid arguments")
            raise ValueError


# main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # Main settings
    # -------------------------------------------------------------------------
    # first of all, parse the arguments provided by the command line
    args = parsetools.CondorArgParser ().parse_args ()

    # now, iterate over all solvers specified in the parser
    for ijob in args.solver:

        # create a new condor submission description file with all this
        # information
        condorfile = CondorDescriptionFile(ijob, args.tests, args.db, args.timeout, args.memory,
                                           args.output, args.check, args.directory, args.bz2,
                                           args.job_name, args.nonice, args.notify,
                                           args.copy_files, args.submit,
                                           args.logfile, args.level,
                                           args.quiet)

        # and generate the condor submission description file
        condordesc = condorfile.generate()

        # and, if requested, submitted to the condor queue
        if args.submit:
            condorfile.submit(condordesc)


# Local Variables:
# mode:python
# fill-column:80
# End: