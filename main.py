# Allow user to interactively connect and disconnect usb devices using usbipd

import pyuac  # for admin rights
from subprocess import check_output  # enter commands in powershell
from argparse import ArgumentParser # CLI help


HELP_NOTICE = """CLI tool that helps automate connect and disconnect process for USB devices
                using usbipd on windows.  You'll no longer have to keep reaching over your
                desk to physically unplug and replug usb devices when messing around with
                virtual machines that require you to do so."""


def getDevices():
    """
    Get device information from 'usbipd list' command, format it and return it
    in an array for parsing
    """

    raw = check_output("powershell.exe usbipd list", shell=True).decode().splitlines()
    raw.pop(0)
    raw.pop(0)

    # Loop through all lines from 'usbipd list' output
    # and split each word and append into 2d array
    devicesRaw = []
    for i in range(0, len(raw)):
        line = raw[i].split()
        if len(line) != 0: # if line is not a newline
            if line[0] == "Persisted:":  # don't add persisted devices
                break
            else:
                devicesRaw.append(line)

    # Create clean device list to use later for automation and stdout
    devicesClean = []
    for line in devicesRaw:
        device = []  # append all formatted device info into device array
        device.append(line[0])  # append BUSID
        device.append(line[1])  # append VID:PID

        if line[-1] == "shared":  # State is 'Not shared'
            device.append(' '.join(line[2:-2]))  # append DEVICE NAME
            device.append(' '.join(line[-2:]))  # append STATE

        else:  # State is either 'Attached' or 'Shared'
            device.append(' '.join(line[2:-1]))  # append DEVICE NAME
            device.append(line[-1])  # append STATE

        devicesClean.append(device)

    return devicesClean  # return array of cleanly formatted devices ready for automation


def runAdmin():
    """
    Prompt the user to run the script with Admin Rights.
    Required for usbipd
    """

    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()


def main():
    """
    Main, calls all methods
    """

    runAdmin()  # run the script with admin rights

    # if firstTime():  # user's first time running script
    #     createSettings()   # create persistent settings files

    devices = getDevices()

    # displayDevices(devices)  # send formatted devices to stdout for user to choose from

    for device in devices:
        print(device)



if __name__ == "__main__":
    main()

