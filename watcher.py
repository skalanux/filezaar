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

import os, sys
import time
from bzrlib import branch, errors
from bzrlib.workingtree import WorkingTree
from bzrlib.conflicts import ConflictList
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes
import config
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

        print "events handler: ",self.events_handler

    def _register_event(self, handler, evt):
        self.events_handler[handler] = evt

    def __call__(self, caller_event):
        file_name = caller_event.name

        if not self.bl_pattern.match(file_name):
            file_path = caller_event.path
            file_complete_name = file_name and os.path.join(file_path, file_name) or file_path

            #Calling the actual event
            events_name = caller_event.event_name.split("|")
            if len(events_name) == 3:
                event_type = events_name[0]
                handler_name = self.events_handler[event_type]
                getattr(self, handler_name)(event_type, file_complete_name)
            else:
                for event in events_name:
                    handler_name = self.events_handler[event]
                    getattr(self, handler_name)(event, file_complete_name)

    def _handle_update(self,event, file_name):
        #self.parent.upload_file(file_name)
        self.queue_.put((file_name,))

    def _handle_isdir(self,event, file_name):
        #Probably we only need to use smart add when it is a directory
        #self.parent.upload_file(file_name)
        pass

class Watcher(object):
    def __init__(self):
        configuration = config.get_config()
        self.working_path = configuration[LOCAL_FILES_DIR]

    def monitor(self, queue_):
        wm = WatchManager()
        notifier = Notifier(wm, Process(queue_))
        ec = EventsCodes
        wm.add_watch(self.working_path, ec.IN_CREATE|ec.IN_MODIFY|ec.IN_MOVED_FROM|ec.IN_ISDIR)
        #Need to add event ON_DELETE and MOVED_TO

        try:
            while True:
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            return
