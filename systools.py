#!/usr/bin/python
#
# systools.py
# Description: process management ---literally taken from the IPC 2008
# -----------------------------------------------------------------------------
#
# Started on  <Tue Mar  8 09:26:14 2011 Carlos Linares Lopez>
# Last update <Tuesday, 23 July 2013 22:09:59 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id:: systools.py 306 2011-11-11 22:25:37Z clinares                        $
# $Date:: 2011-11-11 23:25:37 +0100 (Fri, 11 Nov 2011)                       $
# $Revision:: 306                                                            $
# -----------------------------------------------------------------------------
#

"""
.. module:: systools
   :platform: Linux
   :synopsis: process management ---adapted from the IPC 2008

.. moduleauthor:: Malte Helmert <Malte.Helmert@unibas.ch>, Carlos Linares Lopez <carlos.linares@uc3m.es>
"""

__version__  = '1.2'
__revision__ = '$Revision: 306 $'

# imports
# -----------------------------------------------------------------------------
import datetime         # date/time
import os               # process handling
import time             # time management

import fdtools          # filesystem management

from collections import defaultdict


# globals
# -----------------------------------------------------------------------------
JIFFIES_PER_SECOND = 100

# functions
# -----------------------------------------------------------------------------
def partition(text, pattern):
    pos = text.find(pattern)
    if pos == -1:
        return text, "", ""
    else:
        return text[:pos], pattern, text[pos + len(pattern):]


def rpartition(text, pattern):
    pos = text.rfind(pattern)
    if pos == -1:
        return "", "", text
    else:
        return text[:pos], pattern, text[pos + len(pattern):]


def read_processes (pgrp):
    """
    computes the list of processes whose process group matches the given one or
    whose parent process id matches the process id of a process under
    observation. This is necessary to still keep track of those processes that
    setpgrp () as a mechanism for communicating with its children
    """

    # compute the list of processes currently running in the system
    processes = [Process (int (filename)) for filename in os.listdir ("/proc") 
                 if filename.isdigit ()]

    # initialize a dictionary that maps every pgrp selected to the process ids
    # that belong to it 
    pgrps = defaultdict (set)
    pgrps[pgrp] = set ()        # annotate this pgrp for further tracking

    # now, compute the list of pgrps to watch until a fixpoint is reached
    sentinel = True
    while (sentinel):

        sentinel = False

        # and now update the list of pgrps to watch
        for iprocess in processes:
            if ((iprocess.pgrp not in pgrps or
                 iprocess.pid not in pgrps[iprocess.pgrp]) and
                (iprocess.pgrp in pgrps or
                 iprocess.ppid in reduce (lambda x,y:x.union (y), pgrps.values ()))):

                sentinel = True
                pgrps[iprocess.pgrp].add (iprocess.pid)

    # finally, filter the original list of processes and retain only those whose
    # pgrp has been selected
    return filter (lambda iprocess:iprocess.pgrp in pgrps, processes)


# -----------------------------------------------------------------------------
# Process
#
# Accesses the /proc filesystem to retrieve various statistics of a particular
# process identified by its process identifier (PID)
# -----------------------------------------------------------------------------
class Process(object):
    """
    Accesses the :file:`/proc` filesystem to retrieve various statistics of a
    particular process identified by its process identifier (PID)
    """

    def __init__(self, pid):
        """
        Access the :file:`stat` and :file:`cmdline` of a particular process
        identified by its process id (PID) in the :file:`/proc` filesystem. The
        parameters read are the following: ppid, pgrp, utime, stime, cutime,
        cstime, num_threads and vsize. For a comprehensive description of this
        parameters see ``man /proc``

        It also processes the entries in the /proc/<pid>/fd and stat its
        contents in the form of instances of FileInfo

        :param pid: process identifier (PID)
        :type pid: int
        """

        # avoid race conditions by verifying that there is still information
        # available about this process
        if (not os.path.exists ("/proc/%d/stat" % pid) or
            not os.path.exists ("/proc/%d/cmdline" % pid)):

            self.pid = self.ppid = self.pgrp = -1
            self.cmdline = '<Invalid cmdline>'

            return

        stat = open("/proc/%d/stat" % pid).read()
        cmdline = open("/proc/%d/cmdline" % pid).read()

        # Don't use stat.split(): the command can contain spaces.
        # Be careful which "()" to match: the command name can contain
        # parentheses.
        prefix, lparen, rest = partition(stat, "(")
        command, rparen, suffix = rpartition(rest, ")")
        parts = suffix.split()

        # now, retrieve various data from proc/%pid/stat
        self.pid = pid
        self.ppid = int(parts[1])
        self.pgrp = int(parts[2])
        self.utime = int(parts[11])
        self.stime = int(parts[12])
        self.cutime = int(parts[13])
        self.cstime = int(parts[14])
        self.numthreads = int (parts[17])
        self.sttime = int (parts[19])
        self.vsize = int(parts[20])
        self.cmdline = cmdline.rstrip("\0\n").replace("\0", " ")

        # now, compute the start time of this process as the difference between
        # the current time and the boot up time plus the time in seconds (which
        # is the start time divided by the number of jiffies)
        uptime=open ("/proc/uptime").read ()
        self.starttime = time.time () - float (uptime.split (' ')[0]) + \
            self.sttime/float(JIFFIES_PER_SECOND)

        # compute the initial list of files used by this process
        self.fd = list ()
        self.update_fd ()

        # finally, initialize the end time of this process to an impossible
        # value (so that consistency can be enforced later) and the list of fds
        # to an empty list
        self.endtime=-1


    def __str__ (self):
        """
        service for printing this instance
        """

        return " cmdline: '%s' [pid: %i, ppid: %i, pgrp: %i]" % \
            (self.cmdline, self.pid, self.ppid, self.pgrp)


    def __eq__ (self, other):
        """
        returns true if this instance and other refer to the same process
        """

        return (self.pid == other.get_pid ())


    def __ne__ (self, other):
        """
        returns false if this instance and other refer to the same process
        ---defined only for consistency with __eq__
        """

        return (self.pid != other.get_pid ())


    def get_pid (self):
        """
        returns the start time of this process
        """
        
        return self.pid


    def get_cmdline (self):
        """
        returns the name of this process
        """

        return self.cmdline


    def get_fd (self):
        """
        returns a list of FileInfo objects with the files used by this process
        """

        return self.fd


    def get_start_time (self):
        """
        returns the start time of this process
        """
        
        return self.starttime


    def get_end_time (self):
        """
        returns the end time of this process
        """
        
        return self.endtime


    def set_end_time (self, value):
        """
        sets the end time of this process
        """
        
        self.endtime = value


    def total_time(self):
        """
        returns the total cumulated time of this process as the sum of utime,
        stime, cutime and cstime.
        """

        return self.utime + self.stime + self.cutime + self.cstime

    def update_fd (self):
        """
        updates information about all the files this process access
        """

        # first of all, check that the proc/%d/fd subdirectory is accessible
        path = "/proc/%d/fd" % self.pid
        if (os.access (path, os.F_OK) and
            os.access (path, os.R_OK)):
            
            # check all files in the fd subdirectory
            for ipath in os.listdir (path):

                # and add those that are not present
                if os.path.exists ("/proc/%d/fd/%s" % (self.pid, ipath)):
                    fileInfo = fdtools.FileInfo ("/proc/%d/fd/%s" % (self.pid, ipath))

                    # in case this is a valid FileInfo instance which has not
                    # been seen before
                    if (fileInfo.get_stat () and
                        fileInfo not in self.fd):

                        # then add it to the list of fds of this process
                        self.fd.append (fileInfo)


# -----------------------------------------------------------------------------
# ProcessGroup
#
# Monitor all process that share the same group process id. It provides services
# to acces some statistics such as the memory used, the total CPU time, or the
# total number of threads launched by all processes.
# -----------------------------------------------------------------------------
class ProcessGroup(object):
    """
    Monitor all process that share the same group process id. It provides
    services to acces some statistics such as the memory used, the total CPU
    time, or the total number of threads launched by all processes.
    """

    def __init__(self, pgrp):
        """
        seeks and stores internally a list of all processes that match the given
        group id. Since it uses the :file:`/proc` filesystem, the systools are
        solely restricted to GNU/Linux OSs

        :param pgrp: group id
        :type pgrp: int
        """

        # usually the jiffies per second should be 100. Check it, however!
        self._jiffies_per_second = os.sysconf (os.sysconf_names['SC_CLK_TCK'])
        if (self._jiffies_per_second != 100):
            raise ValueError

        # initialize the list of processes with this group process id
        self.processes = read_processes (pgrp)
        # self.processes = [process for process in read_processes()
        #                   if process.pgrp == pgrp]

        print "-" * 80
        for iprocess in self.processes:
            print " \t ", iprocess


    def get_processes (self):
        """
        return a list of processes
        """

        return self.processes


    def pids(self):
        """
        returns the process identifier of all processes managed by this instance

        For example, if the process id of the *ipython* interpreter is 3075, the
        following code returns the only process id in its own group::

          In [1]: from IPCData import systools

          In [2]: group = systools.ProcessGroup (3075)

          In [3]: group.pids ()
          Out[3]: [3075]
          
        :returns: list of ints
        """

        return [p.pid for p in self.processes]


    def total_time(self):
        """
        cumulated CPU time for this process group, in seconds

        Assuming that the process id of the *ipython* interpreter is 3075, the
        following code returns the total CPU time of the processes in this group
        (which is only one, the interpreter itself)::

          In [1]: from IPCData import systools

          In [2]: group = systools.ProcessGroup (3075)

          In [3]: group.total_time ()
          Out[3]: 0.24

        :returns: int
        """
        
        total_jiffies = sum([p.total_time() for p in self.processes])
        return total_jiffies / float(JIFFIES_PER_SECOND)
                
    def total_vsize(self):
        """
        cumulated virtual memory for this process group, in MB

        If the group id of the *ipython* interpreter is 3075, the following
        snippet can be used to return the total amount of memory in use by the
        processes in this group (which is only one, the interpreter itself)::

          In [1]: from IPCData import systools

          In [2]: group = systools.ProcessGroup (3075)

          In [3]: group.total_vsize ()
          Out[3]: 60.36328125

        :returns: int
        """
        
        total_bytes = sum([p.vsize for p in self.processes])
        return total_bytes / float(2 ** 20)

    def total_processes (self):
        """
        return the total number of processes in this group.

        Say the current group id of my *ipython* interpreter is 3075. Then, the
        following chunk of code shows how to retrieve the total number of
        processes in this group, which is only one, the interpreter itself::

          In [1]: from IPCData import systools

          In [2]: group = systools.ProcessGroup (3075)

          In [3]: group.total_processes ()
          Out[3]: 1

        :returns: int
        """

        return (len (self.processes))


    def total_threads (self):
        """
        return the total number of threads of all processes in this group

        If the group process id of the *ipython* interpreter is 3075, the number
        of threads launched by its processes (which is only one, the interpreter
        itself), can be retrieved with the following lines::

          In [1]: from IPCData import systools

          In [2]: group = systools.ProcessGroup (3075)

          In [3]: group.total_threads ()
          Out[3]: 1

        :returns: int
        """

        return sum ([p.numthreads for p in self.processes])



# -----------------------------------------------------------------------------
# ProcessTimeline
#
# contains a timeline with the start-end time of all processes that were
# executed with a particular process group id
# -----------------------------------------------------------------------------
class ProcessTimeline(object):
    """
    contains a timeline with the start-end time of all processes that were
    executed with a particular process group id
    """

    def __init__(self):
        """
        initializes the list of processes with a given process group id to null
        """

        self.processes = []
        

    def __iadd__ (self, other):
        """
        adds the processes in the process group specified in other to this
        timeline
        """

        # first, take the curren time - this is just an estimation of the end
        # time of the processes. Its accuracy depends on the number of times
        # that the services of this class are invoked
        currtime = time.time ()
        
        # print
        # print " Current processes: ", [p.pid for p in self.processes]
        # print " New processes    : ", [p.pid for p in other.processes]

        # for all processes currently in the timeline that are not in the other
        # process group and whose end time is not set, specify their end time
        oldprocs = filter (lambda x:x not in other.get_processes () and x.get_end_time () < 0,
                           self.processes)
        for iproc in oldprocs:
            iproc.set_end_time (currtime)
            
            # also, add new files used by this process if that is the case
            iproc.update_fd ()
            
            # and update the info (access/modification times and size)
            for ifd in iproc.get_fd ():
                ifd.update ()

        # second, add to this timeline all processes in the other process group
        # that are not contained in the current timeline
        self.processes += filter (lambda x:x not in self.processes,
                                  other.get_processes ())

        return self


    def terminate (self):
        """
        close the current timeline by setting the current time as the end time
        of all its processes with unknown end time
        """

        # first, take the curren time - this is just an estimation of the end
        # time of the processes. Its accuracy depends on the number of times
        # that the services of this class are invoked
        currtime = time.time ()

        # and now set the end time of those processes to the current time
        for iproc in [jproc for jproc in self.processes if jproc.get_end_time () < 0]:
            iproc.set_end_time (currtime)

        # finally, update the information on the files used by every process
        for iproc in self.processes:
            iproc.update_fd ()
            for ifd in iproc.get_fd ():
                ifd.update ()


    def get_processes (self):
        """
        returns a list of lists containing each one data about every process
        along with their start/end times
        """

        return [[iproc.get_pid (),
                 iproc.get_cmdline (),
                 str (datetime.datetime.fromtimestamp (iproc.get_start_time ())),
                 str (datetime.datetime.fromtimestamp (iproc.get_end_time ()))] 
                for iproc in self.processes]


    def get_fd (self):
        """
        returns a list of lists containing each one data about file opened by
        every process
        """

        return [[iproc.get_pid (),
                 ifd.get_path (),
                 ifd.get_uid (),
                 ifd.get_gid ()]
                 # ifd.get_size (),
                for iproc in self.processes
                for ifd in iproc.fd]


    def get_times (self, attr):
        """
        returns a list of lists containing each one the times indicated by the
        attribute for every file opened by every process. Legal choices are
        ['atime', 'mtime', 'ctime']
        """

        return [[iproc.get_pid (),
                 ifd.get_path (),
                 str (datetime.datetime.fromtimestamp (int (itime )))]
                for iproc in self.processes
                for ifd in iproc.fd
                for itime in ifd.get_time (attr)]


    def get_size (self):
        """
        returns a list of lists containing each one the different sizes along
        with the timestamp when the size was observed for all files used by
        every process
        """

        return [[iproc.get_pid (),
                 ifd.get_path (),
                 str (datetime.datetime.fromtimestamp (int (itime))),
                 isize]
                for iproc in self.processes
                for ifd in iproc.fd
                for itime, isize in ifd.get_size ()]



# Local Variables:
# mode:python
# fill-column:80
# End:
