import xbmcaddon
import xbmcgui
import xbmc

import time
import platform
import usb.core
import usb.util


#Globals
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
icon        = addon.getAddonInfo('icon')
usbbutton   = None

class ButtonState(object):
    (ButtonUp, ButtonDown, Unknown) = range(3)

class CoverState(object):
    (LidOpen, LidClosed, Unknown) = range(3)

def usb_setup():

    global usbbutton

    try:
        # Get USB device by vendor and product ID
        usbbutton = usb.core.find(idVendor= 0x1D34, idProduct=0x000D)
    except usb.core.NoBackendError:
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30009), 500, icon))
        return False

    # Device connected? Show notification: "Device connected"
    if usbbutton is not None:
        if addon.getSetting("notify_device_evts") == "true":
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30005), 500, icon))

        try:

            # On Linux we need to detach usb HID first
            if "Linux" == platform.system():
                try:
                    DEVICE.detach_kernel_driver(0)
                except Exception, e:
                    pass # already unregistered

            # set the active configuration. With no arguments, the first
            # configuration will be the active one
            if usbbutton is not None:
               usbbutton.set_configuration()

        except Exception, e:
            #Log Error
            print addonname + ": " + str(e)
            #Set device to none so we can search again for it later
            usbbutton = None

    #works
    #xbmcgui.Dialog().ok(addonname, usbbutton.product, "", "")
    #xbmcgui.Dialog().ok(addonname, usbbutton.manufacturer, "", "")
    #xbmcgui.Dialog().ok(addonname, usbbutton.serial_number, "", "")

    return True

def usb_cmd():

    global usbbutton

    try:
        # dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, length_or_data)
        written = usbbutton.ctrl_transfer(0x21, 0x9, 0x0200, 0x0, [0,0,0,0,0,0,0,2])
        #read the data
        data = usbbutton.read(0x81, 8)
    except Exception, e:
        #Whoops something went wrong, probably disconnected
        print addonname + ": " + str(e)
        #Set device to none so we can search again for it later
        usbbutton = None

        if addon.getSetting("notify_device_evts") == "true":
            #Show notification: "Device disconnected"
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname,addon.getLocalizedString(30006), 1000, icon))

        return ButtonState.Unknown, CoverState.Unknown
    else:

        #Bit 0; 0 = Button pressed
        #Bit 0; 1 = Button not pressed
        if data[0] & 0x01:
            state_btn = ButtonState.ButtonUp
        else:
            state_btn = ButtonState.ButtonDown

        #Bit 1; 0 = Lid closed
        #Bit 1; 1 = Lid opened
        if data[0] & 0x02:
            state_cover = CoverState.LidOpen
        else:
            state_cover = CoverState.LidClosed

        return state_btn, state_cover

def main():

    if addon.getSetting("notify_start_stop_evts") == "true":
        #Show notification: "Service started"
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname,addon.getLocalizedString(30008), 1000, icon))

    #Set the initial states to unknown
    current_state_cover   = CoverState.Unknown
    current_state_btn   = ButtonState.Unknown

    #Search for devices at startup, if the function fails then there is no backend
    #So no reason to continue this service
    if usb_setup() is True:

        monitor = xbmc.Monitor()
        while not monitor.abortRequested():

            #Do we have a connected device?
            if usbbutton is not None:

                #Get the current state
                new_state_btn, new_state_cover = usb_cmd()

                #Check if the button state is changed compared to the previous check
                if current_state_btn <> ButtonState.Unknown and new_state_btn <> ButtonState.Unknown:
                    if current_state_btn <> new_state_btn:
                        if new_state_btn == ButtonState.ButtonDown:

                            if addon.getSetting("notify_button_evts") == "true":
                                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30003), 500, icon))

                            #Play/Pause
                            xbmc.executebuiltin('Action(%s)'%("PlayPause"))

                        else:

                            if addon.getSetting("notify_button_evts") == "true":
                                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30004), 500, icon))

                #Check if the cover state is changed compared to the previous check
                if current_state_cover <> CoverState.Unknown and new_state_cover <> CoverState.Unknown:
                    if current_state_cover <> new_state_cover:
                        if new_state_cover == CoverState.LidOpen:
                            if addon.getSetting("notify_cover_evts") == "true":
                                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30001), 500, icon))
                        else:
                            if addon.getSetting("notify_cover_evts") == "true":
                                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30002), 500, icon))

                        #Show Info
                        #xbmc.executebuiltin('Action(%s)'%("Info"))

                #save current states
                current_state_cover = new_state_cover
                current_state_btn = new_state_btn

                #sleep for 200 ms
                time.sleep(0.200)

            else:

                #sleep for 5 seconds
                time.sleep(5)

                #check if usb device is present
                usb_setup()

    if addon.getSetting("notify_start_stop_evts") == "true":
        #Show notification: "Service stopped"
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, addon.getLocalizedString(30007), 1000, icon))

    #we are done here
    sys.exit(1)

if __name__ == "__main__":
    main()