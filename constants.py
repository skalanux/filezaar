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

try:
    import pygtk
    pygtk.require('2.0')
    import pynotify
    pynotify.init('FileZaar')
    PYGTK_ENABLED = True
except:
    print "Pygtk is not available"
    PYGTK_ENABLED = False

#WORKING_PATH = '/home/ska/Skazar/projecttest1/testp1'
WORKING_PATH = '/home/ska/Skazar/projecttest2'

#WORKING_PATH = os.getcwd()

BRANCH_URI_REMOTE = 'sftp://skazaar@mislupins.com.ar/~/testp1'
BRANCH_URI_LOCAL = "".join(('file://', WORKING_PATH))
