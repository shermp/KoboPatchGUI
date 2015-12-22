# KoboPatchGUI

This is a simple GUI to modify the unofficial patch files for Kobo e-ink ereaders. Information about these patches can be found at the [Index to the Metazoa firmware patches](http://www.mobileread.com/forums/showthread.php?t=260100) thread on Mobileread forums.

The GUI is written in Python, and uses Tk/Tkinter as the GUI library. No other external software dependencies are required.

## Current Status

#### Implemented

The following functionally has been added so far:

- Enable/Disable patches
- Disable all patches
- Checking for mutually exlusive options
- Crude tooltip help

## Installation/Running

The program requires Python 2.7 or 3.4+ to be installed on your system. It should work on Windows and Linux. OS X cannot be tested at this time. Linux users may need to download Tk from their repositories as well. A standard Python install on Windows should be sufficient.

To run the program, simply run *KoboPatchGUI.pyw*. It will ask you to choose the patch file(s) you wish to alter.
