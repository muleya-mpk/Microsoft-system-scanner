[README#Microsoft system scanner#.txt](https://github.com/user-attachments/files/23163018/README.Microsoft.system.scanner.txt)
#Microsoft system scanner

This batch file is an attempt to put together some CMD prompts that troubleshoot the computer

#CMD Prompts used
-wmic diskdrive get status
-chkdsk/c
-sfc/scannow
-chkdsk/c /f /r

#Additional notes
-Slightly interactive as user input is required towards the end of the program
-text changes colour at different stages

#Password
ttscxll

#Help
I am struggling to make the program shutdown the computer if the user wants to initiate the boot up scan. I've tried implementing a class called "Shutdown" to no avail. Please walk me through any suggestions you may have
