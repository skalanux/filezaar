#!/usr/bin/env python
#    This file is part of FileZaar.
#    FileZaar is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#   FileZaar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with FileZaar.  If not, see <http://www.gnu.org/licenses/>.
#    Author: Juan Manuel Schillaci ska@lanux.org.ar

import config
import os, sys
import time

import pyinotify
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes

from filezaar.constants import *

class Process(ProcessEvent):
    """
    Class that process events as they ocurred
    """
    def __init__(self, queue_):
        self.queue_ = queue_
        self.bl_pattern = BLACK_LISTED_FILE_PATTERN

        #Create Events handler
        self.events_handler = {}

        self._register_event('IN_CREATE', '_handle_update')
        self._register_event('IN_MODIFY', '_handle_update')
        self._register_event('IN_MOVED_FROM', '_handle_update')
        self._register_event('IN_ISDIR', '_handle_isdir')
        self._register_event('IN_DELETE', '_handle_dummy')

        print "events handler: ",self.events_handler

    def _register_event(self, handler, evt):
        self.events_handler[handler] = evt

    def __call__(self, caller_event):
        file_name = caller_event.name

        # TODO: Check if it is possible to set the an ignore pattern
        # instead of doing this
        if not self.bl_pattern.match(file_name):
            pathname = caller_event.pathname
            maskname = caller_event.maskname

            #Calling the actual event
            events_name = maskname.split("|")
            print events_name

            try:
                if len(events_name) == 3:
                    event_type = events_name[0]
                    handler_name = self.events_handler[event_type]
                    getattr(self, handler_name)(event_type, pathname)
                else:
                    for event in events_name:
                        handler_name = self.events_handler[event]
                        getattr(self, handler_name)(event, pathname)
            except Exception, e:
                print e

    def _handle_update(self,event, file_name):
        #self.parent.upload_file(file_name)
        self.queue_.put((file_name,))

    def _handle_isdir(self, event, file_name):
        # Probably we will only need to use smart add when it is a directory
        # self.parent.upload_file(file_name)
        pass

    def _handle_dummy(self, event, file_name):
        """Do nothing."""
        pass

class Watcher(object):
    def __init__(self):
        configuration = config.get_config()
        self.working_path = configuration[LOCAL_FILES_DIR]

    def monitor(self, queue_):
        wm = WatchManager()
        notifier = Notifier(wm, Process(queue_))
        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | \
            pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | \
            pyinotify.IN_ISDIR
        wm.add_watch(self.working_path, mask, rec=False)

        try:
            while True:
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            return
