import dbus

bus = dbus.SessionBus()
filezaar = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
filezaar = bus.get_object('org.filezaar.daemon', '/org/filezaar/daemon')
daemon = dbus.Interface(filezaar, 'org.filezaar.daemon')
print daemon.Hello()
#print daemon.Sync()
