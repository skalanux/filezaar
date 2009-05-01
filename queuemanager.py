#!/usr/bin/env python
#    This file is part of FileZaar.
#    FileZaar is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    FileZaar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with FileZaar.  If not, see <http://www.gnu.org/licenses/>.
#    Author: Juan Manuel Schillaci ska@lanux.org.ar

import os, sys
import re
import threading
import config
from filezaar.constants import *
from filezaar.updater_bzr import UpdaterBZR
import dbus

class QueueManager(threading.Thread):
    """
    This class is on charge of processing incoming upload/synchronizing
    requests, the files on the queue should have a priprity so they can
    be process according to it, this could be achived using weigths
    according to a specific critery
    """
    def __init__(self, queue_):
        self.queue_ = queue_
        self.bus = dbus.SessionBus()
        filezaard = self.bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
        filezaard = self.bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
        self.filezaar_daemon = dbus.Interface(filezaard, 'org.filezaar.daemon')
        self.filezaar_daemon.EmitStatusChanged(STATUS_UPDATING, 'Synchronizing')

        # The updater has several methods to handle a file upload
        # In theory is possible to implements differents backends for
        # File Upload, for now the only backend used is bazaar

        self.updater = UpdaterBZR()
        self.updater.sync()

        self.filezaar_daemon.EmitStatusChanged(STATUS_IDLE, 'UpToDate')
        threading.Thread.__init__(self)

    def dbus_queue(self, arg):
        """
        Pushes into the queue requests received from DBUS
        """
        # Need to implement a thread so I can run the object 
        # mainloop, tal vez en el main???
        pass

    def run(self):
        while True:
            data = self.queue_.get()
            self.filezaar_daemon.EmitStatusChanged(STATUS_UPDATING, 'Uploading')
            self.updater.upload_file(data[0])
            self.filezaar_daemon.EmitStatusChanged(STATUS_IDLE, 'UpToDate')
