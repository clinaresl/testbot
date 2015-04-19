#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# condorize.py
# Description: create condor description files which can be directly
# submitted to the condor queue
# -----------------------------------------------------------------------------
#
# Started on  <Wed Apr 15 10:29:48 2015 Carlos Linares Lopez>
# Last update <lunes, 20 abril 2015 00:30:29 Carlos Linares Lopez (clinares)>
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
import shutil                           # for copying trees
import site                             # to find Python installation dirs
import string                           # string services: find
import subprocess                       # services to launch other execs
import sys                              # binaries/modules path

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
                 jobname, nonice, notify, copyfiles,
                 transfer_input_files, transfer_output_files, submit,
                 logfile, loglevel, quiet):
        """
        creates an instance of a new Condor Description File which is used to
        run testbot with the given parameters considering only a single solver
        """

        # copy the attributes - note that both the directory and the logfile are
        # normalizedq
        (self._solver, self._tstfile, self._dbfile, self._timeout, self._memory,
         self._output, self._check, self._directory, self._compress, 
         self._jobname, self._nonice, self._notify, self._copyfiles,
         self._transfer_input_files, self._transfer_output_files, self._submit,
         self._logfile, self._loglevel, self._quiet) = \
        (solver, tstfile, dbfile, timeout, memory,
         output, check, os.path.normpath(directory), compress,
         jobname, nonice, notify, copyfiles,
         transfer_input_files, transfer_output_files, submit,
         logfile, loglevel, quiet)

        # make sure to process the logfile correctly in case it was given a
        # value
        if logfile:
            self._logfile = os.path.normpath(logfile)

        # likewise, normalize the directories given in
        # transfer_input/output_files as well
        self._transfer_input_files = map (lambda x:os.path.normpath(x),
                                          self._transfer_input_files)
        self._transfer_output_files = map(lambda x:os.path.normpath(x),
                                          self._transfer_output_files)

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


    # -----------------------------------------------------------------------------
    # check_flags
    #
    # check the parameters given
    # -----------------------------------------------------------------------------
    def check_flags (self):
        """
        check the parameters given
        """

        # make sure that neither the solver nor the specification files are
        # given as a path which is nested more than one level.
        for ifile in [self._solver, self._tstfile, self._dbfile]:
            if len(string.split(os.path.dirname(os.path.normpath(ifile)), '/')) > 1:
                self._logger.fatal(" It is not possible to specify files which are nested more than one level: %s" % ifile)
                raise ValueError(" It is not possible to specify files which are nested more than one level: %s" % ifile)
            
        # Also, ensure that these files exist and, in the specific case of the
        # solver, that it can be executed
        if not os.access(self._solver, os.F_OK | os.X_OK):
            self._logger.fatal(" The solver %s does not exist or it is not executable" % ifile)
            raise ValueError(" The solver %s does not exist or it is not executable" % ifile)

        for ifile in [self._tstfile, self._dbfile]:
            if not os.access(ifile, os.F_OK):
                self._logger.fatal(" The configuration file %s does not exist or it is unaccessible" % ifile)
                raise ValueError(" The configuration file %s does not exist or it is unaccessible" % ifile)
        
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

        # verify also that all directories referred in transfier_input_files and
        # transfer_output_files exist, are accessible and are rooted in the
        # current working directory
        for ifile in self._transfer_input_files:
            if os.path.dirname(ifile):
                self._logger.fatal(" The directory %s given in transfer_input_files should be local to the current working directory" % ifile)
                raise ValueError(" The directory %s given in transfer_input_files should be local to the current working directory" % ifile)
            if not os.access (ifile, os.F_OK | os.X_OK):
                self._logger.fatal(" The directory %s does not exist or it is unaccessible" % ifile)
                raise ValueError(" The directory %s does not exist or it is unaccessible" % ifile)

        for ifile in self._transfer_output_files:
            if os.path.dirname(ifile):
                self._logger.fatal(" The directory %s given in transfer_output_files should be local to the current working directory" % ifile)
                raise ValueError(" The directory %s given in transfer_output_files should be local to the current working directory" % ifile)

        # more over, make sure that files in transfer-input-files consist of a
        # single level(dunno exactly why, I am not able to make condor transfer
        # files correctly when more than one level is given ...)
        for ifile in self._transfer_input_files:
            if len(string.split(os.path.dirname(os.path.normpath(ifile)), '/')) > 1:
                self._logger.fatal(" It is not possible to specify files to be transferred in the input which are nested more than one level")
                raise ValueError(" It is not possible to specify files to be transferred in the input which are nested more than one level")
            
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
      * Solver                : %s
      * Tests                 : %s
      * Database              : %s

      * Check flag            : %.2f seconds

      * Directory             : %s
      * Compression           : %s
      * Time limit            : %i seconds
      * Memory bound          : %i bytes

      * Job name              : %s
      * Nice user             : %s
      * Notify                : %s
      * transfer_input_files  : %s
      * transfer_output_files : %s
     -----------------------------------------------------------------------------""" % (__revision__[1:-1], __date__[1:-2], __version__, self._solver, self._tstfile, self._dbfile, self._check, self._directory, {False: 'disabled', True: 'enabled'}[self._compress], self._timeout, self._memory * 1024**3, self._jobname, {False: 'True', True: 'False'}[self._nonice], {False: 'disabled', True: self._notify}[self._notify!=None], self._transfer_input_files, self._transfer_output_files))

    # -----------------------------------------------------------------------------
    # copy_autobot
    #
    # it copies the installation of autobot and testbot in the current machine
    # to a dedicated directory with the given name.
    # -----------------------------------------------------------------------------
    def copy_autobot (self, dst):
        """
        it copies the installation of autobot and testbot in the current machine to
        a dedicated directory with the given name.
        """

        # for every directory where autobot might be found
        for idir in site.getsitepackages():

            # in case autobot resides here
            if os.path.exists(os.path.join(idir, 'autobot')):

                # copy it ignoring the pyc files and exit
                shutil.copytree(os.path.join(idir, 'autobot'),
                                os.path.join(os.getcwd(), dst),
                                ignore=shutil.ignore_patterns("*.pyc"))
                break

        # if control reaches this point then autobot has not been found, raise
        # then an error
        else:
            raise ValueError(" 'autobot' has not been found in the current Python installation!")
    

    # -----------------------------------------------------------------------------
    # copy_testbot
    #
    # it copies the installation of testbot.py in the current machine to a
    # dedicated directory with the given name.
    # -----------------------------------------------------------------------------
    def copy_testbot (self, dst):
        """
        it copies the installation of testbot.py in the current machine to a
        dedicated directory with the given name.
        """

        # for every directory where autobot might be found
        for idir in sys.path:

            print " * idir: %s" % idir
            
            # in case autobot resides here
            if os.path.exists(os.path.join(idir, 'testbot.py')):

                # copy it and exit
                shutil.copy(os.path.join(idir, 'testbot.py'),
                            os.path.join(os.getcwd(), dst))
                break
                
        # if control reaches this point then testbot.py has not been found,
        # raise then an error
        else:
            raise ValueError(" 'testbot.py' has not been found in the current Python installation!")
    

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

        def _normdirname(path):
            """
            returns the directory of the given path after normalizing it
            """

            return os.path.dirname(os.path.normpath(path))
        

        # first of all, make sure the logs directory exists. If not, create it
        if not os.path.exists ('logs'):
            os.mkdir ('logs')
        
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
        spec += " --output %s" % self._output
        spec += " --level %s" % self._loglevel

        # second, other optional parameters that might affect its behaviour
        if os.getcwd()!=os.path.abspath('./'):
            # if the --directory directive took its default value, then do not
            # add it!
            spec += " --directory %s" % self._directory

        else:
            # otherwise, make sure that transfer_output_files contains the name
            # of the solver. For this, it just suffices to overwrite the value
            # of self._directory
            self._directory = os.path.basename(self._solver)
        if self._compress:
            spec += " --bz2"
        if self._logfile:
            spec += " --logfile '%s'" % self._logfile
        if self._quiet:
            spec += " --quiet"
        spec += '\n'
            
        # memory
        # spec += "request_memory = %i\n" % (self._memory * 1024)

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
        # requested. Regarding the solver and the configuration files, only the
        # directories have to be specified

        # create a list with these directories
        paths = []
        for ifile in [self._solver, self._tstfile, self._dbfile]:

            # if this path starts with a directory
            if string.split(_normdirname(ifile), '/') [0]:
                paths.append(string.split(_normdirname(ifile), '/') [0])

        # also, add to the list of paths to transfer, the testbot directory in
        # case copy-files was requested and also all directories specified in
        # transfer-input-files
        if self._copyfiles:
            paths.append("testbot")
        for ifile in self._transfer_input_files:
            paths.append(ifile)
                
        # now, ensure that there are no duplicates
        paths=list(set(paths))

        # in case there is at least one file in paths, or copy-files has been
        # requested or transfer-input-files has been given, then create an entry
        # for this directive
        if len(paths) > 0:
            spec += "transfer_input_files = %s" % paths[0]

            # and copy the rest all one after the other
            for ipath in paths[1:]:
                spec += ", %s" % ipath
            
        spec += '\n'

        # files to transfer from the backend node - just the output directory
        # given to testbot and the logfile in case any was specified
        spec += "transfer_output_files = %s" % self._directory
        if self._logfile:
            spec += ", %s" % self._logfile
        for ifile in self._transfer_output_files:
            spec += ", %s" % ifile
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
    # the condor queue. If necessary, it copies autobot and testbot so that
    # condor can get them
    # -----------------------------------------------------------------------------
    def submit (self, condordesc):
        """
        this function submits the specified condor submission description file to
        the condor queue
        """

        # in case copy-files was requested
        target = 'testbot'
        if self._copyfiles:
        
            # first, make sure there is no directory called 'testbot'
            if os.path.exists(os.path.join(os.getcwd(), target)):
                self._logger.fatal(" The target directory '%s' already exists!" % target)
                raise ValueError(" The target directory '%s' already exists!" % target)

            # now, copy the installation of autobot
            self.copy_autobot(target)

            # and also the installation of testbot.py
            self.copy_testbot(target)
        
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
            child = subprocess.Popen (["condor_submit", condordesc],
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
                                           args.copy_files, args.transfer_input_files,
                                           args.transfer_output_files, args.submit,
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
