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
""" Updater module handler for bazaar backend """

import config
import os, sys
import re
import time

from bzrlib import branch, errors
from bzrlib.conflicts import ConflictList
from bzrlib.lockdir import LockDir
from bzrlib.workingtree import WorkingTree
from fnmatch import translate

from filezaar.constants import *


class UpdaterBZR(object):
    def __init__(self):
        configuration = config.get_config()
        self.working_path = configuration[LOCAL_FILES_DIR]
        branch_uri_remote = configuration[REMOTE_REPOSITORY_URI]
        branch_uri_local = "".join(('file://', self.working_path))

        # During initialization we need to check if the repository and
        # local branch exists
        try:
            self.branch_remote = branch.Branch.open('%s' % branch_uri_remote)
        except Exception, e:
            print e
            sys.exit(1)

        # Check for local copy
        try:
            self.tree = WorkingTree.open(self.working_path)
            self.branch_local = branch.Branch.open(branch_uri_local)
        except errors.NotBranchError:
            print "please run setup.sh first to create the repository"
            #print "Creating local Branch"
            #self._create_local_branch(branch_uri_local)
            #self.tree = WorkingTree.open(self.working_path)
            #self.branch_local = branch.Branch.open(branch_uri_local)

    def _create_local_branch(self, branch_uri_local):
        local_branch = self.branch_remote.bzrdir.sprout( \
                       branch_uri_local).open_branch()


    def sync (self):
        """
        Synchronize working copy with repository and viceversa
        if remote respository does not exists yet, it creates it,
        and the same thing happens with the local copy
        """
        # First check if anything has been removed
        # Then add everything that is not already in the working copy
        self._add()
        # Commit Local changes
        self._commit("Adding files that were created, modified or deleted while filezaar was not running")
        # Merge with server files
        self._merge()
        # This commit should ocurred only if something was merged
        self._commit("Adding files that were created, modified or deleted while filezaar was not running")
        # Push everything back to the repository
        self._push()

    def upload_files(self, file_names):
        """Upload files and add them to the filezaar repository."""
        #lft = LockDir('sftp://skazaar@mislupins.com.ar/~/testp1/.bzr/branch/lock', 'breaklock')
        #lft.unlock()
        for file_name in file_names:
            print file_name
            try:
                self._add(file_name)
            except AssertionError:
                return
        try:
            self._commit("Adding %s" % file_name)
            self._merge()
            self._push()
            return True
        except:
            return False

    def _resolve_all(self):
        """Resolve some or all of the conflicts in a working tree."""
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
        except errors.NoCommits:
            pass

    def _pull(self):
        """
        Pull changes from remote repository
        """
        self.branch_local.pull(self.branch_remote)

    def _push(self):
        """Push the commited files to filezaar."""
        try:
            self.branch_local.push(self.branch_remote)
        except errors.DivergedBranches:
            self._merge()
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
        # It would be great if I could add all the files as binaries
        # but right now I don't know how to do it

        if file_name is not None:
            self.tree.smart_add(['%s' % (file_name)])
        else:
            self.tree.smart_add(['%s' % (self.working_path)])

    def _commit(self, commit_text):
        """Commit the changes to local repository."""
        try:
            self.tree.commit(commit_text)
        except errors.ConflictsInTree:
            self._resolve_all()
            self.tree.commit(commit_text)

    def _update(self):
        """update files."""
        self.tree.update()
