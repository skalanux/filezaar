#!/usr/bin/env python


import sys
import gtk
import gobject
import dbus
import dbus.service
import getopt
import os

from filezaar.constants import *

ICON_AVAIL = True

if getattr(dbus, 'version', (0, 0, 0)) < (0, 80, 0):
    import dbus.glib
else:
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

bus = None
daemon = None
wireless = None
wired = None
wired = None
config = None

class FileZaarPath(object):
    images = './resources/'
 



class TrayIcon(object):
    """ Base Tray Icon class.
    
    Base Class for implementing a tray icon to display network status.
    
    """
    def __init__(self, use_tray, animate):
        self.tr = self.StatusTrayIconGUI(use_tray)
        self.icon_info = self.TrayConnectionInfo(self.tr, use_tray, animate)
        
    def is_embedded(self):
        return self.tr.is_embedded()
        

    class TrayConnectionInfo(object):
        """ Class for updating the tray icon status. """
        def __init__(self, tr, use_tray=True, animate=True):
            """ Initialize variables needed for the icon status methods. """
            self.last_strength = -2
            self.still_wired = False
            self.network = ''
            self.tried_reconnect = False
            self.connection_lost_counter = 0
            self.tr = tr
            self.use_tray = use_tray
            self.last_sndbytes = -1
            self.last_rcvbytes = -1
            self.max_snd_gain = 10000
            self.max_rcv_gain = 10000
            self.animate = animate
            self.update_tray_icon()

            
        def set_idle_state(self, info):
            """ Sets the icon info for a wired state. """
            self.tr.set_from_file(FileZaarPath.images + "filezaar_uptodate.png")
            self.tr.set_tooltip(info)
            
        def set_syncing_state(self, info):
            """ Sets the icon info for a connecting state. """
            if info[0] == 'wired' and len(info) == 1:
                cur_network = language['wired']
            else:
                cur_network = info[1]
            self.tr.set_tooltip(language['connecting'] + " to " + 
                                cur_network + "...")
            self.tr.set_from_file(FileZaarPath.images + "no-signal.png")  
            
        def set_not_connected_state(self, info):
            """ Set the icon info for the not connected state. """
            self.tr.set_from_file(FileZaarPath.images + "no-signal.png")
            if wireless.GetKillSwitchEnabled():
                status = (language['not_connected'] + " (" + 
                         language['killswitch_enabled'] + ")")
            else:
                status = language['not_connected']
            self.tr.set_tooltip(status)

        def update_tray_icon(self, state=None, info=None):
            """ Updates the tray icon and current connection status. """
            if not self.use_tray: return False

            if not state or not info:
                [state, info] = daemon.GetFileZaarStatus()
           
            
 
            if state in (STATUS_PULLING, STATUS_PUSHING, STATUS_UPDATING):
                self.set_syncing_state(info)
            elif state == STATUS_IDLE:
                self.set_idle_state(info)
            else:
                print 'Invalid state returned!!!'
                return False
            return True

        def set_signal_image(self, wireless_signal, lock):
            """ Sets the tray icon image for an active wireless connection. """
            if self.animate:
                prefix = self.get_bandwidth_state()
            else:
                prefix = ''
            if daemon.GetSignalDisplayType() == 0:
                if wireless_signal > 75:
                    signal_img = "high-signal"
                elif wireless_signal > 50:
                    signal_img = "good-signal"
                elif wireless_signal > 25:
                    signal_img = "low-signal"
                else:
                    signal_img = "bad-signal"
            else:
                if wireless_signal >= -60:
                    signal_img = "high-signal"
                elif wireless_signal >= -70:
                    signal_img = "good-signal"
                elif wireless_signal >= -80:
                    signal_img = "low-signal"
                else:
                    signal_img = "bad-signal"

            img_file = ''.join([FileZaarPath.images, prefix, signal_img, lock, ".png"])
            self.tr.set_from_file(img_file)
            


    class TrayIconGUI(object):
        """ Base Tray Icon UI class.
        
        Implements methods and variables used by both egg/StatusIcon
        tray icons.

        """
        def __init__(self, use_tray):
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
                     'Connect to network', self.on_preferences),
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
            self.use_tray = use_tray

        def on_activate(self, data=None):
            """ Opens the wicd GUI. """
            self.show_nautilus_filezaar_folder()

        def on_quit(self, widget=None):
            """ Closes the tray icon. """
            sys.exit(0)

        def on_preferences(self, data=None):
            """ Opens the wicd GUI. """
            self.show_nautilus_filezaar_folder()

        def on_about(self, data=None):
            """ Opens the About Dialog. """
            dialog = gtk.AboutDialog()
            dialog.set_name('FileZaar Tray Icon')
            # VERSIONNUMBER
            dialog.set_version('0.1')
            dialog.set_comments('This icon controls FileZaar and show it status')
            dialog.set_website('http://filezaar.com.ar')
            dialog.run()
            dialog.destroy()

        def show_nautilus_filezaar_folder(self):
            """ Opens Nautilus. 
                It would be great to use DBUS , but it seems like
                Those Features are not present at the moment
            """
            if not self.gui_win:
                self.gui_win = gui.appGui()
                bus.add_signal_receiver(self.gui_win.dbus_scan_finished,
                                        'SendEndScanSignal',
                                        'org.filezaar.daemon')
                bus.add_signal_receiver(self.gui_win.dbus_scan_started,
                                        'SendStartScanSignal',
                                        'org.filezaar.daemon')
                bus.add_signal_receiver(self.gui_win.update_connect_buttons,
                                        'StatusChanged', 'org.filezaar.daemon')
            elif not self.gui_win.is_visible:
                self.gui_win.show_win()
            else:
                self.gui_win.exit()
                return True
        
    if hasattr(gtk, "StatusIcon"):
        class StatusTrayIconGUI(gtk.StatusIcon, TrayIconGUI):
            """ Class for creating the FileZaar tray icon on gtk > 2.10.
            
            Uses gtk.StatusIcon to implement a tray icon.
            
            """
            def __init__(self, use_tray=True):
                TrayIcon.TrayIconGUI.__init__(self, use_tray)
                self.use_tray = use_tray
                self.use_tray = True
                if not use_tray: 
                    self.show_nautilus_filezaar_folder()
                    return
    
                gtk.StatusIcon.__init__(self)
    
                self.current_icon_path = ''
                self.set_visible(True)
                self.connect('activate', self.on_activate)
                self.connect('popup-menu', self.on_popup_menu)
                self.set_from_file(FileZaarPath.images + "no-signal.png")
                self.set_tooltip("Initializing wicd...")
    
            def on_popup_menu(self, status, button, timestamp):
                """ Opens the right click menu for the tray icon. """
                self.menu.popup(None, None, None, button, timestamp)
    
            def set_from_file(self, path = None):
                """ Sets a new tray icon picture. """
                if not self.use_tray: return
                if path != self.current_icon_path:
                    self.current_icon_path = path
                    gtk.StatusIcon.set_from_file(self, path)


def usage():
    # VERSIONNUMBER
    """ Print usage information. """
    print """
wicd 1.5.9
wireless (and wired) connection daemon front-end.

Arguments:
\t-n\t--no-tray\tRun wicd without the tray icon.
\t-h\t--help\t\tPrint this help information.
\t-a\t--no-animate\tRun the tray without network traffic tray animations.
"""
    
def connect_to_dbus():
    global bus, daemon, wireless, wired, config
    # Connect to the daemon
    bus = dbus.SessionBus()
    try:
        print 'Attempting to connect tray to daemon...'
        proxy_obj = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
        print 'Success.'
    except dbus.DBusException:
        print "Can't connect to the daemon, trying to start it automatically..."
        #constants.PromptToStartDaemon()
        try:
            print 'Attempting to connect tray to daemon...'
            proxy_obj = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
            print 'Success.'
        except dbus.DBusException:
            gui.error(None, "Could not connect to wicd's D-Bus interface.  " +
                      "Make sure the daemon is started.")
            sys.exit(1)
    
    daemon = dbus.Interface(proxy_obj, 'org.filezaar.daemon')
    return True

def main(argv):
    """ The main frontend program.

    Keyword arguments:
    argv -- The arguments passed to the script.

    """
    use_tray = True
    animate = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'nha', ['help', 'no-tray',
                                                         'no-animate'])
    except getopt.GetoptError:
        # Print help information and exit
        usage()
        sys.exit(2)

    for opt, a in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-n', '--no-tray'):
            use_tray = False
        elif opt in ('-a', '--no-animate'):
            animate = False
        else:
            usage()
            sys.exit(2)
    
    print 'Loading...'
    connect_to_dbus()

    if not use_tray or not ICON_AVAIL:
        the_gui = gui.appGui()
        the_gui.standalone = True
        mainloop = gobject.MainLoop()
        mainloop.run()
        sys.exit(0)

    # Set up the tray icon GUI and backend
    tray_icon = TrayIcon(use_tray, animate)

    #bus.add_signal_receiver(tray_icon.icon_info.wired_profile_chooser,
    #                        'LaunchChooser', 'org.filezaar.daemon')

    bus.add_signal_receiver(tray_icon.icon_info.update_tray_icon,
                            'StatusChanged', 'org.filezaar.daemon')
    print 'Done.'
    mainloop = gobject.MainLoop()
    mainloop.run()


if __name__ == '__main__':
    main(sys.argv)
