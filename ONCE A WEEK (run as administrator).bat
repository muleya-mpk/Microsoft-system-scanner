@echo off
:start
color a
echo Drive and system scans initiated.
echo Stage 1: Diskdrive status
wmic diskdrive get status
echo Stage 1 complete. If anything other "OK" is displayed please look for a solution online.
echo Stage 2: Diskdrive light scan
chkdsk /c
echo Stage 2 complete. Confirm in the text if further action is required.
echo Satge 3: Windows file verification
sfc /scannow
echo Stage 3 complete. Read through each stage and confirm no problems have been detected in the system files.
pause;
chkdsk /c /f /r 
set /p input1 = Key in 1 to restart your computer or 2 to exit the program:  
if %input1% == 2 exit
if %input1% == 1 goto shutdown /r /t 100 /c "System boot up scan intiated, it will begin once your computer restarts. This will take a while; Please leave PC plugged in and idle."
echo System and drive scans ocmplete. See you in seven days.

:SHUTDOWN
shutdown /r /t 100 /c "System boot up scan intiated, it will begin once your computer restarts. This will take a while; Please leave PC plugged in and idle."
echo System and drive scans ocmplete. See you in seven days.
