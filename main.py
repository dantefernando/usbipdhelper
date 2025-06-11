# Allow user to interactively connect and disconnect usb devices using usbipd
# Written by Dante Fernando

# Urgent TODO 
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
from ssh_credentials import USERNAME, PASSWORD  # TODO ask user for username and password, store it in default.txt


def disconnect(device):
    """
    Disconnect the USB device from VM
    """

    busID = device[0]

    os.system(f'powershell.exe usbipd unbind -b {busID}')  # unbind device from host
    print(f"Device: {device[2]} disconnected!")
    sleep(1.5)


def getRawIP(virtualMachineAdapter):
    """
    Return raw info output of netsh command
    """

    # Get network adapter raw output from netsh
    return check_output(f"netsh interface ip show addresses \"vEthernet ({virtualMachineAdapter})\"", shell=True).decode().splitlines()


def getHostIP(virtualMachineAdapter):
    """
    Return host IP
    """

    raw = getRawIP(virtualMachineAdapter)  # get the raw output from netsh

    cleanRaw = []  # array with no newlines
    for index, line in enumerate(raw):  # loop thru each line and split it into strings in array
        if not len(line) == 0:  # line is not empty
            cleanRaw.append(line.split())

    for line in cleanRaw:  # loop thru lines to find the host IP
        if line[0] == "IP" and line[1] == "Address:":  # Found host ip address
            hostip = line[2]

    return hostip


def connect(device, virtualMachine, isBinded):
    """
    Connect the USB device with usbipd-win on host and usbip on VM

    """

    virtualMachineName = virtualMachine[0]  # get name
    virtualMachineAdapter = virtualMachine[1]  # get adapter
    virtualMachineIP = virtualMachine[2]  # get ip

    # Check if IP is empty
    if virtualMachineIP == "":  # IP is empty.
        print(f"Error: Unable to retrieve Virtual Machine IP for: {virtualMachineName}. Please Start the VM in Hyper-V or double"
              "\ncheck that the name of the VM is correct.")

        print("Returning to menu...")

    else:  # IP is not empty. Start the connection process

        hostIP = getHostIP(virtualMachineAdapter)  # host IP
        busID = device[0]

        if isBinded == False:  # device is not shared/binded
            print("Binding Device...")
            os.system(f'powershell.exe usbipd bind -b {device[0]}')  # Bind device
            sleep(0.5)

        # SSH into VM
        print("Connecting to Virtual Machine via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Allows login if not in known_hosts
        ssh.connect(virtualMachineIP, username=USERNAME, password=PASSWORD)  # TODO store password somewhere else

        # Enable kernel module in VM
        print("Enabling Virtual USB Kernel Module...")
        stdin, stdout, stderr = ssh.exec_command("echo 1234 | sudo -S modprobe vhci-hcd ")  # kernel module

        # connect the USB over IP
        print("Attaching USB with usbip to Virtual Machine...")
        stdin, stdout, stderr = ssh.exec_command(f"echo 1234 | sudo -S usbip attach --remote={hostIP} --busid={busID}")

        # clear()
        print(f"Device: {device[2]} Attached.")
        sleep(2)


def displayDevice(index):
    """
    Display device to user in a readable format
    with BUSID, VID:PID, NAME AND STATE
    """

    raw = getRawDevices()
    print(f"\n{raw[1]}\n{raw[index+2]}\n")


def manageDevice(index, virtualMachine):
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
                if device[3] == "Not shared": # is not binded
                    connect(device, virtualMachine, False)  # bind and connect the device 
                else:  # is already binded
                    connect(device, virtualMachine, True)  # connect the device without binding

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
                connect(device, virtualMachine, False)  # connect and bind the device
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
    virtualMachine = getDefaultVM()  # get default vm with all info

    while True:

        devices = getDevices()  # return devices data as 2D array 

        displayDevices()  # send formatted devices to stdout for user to choose from

        print("Select a device using the index under \"INDEX\"")

        print("Press CTRL-C at any time throughout the program to exit.")
        inp = input(f"Index of Device to Connect/Disconnect (1-{len(devices)}) or (R)efresh devices: ")
        try:
            inp = int(inp)

            if 1 <= inp <= len(devices):  # int in range
                clear()
                manageDevice(inp-1, virtualMachine)  # disconnect/connect device
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

    if not pyuac.isUserAdmin():  # user is not admin
        print("Prompting user to Run as Administrator...")
        pyuac.runAsAdmin()

    else:  # user is already admin
        print("Already Adminstator, proceeding.")


def hasLogin():
    """
    Check if the user has entered their username, password, adapter and VM ip
    """

    if USERNAME == "" or PASSWORD == "":  # vars are empty

        print(
              "\nError: Variables require changing...\n\n"
              "\n################################################################\n\n"
              "Edit ssh_credentials.py file and edit the following variables:\n\n" # temporary
              "USERNAME - this is the username used to ssh into the virtual machine \n\n"

              "PASSWORD - this is the password used to ssh into the virtual machine\n\n"

              "\n################################################################\n")

        print("After you have edited these variables, restart the script and try again...")
        print("Exiting...\n")

        return False  # fail test

    else:  # all vars are filled out
        return True  # pass test


def getDefaultVM():
    """
    Read the default file to retrieve default virtualmachine Hyper-v name, adapter and ip
    """

    try:
        with open("default.txt", "r") as file:  # open the file with read permissions
            name = file.readline()  # get default vm name from file

        # cross reference name with existing VMs 

        virtualMachines = getVMs()  # get existing VMs

        for machine in virtualMachines:  # loop thru all existing virtualMachines 
            if machine[0] == name:  # name matches default
                return machine  # return the virtual machine info

    except IOError:  # can't find file/can't open file
        print("Unable to open default.txt...")


def setDefaultVM(virtualMachine):
    """
    Store default virtualMachine to ssh into in a file on disk
    """

    with open("default.txt", "w") as file:  # Create the settings file
        print(f"Setting \"{virtualMachine[0]}\" as default ssh machine in default.txt...")
        file.write(f"{virtualMachine[0]}")


def getVMs():
    """
    Get array of available Hyper-V VMs formatted.
    """

    print("Retrieving Existing Hyper-V Virtual Machines...")

    virtualMachines = []  # 2D array with VMs. [[VMName, SwitchName, IPAddress],[...,...,...]] etc.


    # Get only the VM names from the get-vm command
    rawNames = check_output("powershell.exe \"get-vm | select -ExpandProperty networkadapters | select vmname | ft -wrap -autosize\"", shell=True).decode().splitlines()

    for line in rawNames[3:]:  # Append lines after the first 3 lines of raw stdout from command
        if not line == "":  # if line is not empty
            virtualMachines.append([line.strip()])


    # get VM Switchnames
    rawSwitches = check_output("powershell.exe \"get-vm | select -ExpandProperty networkadapters | select switchname | ft -wrap -autosize\"", shell=True).decode().splitlines()

    for i in range(3, 3+len(virtualMachines)):  # skip first 3 lines but get the number of virtual machines and only append that many lines

        virtualMachines[i-3].append(rawSwitches[i].strip())


    # get VM ip addresses
    rawIPs = check_output("powershell \"get-vm | select -ExpandProperty networkadapters | select ipaddresses | ft -wrap -autosize\"", shell=True).decode().splitlines()

    for i in range(3, 3+len(virtualMachines)):  # skip first 3 lines but append IPs for amount of virtualMachines

        ips = rawIPs[i].strip().strip("{}").split(",")  # get raw string containing ipv4 and ipv6 together and convert to array

        for j in range(0, len(ips)):  # loop thru ips
            ips[j] = ips[j].strip()  # removes whitespace from each ip address

            if not any(c.isalpha() for c in ips[j]):  # if the IP is IPv4
                virtualMachines[i-3].append(ips[j])  # append IPv4 to virtualMachines array

    return virtualMachines  # returns all virtual machines in 2D array [[VMName, SwitchName, IPAddress],[...,...,...]] etc.


def getRawVMs():
    """
    get raw output of `get-vm | select -ExpandProperty networkadapters | select vmname, switchname, ipaddresses | ft
    -wrap -autosize` command.
    """

    return check_output("powershell.exe \"get-vm | select -ExpandProperty networkadapters | select vmname, switchname, ipaddresses | ft -wrap -autosize\"", shell=True).decode().splitlines()


# TODO add exception for having no VMs set up
def displayVMs():
    """
    Display Hyper-V VMs cleanly with indexes for user to choose from
    """
    raw = getRawVMs()  # get raw output of VMs to display to user

    raw.pop(0)  # pop empty line

    print("Your Configured VMs in Hyper-V:\n")

    for index, line in enumerate(raw):  # loop thru all lines in raw output

        if len(line) == 0:  # Reached end of VMs
            break

        else:  # Check line
            if index == 0:
                print(f"INDEX \t {line}")
            elif index == 1:
                print(f"----- \t {line}")
            else:  # Print with index beside device
                print(f"{index-1}) \t {line}")


def confirmVM():
    """
    Confirm with the user which Hyper-V VM they want to connect to by default
    """

    while True:

        virtualMachines = getVMs()  # retrieve all virtual machines set up in hyper-v as an array

        displayVMs()  # Display the VMs to the user

        print("\nWhich VM would you like to connect to from now on? (This will be saved as the Default in default.txt)")
        print("Select a device using the index under \"INDEX\"")

        inp = input(f"Index of Device to Connect/Disconnect (1-{len(virtualMachines)}) or (R)efresh Virtual Machines: ")
        try:
            inp = int(inp)

            if 1 <= inp <= len(virtualMachines):  # int in range
                setDefaultVM(virtualMachines[inp-1])  # set the default Virtual Machine to the selected VM
                break
            else:  # int out of range
                clear()
                print(f"\nEnter a valid index between 1 and {len(virtualMachines)}...\n")

        except ValueError:  # user entered a string
            if inp.lower() == "r" or inp.lower() == "refresh":  # str in range
                clear()
                print("Refreshed and Updating Virtual Machines...")
            else:  # str out of range
                clear()
                print(f"\nEnter a valid index between 1 and {len(virtualMachines)}...\n")



def defaultFileExists():
    """
    Check if the default.txt file exists in working directory

    return True if file exists
    return False if file does not exist
    """

    try:  # Check for existing file by trying to read the file
        with open("default.txt", "r") as file:
            return True  # default.txt exists

    except IOError:  # default.txt does not exist
        return False


def main():
    """
    Main, calls all methods
    """

    try:

        runAdmin()  # prompt user to run as admin if needed for powershell commands

        while True:

            # First time setup, check if settings file exists
            if defaultFileExists() == False:  # default.txt file doesn't exist

                print("default.txt not found, performing first time setup...")

                confirmVM()  # confirm with user which vm to connect to by default

            else:  # vm info file exists
                print("Found default VM in default.txt...")

                break

        if hasLogin() == True:  # user has filled out ssh_credentials.py

            chooseDevice()  # user chooses device to connect/disconnect

    except KeyboardInterrupt:  # user presses ^C
        print("\nExiting...")


if __name__ == "__main__":
    main()

