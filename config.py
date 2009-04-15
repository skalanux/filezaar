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

import ConfigParser

cp = ConfigParser.ConfigParser()
cp.read('config.inc')
section = 'main'

def get_config():
    working_path = cp.get(section, 'working_path')
    branch_uri_remote = cp.get(section, 'branch_uri_remote')
    branch_uri_local = "".join(('file://', working_path))
    return locals()
