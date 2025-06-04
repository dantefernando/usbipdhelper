# Allow user to interactively connect and disconnect usb devices using usbipd
# Written by Dante Fernando

# TODO 
# - interactive support with arrow keys or vim keybinds
# - add exception for zero usb devices connected
# - add reconnect feature to device that is already connected

import pyuac  # for admin rights
import os # clear screen
from subprocess import check_output  # enter commands in powershell
from time import sleep


# WIP
def disconnect(device):
    os.system(f'powershell.exe usbipd unbind -b {device[0]}')
    sleep(1)



# WIP
def connect():

    # TODO connecting device:
    # - ssh into virtual machine
    # - get correct ethernet adapter ipv4 address of host machine get it from 'who' command
    # - enter that into ssh command 

    pass


def displayDevice(index):
    """
    Display device to user in a readable format 
    with BUSID, VID:PID, NAME AND STATE
    """

    raw = getRawDevices()
    print(f"\n{raw[1]}\n{raw[index+2]}\n")


def manageDevice(index):
    """
    Let user interactively Connect/Disconnect Device from usbipd
    """

    # TODO
    # - display device, show all info
    # - tell user if the device is currently connected or disconnected
    # - ask to (C)onnect or (D)isconnect device from session
    # add cases for 'Not shared', 'Shared' and Attached

    # TODO connecting device:
    # - ssh into virtual machine
    # - get correct ethernet adapter ipv4 address of host machine get it from 'who' command
    # - enter that into ssh command 

    # TODO disconnecting device:
    # unbind from powershell

    while True:

        device = getDevices()[index]  # return devices data as 2D array 

        displayDevice(index)

        # send a status to stdout
        if device[3] == "Not shared" or device[3] == "Shared":  # device is disconnected to VM
            print("Device is currently DISCONNECTED from the VM")
            inp = input("(C)onnect or Go (B)ack: ")

            if inp.lower() == "c" or inp.lower() == "connect":  # User wants to connect
                clear()
                print("Connecting...")
                connect(device)
            elif inp.lower() == "b" or inp.lower() == "back":  # User wants to go back to the dev menu
                clear()
                break
            else:  # invalid input
                clear()
                print("Invalid input")

        else:  # device is connected to VM
            print("Device is currently CONNECTED to the VM")
            inp = input("(D)isconnect, (R)econnect or Go (B)ack: ")

            if inp.lower() == "d" or inp.lower() == "disconnect":  # user wants to disconnect
                clear()
                print("Disconnecting...")
                disconnect(device)
            elif inp.lower() == "b" or inp.lower() == "back":  # user wants to go back
                clear()
                break
            # elif inp.lower() == "r" or inp.lower() == "reconnect":  # user wants to reconnect
            #     clear()
            #     disconnect(device)
            #     wait 5
            #     connect(device)
            else:  # user entered invalid input
                clear()
                print("Invalid input")


def clear():
    """
    Clear the console
    """
    os.system('cls')


def chooseDevice():
    """
    Let user connect/disconnect devices after displaying a list
    devices to choose from
    """

    while True:

        devices = getDevices()  # return devices data as 2D array 

        displayDevices()  # send formatted devices to stdout for user to choose from

        print("Select a device using the index under \"INDEX\"")

        inp = input(f"Index of Device to Connect/Disconnect (1-{len(devices)}) or (R)efresh devices: ")
        try:
            inp = int(inp)

            if 1 <= inp <= len(devices):  # int in range
                clear()
                manageDevice(inp-1)  # disconnect/connect device
            else:  # int out of range
                clear()
                print(f"\nEnter a valid index between 1 and {len(devices)}...\n")

        except ValueError:  # user entered a string
            if inp.lower() == "r" or inp.lower() == "refresh":  # str in range
                clear()
                print("Refreshed and Updating Devices...")
            else:  # str out of range
                clear()
                print(f"\nEnter a valid index between 1 and {len(devices)}...\n")


def displayDevices():
    """
    Display devices cleanly with indexes for user to choose from
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
                print(f"INDEX \t {line}")
            else:  # Print with index beside device
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
    Required for usbipd-win
    """

    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()


def main():
    """
    Main, calls all methods
    """

    runAdmin()  # run the script with admin rights

    chooseDevice()  # user chooses device to connect/disconnect


if __name__ == "__main__":
    main()

