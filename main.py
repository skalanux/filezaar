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
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes
from bzrlib import branch, errors
from bzrlib.workingtree import WorkingTree
from bzrlib.conflicts import ConflictList
from fnmatch import translate
#from filezaar.updater import Updater
import time

try:
    import pygtk
    pygtk.require('2.0')
    import pynotify
    pynotify.init('FileZaar')
    PYGTK_ENABLED = True
except:
    print "Pygtk is not available"
    PYGTK_ENABLED = False

#WORKING_PATH = '/home/ska/Skazar/projecttest1'
WORKING_PATH = os.getcwd()



BRANCH_URI_REMOTE = 'sftp://skazaar@mislupins.com.ar/~/testp1'
BRANCH_URI_LOCAL = "".join(('file://', WORKING_PATH))

class Updater(object):

    def __init__(self):
        self.tree = WorkingTree.open(WORKING_PATH)
        self.branch_local = branch.Branch.open(BRANCH_URI_LOCAL)
        self.branch_remote = branch.Branch.open('%s' % BRANCH_URI_REMOTE)

    def upload_file(self, file_name):
        """
        Uploads a file and it adds it to the skazaar server
        """
        try:
            self._add(file_name)
        except:
            print "File does not exists any more %s", file_name
            return

        #Poner los trys en las funciones ya que cada exception es unica a cada funcion

        self._commit("Adding %s" % file_name)
        self._push()
        noti = self._notify("Upload Completed:", "File  %s has been uploaded" % file_name)

       
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
        self.tree.merge_from_branch(self.branch_remote)

    def _notify(self, msg_title, msg_content):
        if PYGTK_ENABLED:
            noti = pynotify.Notification(msg_title,"%s" % msg_content)
            noti.show()
        else:
            print msg_title, msg_content

    def _pull(self):
        """
        Pull changes from remote repository
        """
        self.branch_local.pull(self.branch_remote)


    def _push(self):
        """
        Pushes the commited files to skazaar
        """
        try:
            self.branch_local.push(self.branch_remote)
        except errors.DivergedBranches:
            self._merge()
            self._notify("Branch Merged:", "Branch has been merged")
            self._push()

    def _add(self, file_name):
        #It would be great if I could add all the files as binaries
        #But right now I don't know how to doit
        self.tree.smart_add(['%s' % (file_name)])

    def _commit(self, commit_text):
        """
        Commits the changes to local repository
        """
        try:
            self.tree.commit(commit_text)
        except errors.ConflictsInTree:
            self._resolve_all() 
            self.tree.commit(commit_text)
            self._notify("Conflicts:", "Conflicts have been resolved")

    def _update(self):
        """
        update files
        """
        self.tree.update()

    def monitor(self):
        class Process(ProcessEvent):
       

            def __init__(self, parent):
                self.parent = parent
                BLACK_LISTED_FILE_TYPES = ('*.swp', '*.pepe')
                rx = '|'.join(translate(p) for p in BLACK_LISTED_FILE_TYPES)
                self.pattern = re.compile(rx)
                
                #Create Events handler
                self.events_handler = {}

                self._register_event('IN_CREATE', '_notify_update') 
                self._register_event('IN_MODIFY', '_notify_update') 
                self._register_event('IN_MOVED_FROM', '_notify_update') 

                print "events handler: ",self.events_handler
    
            def _register_event(self, handler, evt):
                self.events_handler[handler] = evt
     
            def __call__(self, event):
                file_name = event.name

                if not self.pattern.match(file_name):
                    file_path = event.path
                    event_type = event.event_name
                    handler_name = self.events_handler[event_type]

                    file_complete_name = file_name and os.path.join(file_path, file_name) or file_path

                    #Calling the actual event
                    getattr(self, handler_name)(event, file_complete_name)

            def _notify_update(self,event, file_name):
                self.parent.upload_file(file_name)

 
        wm = WatchManager()
        notifier = Notifier(wm, Process(self))
        ec = EventsCodes
        wm.add_watch(WORKING_PATH, ec.IN_CREATE|ec.IN_MODIFY|ec.IN_MOVED_FROM)
        #Need to add event ON_DELETE and MOVED_TO
    
        try:
            while True:
                #time.sleep(2)
                #self._update()
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            return

if __name__ == '__main__':
    filezaar = Updater()
    filezaar.monitor()
