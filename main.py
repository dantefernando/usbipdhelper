# Allow user to interactively connect and disconnect usb devices using usbipd

import pyuac  # for admin rights
from subprocess import check_output  # enter commands in powershell


# Get the devices and store it in a list
def getDevices():
    raw = check_output("powershell.exe usbipd list", shell=True).decode().splitlines()
    raw.pop(0)
    raw.pop(0)

    # Loop through all lines from 'usbipd list' output
    # and split each word and append into 2d array
    devicesRaw = []
    for i in range(0, len(raw)):
        line = raw[i].split()
        if len(line) != 0: # if line is not a newline
            if line[0] != "Persisted:" and line[0] != "GUID":
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

    for line in devicesClean:
        print(line)


# Ask the user to run the script with admin rights
def runAdmin():
    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()


def main():
    runAdmin()
    getDevices()


if __name__ == "__main__":
    main()
