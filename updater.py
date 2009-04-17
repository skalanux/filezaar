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

import os, sys
import re
from fnmatch import translate
import time
import threading
import Queue
from bzrlib import branch, errors
from bzrlib.workingtree import WorkingTree
from bzrlib.conflicts import ConflictList
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes
import config
from filezaar.constants import *

class QueueManager(threading.Thread):
    """
    This class is on charge of processing incoming upload/synchronizing
    requests, the files on the queue should have a priprity so they can
    be process according to it, this could be achived using weigths
    according to a specific critery
    """
    def __init__(self, parent):
        self.parent = parent
        self.queue_ = parent.queue_
        threading.Thread.__init__(self)

    def run(self):
        while True:
            data = self.queue_.get()
            print "mandadno a subir data %s" % data[0]
            self.parent.upload_file(data[0])

class Process(ProcessEvent):
    """
    Class that process events as they ocurred
    """
    def __init__(self, parent):
        self.parent = parent
        BLACK_LISTED_FILE_TYPES = ('*.swp', '*.pepe')
        rx = '|'.join(translate(p) for p in BLACK_LISTED_FILE_TYPES)
        self.pattern = re.compile(rx)
        
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

        if not self.pattern.match(file_name):
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
        #self.parent.upload_file(file_name)
        self.parent.queue_.put((file_name,))

    def _handle_isdir(self,event, file_name):
        #Probably we only need to use smart add when it is a directory
        #self.parent.upload_file(file_name)
        pass

class Updater(object):
    def __init__(self):
        self.queue_ = Queue.Queue()
        self.queue_manager = QueueManager(self)
        self.queue_manager.start()
        configuration = config.get_config()
        branch_uri_local = configuration['branch_uri_local']
        branch_uri_remote = configuration['branch_uri_remote']
        self.working_path = configuration['working_path']
        self.tree = WorkingTree.open(self.working_path)
        self.branch_local = branch.Branch.open(branch_uri_local)
        self.branch_remote = branch.Branch.open('%s' % branch_uri_remote)
        self.sync()

    def sync (self):
        """
        Synchronize working copy with repository and viceversa
        """
        #First check if anything has been removed
        #Then add everything that is not already in the working copy
        noti = pynotify.Notification("Synchronizing files:", "synchronizing files")
        noti.set_timeout(0)
        noti.show()
        self._add()
        #Commit Local changes
        self._commit("Adding files that were created, modified or deleted while filezaar was not running")
        #Merge with server files
        self._merge()
        #This commit should ocurred only if something was merged
        self._commit("Adding files that were created, modified or deleted while filezaar was not running")
        #Push everything to the repository
        self._push()
        noti.update("Synchronization complete:", "Files have been synchronized with remote repository")
        noti.set_timeout(pynotify.EXPIRES_DEFAULT)
        noti.show()


    def upload_file(self, file_name):
        """
        Uploads a file and it adds it to the filezaar
        """
        #Still need to add locking mechanisims to avoid files not being updated

        try:
            self._add(file_name)
        except AssertionError:
            return
        try:
            self._commit("Adding %s" % file_name)
            self._merge()
            noti = pynotify.Notification("Upload in progress:", "File  %s is being uploaded" % file_name)
            noti.set_timeout(0)
            noti.show()
            self._push()
            noti.update("Upload Completed:", "File  %s has been uploaded" % file_name)
            noti.set_timeout(pynotify.EXPIRES_DEFAULT)
            noti.show()
        except:
            noti.update("Upload has failed:", "There was a problem trying to upload %s" % file_name)
            noti.set_timeout(pynotify.EXPIRES_DEFAULT)
            noti.show()

    def _resolve_all(self):
        """Resolve some or all of the conflicts in a working tree.
        """
        tree = self.tree
        tree.lock_tree_write()
        try:
            tree_conflicts = tree.conflicts()
            new_conflicts = ConflictList()
            selected_conflicts = tree_conflicts
            try:
                tree.set_conflicts(new_conflicts)
            except errors.UnsupportedOperation:
                pass
            selected_conflicts.remove_files(tree)
        finally:
            tree.unlock()
    

    def _merge(self):
        try:
            self.tree.merge_from_branch(self.branch_remote)
        except errors.PointlessMerge:
            pass

    def _pull(self):
        """
        Pull changes from remote repository
        """
        self.branch_local.pull(self.branch_remote)

    def _push(self):
        """
        Pushes the commited files to filezaar
        """
        try:
            self.branch_local.push(self.branch_remote)
        except errors.DivergedBranches:
            self._merge()
            noti = pynotify.Notification("Branch Merged:", "Branch has been merged")
            noti.set_timeout(0)
            self.branch_local.push(self.branch_remote)
            self._push()
            noti.show()
        except errors.UncommittedChanges:
            self._commit("Adding uncommited changes")
            self._push()
        except Exception, e :
            print e


    def _add(self, file_name=None):
        #It would be great if I could add all the files as binaries
        #But right now I don't know how to do it
        if file_name is not None:
            self.tree.smart_add(['%s' % (file_name)])
        else:
            self.tree.smart_add(['%s' % (self.working_path)])

    def _commit(self, commit_text):
        """
        Commits the changes to local repository
        """
        try:
            self.tree.commit(commit_text)
        except errors.ConflictsInTree:
            self._resolve_all() 
            self.tree.commit(commit_text)

    def _update(self):
        """
        update files
        """
        self.tree.update()

    def monitor(self):

        wm = WatchManager()
        notifier = Notifier(wm, Process(self))
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
