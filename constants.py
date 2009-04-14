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
import os
try:
    import pygtk
    pygtk.require('2.0')
    import pynotify
    pynotify.init('FileZaar')
    PYGTK_ENABLED = True
except:
    print "Pygtk is not available"
    PYGTK_ENABLED = False

WORKING_PATH = '/home/user/filezaar'                #This is where you downloaded 
                                                    #the branch to

BRANCH_URI_REMOTE = 'sftp://user@server/~/branch'   #is not necessary for this
                                                    #to be an sftp server,
                                                    #it could be any supported
                                                    #protocol,with read and write
                                                    #capabilities you can even use
                                                    #Launchpad or similar for
                                                    #this, altough I don't know If
                                                    #that is allowed. If you are
                                                    #testing it can also be a
                                                    #local branch.

BRANCH_URI_LOCAL = "".join(('file://', WORKING_PATH))
