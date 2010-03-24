#!/usr/bin/env python

#   This File is Slightly based on wicd daemon implementation
#   Copyright (C) 2007 - 2008 Adam Blackburn
#   Copyright (C) 2007 - 2008 Dan O'Reilly
#   Copyright (C) 2007 - 2008 Byron Hillis
#   
#   Filezaar Daemon:
#   Copyright (C) 2009 Juan Manuel Schillaci
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License Version 2 as
#   published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
""" filezaar - filezaar daemon implementation.

"""

import os
import sys
import time
import getopt
import ConfigParser
import signal
import logging
import Queue

# DBUS
import gobject
import dbus
import dbus.service

# Others clean up
import os, sys
import re
from fnmatch import translate
import time
from bzrlib import branch, errors
from bzrlib.conflicts import ConflictList
from bzrlib.lockdir import LockDir
from bzrlib.workingtree import WorkingTree
from dbus.mainloop.glib import DBusGMainLoop

# FileZaar specific libraries
#from filezaar.queuemanager import QueueManager
#from filezaar.watcher import Watcher
import config
from filezaar.constants import *


DBusGMainLoop(set_as_default=True)
global child_pid

class FileZaarDBUS(dbus.service.Object):
    def __init__(self, bus_name, object_path='/org/filezaar/daemon',
                 auto_connect=True):
        dbus.service.Object.__init__(self, bus_name, object_path)

    @dbus.service.method('org.filezaar.daemon')
    def Hello(self):
        """ Return the version number."""
        # VERSIONNUMBER
        version = '0.1'
        print 'returned version number', version
        return version

    @dbus.service.method('org.filezaar.daemon')
    def GetFileZaarStatus(self):
        """ Return the version number."""
        # Checking for the state of filezaar
        # right now this is a dummy method
        return STATUS_IDLE, "Filezaar is uptodate"

    ########## Signals and Signals methods #############################
    ####################################################################

    # Status Changed
    @dbus.service.method('org.filezaar.daemon', in_signature='uav')
    def EmitStatusChanged(self, state, info):
        self.StatusChanged(state, info)

    @dbus.service.signal(dbus_interface='org.filezaar.daemon', signature='uav')
    def StatusChanged(self, state, info):
        """ Emits a "status changed" dbus signal.

        This D-Bus signal is emitted when the connection status changes.

        """
        pass

    # Request a Synchronization
    @dbus.service.method('org.filezaar.daemon')
    def EmitRequestSync(self):
        self.RequestSync()

    @dbus.service.signal(dbus_interface='org.filezaar.daemon')
    def RequestSync(self):
        """ Emits a "status changed" dbus signal.

        This D-Bus signal is emitted when the connection status changes.

        """
        print "Requesting synchronization"
        pass


################ Start Module Methods #############################
###################################################################
def usage():
    # VERSIONNUMBER
    print """
    filezaar 0.1
    FileZaar connection daemon.
    """

def daemonize():
    """ Disconnect from the controlling terminal.
    """
    # Fork the first time to disconnect from the parent terminal and
    # exit the parent process.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "Fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # Decouple from parent environment to stop us from being a zombie.
    os.setsid()
    os.umask(0)

    # Fork the second time to prevent us from opening a file that will
    # become our controlling terminal.
    try:
        pid = os.fork()
        if pid > 0:
            pidfile = '/tmp/filezaar.pid'
            dirname = os.path.dirname(pidfile)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            pidfile = open(pidfile, 'w')
            pidfile.write(str(pid) + '\n')
            pidfile.close()
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "Fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.__stdin__.fileno())
    os.close(sys.__stdout__.fileno())
    os.close(sys.__stderr__.fileno())

    # stdin always from /dev/null
    sys.stdin = open('/dev/null', 'r')


def main(argv):
    """ The main daemon program.

    Keyword arguments:
    argv -- The arguments passed to the script.

    """
    global child_pid
    do_daemonize = True
    redirect_stderr = True
    redirect_stdout = True
    auto_connect = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'fenoah',
                                   ['help', 'no-daemon', 'no-poll', 'no-stderr', 'no-stdout',
                                    'no-autoconnect'])
    except getopt.GetoptError:
        # Print help information and exit
        usage()
        sys.exit(2)

    no_poll = False
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o in ('-e', '--no-stderr'):
            redirect_stderr = False
        if o in ('-o', '--no-stdout'):
            redirect_stdout = False
        if o in ('-f', '--no-daemon'):
            do_daemonize = False
        if o in ('-a', '--no-autoconnect'):
            auto_connect = False
        if o in ('-n', '--no-poll'):
            no_poll = True

    #This is commented only for testing purposes
    #daemonize()

    # Open the DBUS session
    # TODO: Decide if I should use a SessionBus(SessionWide) or a SystemBus(SystemWide)
    d_bus_name = dbus.service.BusName('org.filezaar.daemon', bus=dbus.SessionBus())
    obj = FileZaarDBUS(d_bus_name, auto_connect=auto_connect)

    gobject.threads_init()

    (child_pid, aa, bb, cc) = gobject.spawn_async(["controller.py"],
                                               flags=gobject.SPAWN_CHILD_INHERITS_STDIN)


    signal.signal(signal.SIGINT, sigterm_caught)
    signal.signal(signal.SIGTERM, sigterm_caught)
    # Enter the main loop
    mainloop = gobject.MainLoop()
    mainloop.run()


def sigterm_caught(sig, frame):
    global child_pid
    """ Called when a SIGTERM is caught, kills controller.py before exiting. """
    print 'SIGTERM caught, killing controller..'
    os.kill(child_pid, signal.SIGTERM)
    print 'Removing PID file...'
    if os.path.exists(wpath.pidfile):
        os.remove(wpath.pidfile)
    print 'Shutting down...'
    sys.exit(0)


if __name__ == '__main__':
    # Only do this if we decide to use system bus instead of the session One
    # if os.getuid() != 0:
    #    print ("Root privileges are required for the daemon to run properly." +
    #           "  Exiting.")
    #    sys.exit(1)
    main(sys.argv)
