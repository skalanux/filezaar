#!/usr/bin/env python
import sys
import gtk
import gobject
import dbus
import dbus.service
import getopt
import os
from dbus.mainloop.glib import DBusGMainLoop

import config
from filezaar.constants import *


DBusGMainLoop(set_as_default=True)
bus = None
daemon = None



class TrayIcon(object):
    """ Base Tray Icon class.
    
    Base Class for implementing a tray icon to display network status.
    
    """
    def __init__(self):
        self.tr = self.StatusTrayIconGUI()
        self.icon_info = self.TrayConnectionInfo(self.tr)
        
    def is_embedded(self):
        return self.tr.is_embedded()

    class TrayConnectionInfo(object):
        """ Class for updating the tray icon status. """
        def __init__(self, tr):
            """ Initialize variables needed for the icon status methods.
            """
            self.tr = tr
            #noti = pynotify.Notification("Upload in progress:", "File  %s is being uploaded" % file_name)
            #noti.set_timeout(0)
            #noti.show()
            #self._push()
            #noti.update("Upload Completed:", "File  %s has been uploaded" % file_name)
            #noti.set_timeout(pynotify.EXPIRES_DEFAULT)
            #noti.show()
            self.update_system_state()
            
        def set_idle_state(self, info):
            """ Sets the icon info for a wired state. """
            noti = pynotify.Notification("Updated", "FileZaar is uptodate")

            self.tr.set_tooltip('FileZaar is uptodate')
            self.tr.set_from_file(PATH_IMAGES + "filezaar_uptodate.png")
            noti.show()
    
        def set_syncing_state(self, info):
            """ Sets the icon info for a connecting state. """
            file_name = "xx"
            noti = pynotify.Notification("Synchronizing", 
                                         "FileZaar is synchronizing "
                                         "files with remote repository")
            self.tr.set_tooltip("FileZaar is synchronizing files")
            self.tr.set_from_file(PATH_IMAGES + "filezaar_sync.png")
            noti.show()

        def set_uploading_state(self, info):
            """ Sets the icon info for a connecting state. """
            file_name = "xx"
            noti = pynotify.Notification("Updating Files", 
                                         "FileZaar is uploading  %s" 
                                         % file_name)
            self.tr.set_tooltip("FileZaar is updating files")
            self.tr.set_from_file(PATH_IMAGES + "filezaar_sync.png")
            noti.show()

        def dummy_receive_signal_1(self, status, info):
            print status, info

        def update_system_state(self, state=None, info=None):
            """ Updates the tray icon and show notifications"""

            if not state or not info:
                [state, info] = daemon.GetFileZaarStatus()
 
            if state in (STATUS_PULLING, STATUS_PUSHING, 
                         STATUS_UPDATING):
                self.set_syncing_state(info)
            elif state == STATUS_IDLE:
                self.set_idle_state(info)
            else:
                print 'Invalid state returned!!!'
                return False
            return True

    class TrayIconGUI(object):
        """ Base Tray Icon UI class.
        
        Implements methods and variables used by 
        tray icon.

        """
        def __init__(self):
            menu = """
                    <ui>
                    <menubar name="Menubar">
                    <menu action="Menu">
                    <menuitem action="Synchronize"/>
                    <separator/>
                    <menuitem action="About"/>
                    <menuitem action="Quit"/>
                    </menu>
                    </menubar>
                    </ui>
            """
            actions = [
                    ('Menu',  None, 'Menu'),
                    ('Synchronize', gtk.STOCK_CONNECT, '_Synchronize..', None,
                     'Synchronize FileZaar with remote repository', self.on_synchronize),
                    ('About', gtk.STOCK_ABOUT, '_About...', None,
                     'About filezaar-tray-icon', self.on_about),
                    ('Quit',gtk.STOCK_QUIT,'_Quit',None,'Quit FileZaar Tray Icon',
                     self.on_quit),
                    ]

            actg = gtk.ActionGroup('Actions')
            actg.add_actions(actions)
            self.manager = gtk.UIManager()
            self.manager.insert_action_group(actg, 0)
            self.manager.add_ui_from_string(menu)
            self.menu = (self.manager.get_widget('/Menubar/Menu/About').
                                                                  props.parent)
            self.gui_win = None
            self.current_icon_path = None

        def on_activate(self, data=None):
            """ Opens nautilus folder """
            self.show_nautilus_filezaar_folder()
    
        def on_synchronize(self, data=None):
            """ Force synchronization of Filezaar """
            daemon.EmitRequestSync()

        def on_quit(self, widget=None):
            """ Closes the tray icon. """
            sys.exit(0)

        def on_about(self, data=None):
            """ Opens the About Dialog. """
            dialog = gtk.AboutDialog()
            dialog.set_name('FileZaar Tray Icon')
            dialog.set_version('0.1')
            dialog.set_comments('This icon controls FileZaar and show it status')
            dialog.set_website('http://filezaar.com.ar')
            dialog.run()
            dialog.destroy()

        def show_nautilus_filezaar_folder(self):
            """ Opens Nautilus. 
                It would be great if we could use DBUS , 
                but it seems like Those Features are 
                not present at the moment
            """
            print "open nautilus"
 
    class StatusTrayIconGUI(gtk.StatusIcon, TrayIconGUI):
        """ Class for creating the FileZaar tray icon on gtk > 2.10.
        """

        def __init__(self):
            TrayIcon.TrayIconGUI.__init__(self)

            gtk.StatusIcon.__init__(self)

            self.current_icon_path = ''
            self.set_visible(True)
            self.connect('activate', self.on_activate)
            self.connect('popup-menu', self.on_popup_menu)
            self.set_from_file(PATH_IMAGES + "no-signal.png")
            self.set_tooltip("Initializing filezaar...")

        def on_popup_menu(self, status, button, timestamp):
            """ Opens the right click menu for the tray icon. """
            self.menu.popup(None, None, None, button, timestamp)

        def set_from_file(self, path = None):
            """ Sets a new tray icon picture. """
            if path != self.current_icon_path:
                self.current_icon_path = path
                gtk.StatusIcon.set_from_file(self, path)


# Module main methods 
def connect_to_dbus():
    global bus, daemon
    # Connect to the daemon
    bus = dbus.SessionBus()
    try:
        print 'Attempting to connect tray to daemon...'
        proxy_obj = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
        print 'Success.'
    except dbus.DBusException:
        print "Can't connect to the daemon, trying to start it automatically..."
        try:
            print 'Attempting to connect tray to daemon...'
            proxy_obj = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
            print 'Success.'
        except dbus.DBusException:
            print ("Could not connect to filezaar D-Bus interface.  " +
                      "Make sure the daemon is started.")
            sys.exit(1)
    
    daemon = dbus.Interface(proxy_obj, 'org.filezaar.daemon')
    return True

def main(argv):
    """ The main frontend program.
    """
    connect_to_dbus()

    # Set up the tray icon GUI and backend
    tray_icon = TrayIcon()

    bus.add_signal_receiver(tray_icon.icon_info.update_system_state,
                            'StatusChanged', 'org.filezaar.daemon')

    #bus.add_signal_receiver(tray_icon.icon_info.dummy_receive_signal_1,
    #                        'RequestSync', 'org.filezaar.daemon')

    mainloop = gobject.MainLoop()
    mainloop.run()

if __name__ == '__main__':
    main(sys.argv)
