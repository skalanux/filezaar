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
import ConfigParser

cp = ConfigParser.ConfigParser()
home_dir = os.getenv("HOME")
path_config_file = "/".join((home_dir,'.filezaarrc'))
cp.read(path_config_file)
section = 'main'

def get_config():
    local_files_dir = cp.get(section, 'local_files_dir')
    remote_repository_uri = cp.get(section, 'remote_repository_uri')
    return locals()
