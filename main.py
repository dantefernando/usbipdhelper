# Allow user to interactively connect and disconnect usb devices using usbipd
# Written by Dante Fernando

# Urgent TODO 
# - getRawIP() should automatically figure out which ethernet adapter to look for
# - connect() should automatically figure out the VM's ip for SSH
# - connect() should ask for password from user and store it somewhere
# - Check if username, password, adapters and virtual machine IP are all correct
# - Add Quit option to devices menu

# Not urgent TODO
# - interactive support with arrow keys or vim keybinds
# - add exception for zero usb devices connected

import paramiko  # for ssh # pip install
import pyuac  # for admin rights # pip install
import os # clear screen
from subprocess import check_output  # enter commands in powershell
from time import sleep

# TODO automate all these 
# CHANGE THESE FOUR VARS BELOW FOR YOUR SYSTEM
USERNAME = "nexus"  # username for ssh
PASSWORD = "1234"  # password for ssh
ADAPTER = "vEthernet (Default Switch)"  # Virtual Adapter Name, check ipconfig e.g. "vEthernet (Default Switch)
VIRTUAL_MACHINE_IP = "172.28.53.30"  # VM ip, find ip in virtual machine using `ip a` command e.g. 172.28.53.30


def disconnect(device):
    """
    Disconnect the USB device from VM
    """

    busID = device[0]

    os.system(f'powershell.exe usbipd unbind -b {busID}')  # unbind device from host
    print(f"Device: {device[2]} disconnected!")
    sleep(1.5)


def getRawIP():
    """
    Return raw info output of netsh command
    """

    # Get network adapter raw output from netsh
    # TODO make it automatically look for this adapter
    return check_output(f"netsh interface ip show addresses \"{ADAPTER}\"", shell=True).decode().splitlines()


def getHostIP():
    """
    Return host IP
    """

    raw = getRawIP()  # get the raw output from netsh

    cleanRaw = []  # array with no newlines
    for index, line in enumerate(raw):  # loop thru each line and split it into strings in array
        if not len(line) == 0:  # line is not empty
            cleanRaw.append(line.split())

    for line in cleanRaw:  # loop thru lines to find the host IP
        if line[0] == "IP" and line[1] == "Address:":  # Found host ip address
            hostip = line[2]

    return hostip


def connect(device):
    """
    Connect the USB device with usbipd-win on host and usbip on VM
    """

    hostIP = getHostIP()  # host IP
    busID = device[0]

    os.system(f'powershell.exe usbipd bind -b {device[0]}')  # Bind device
    sleep(0.5)

    # SSH into VM
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Allows login if not in known_hosts
    ssh.connect(VIRTUAL_MACHINE_IP, username=USERNAME, password=PASSWORD)  # TODO store password somewhere else

    stdin, stdout, stderr = ssh.exec_command("echo 1234 | sudo -S modprobe vhci-hcd ")  # kernel module

    # connect the USB over IP
    stdin, stdout, stderr = ssh.exec_command(f"echo 1234 | sudo -S usbip attach --remote={hostIP} --busid={busID}")

    clear()
    print(f"Device: {device[2]} Attached!")
    sleep(2)


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
            elif inp.lower() == "r" or inp.lower() == "reconnect":  # user wants to reconnect
                clear()
                disconnect(device)
                connect(device)
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


def hasLogin():  # TODO eventually automate this and store as non volatile files.
    """
    Check if the user has entered their username, password, adapter and VM ip
    """

    if USERNAME == "" or PASSWORD == "" or ADAPTER == "" or VIRTUAL_MACHINE_IP == "":  # vars are empty
        return False  # fail test
    else:  # all vars are filled out
        return True  # pass test


def main():
    """
    Main, calls all methods
    """

    if hasLogin() == False:  # user hasn't filled out constants at top of file

        print(
              "\nError: Variables require changing...\n\n"
              "\n################################################################\n\n"
              "Edit this python script file and edit the following variables:\n\n" # temporary
              "USERNAME - this is the username used to ssh into the virtual machine \n\n"

              "PASSWORD - this is the password used to ssh into the virtual machine\n\n"

              "ADAPTER - open cmd, enter \'ipconfig\' and enter the name of the Virtual Adapter\n"
              "after the \"Ethernet adapter\" part. E.g. \"vEthernet (Default Switch)\"\n\n"

              "VIRTUAL_MACHINE_IP - this is the IP of the virtual machine used to ssh into, open the\n"
              "virtual machine, open terminal, type \"ip a\" into the terminal, and enter the ipv4 of\n"
              "the virtual local machine ip under eth0\n"
              "\n################################################################\n")

        print("After you have edited these variables, restart the script and try again...")
        print("Exiting...\n")

    else:

        runAdmin()  # run the script with admin rights

        chooseDevice()  # user chooses device to connect/disconnect


if __name__ == "__main__":
    main()

