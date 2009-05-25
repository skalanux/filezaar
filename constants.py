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



import os
import re
from fnmatch import translate
try:
    import pygtk
    pygtk.require('2.0')
    import pynotify
    pynotify.init('FileZaar')
    PYGTK_ENABLED = True
except:
    print "Pygtk is not available"
    PYGTK_ENABLED = False

STATUS_UPDATING = 100
STATUS_PULLING = 200
STATUS_PUSHING = 300
STATUS_IDLE = 400
PATH_IMAGES = './resources/'
LOCAL_FILES_DIR = 'local_files_dir'
REMOTE_REPOSITORY_URI = 'remote_repository_uri'

# Black Listed File Types
BLACK_LISTED_FILE_TYPES = ('*.swp', '*.pepe')
rx = '|'.join(translate(p) for p in BLACK_LISTED_FILE_TYPES)
BLACK_LISTED_FILE_PATTERN = re.compile(rx)

