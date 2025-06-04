# Allow user to interactively connect and disconnect usb devices using usbipd

import pyuac  # for admin rights
from subprocess import check_output  # enter commands in powershell


def displayDevices(devices):
    """
    Display devices formatted cleanly for user to choose from
    """
    raw = getRawDevices()  # get raw output of devices to display to user

    endOfDevices = False  # End of connected devices
    for index, line in enumerate(raw):  # loop thru all lines

        if len(line) == 0:  # Reached end of devices
            endOfDevices = True

        if not endOfDevices:  # Device is connected
            if index == 0:
                print(f"Connected Devices:\n") 
            elif index == 1:
                print(f"SELECT \t {line}")
            else:
                print(f"{index-1}) \t {line}")
        else:  # Disconnected device
            print(line)


def getRawDevices():
    """
    Return raw output of usbipd list command
    """
    return check_output("powershell.exe usbipd list", shell=True).decode().splitlines()


def getDevices():
    """
    Get device information from 'usbipd list' command, format it and return it
    in an array for parsing
    """

    raw = getRawDevices()
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
            else:  # device is currently connected 
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

    devices = getDevices()

    displayDevices(devices)  # send formatted devices to stdout for user to choose from


if __name__ == "__main__":
    main()

