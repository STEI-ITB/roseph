@ECHO OFF
SETLOCAL

setlocal EnableDelayedExpansion

REM - Batch file quick connect to an iSCSI Target.

REM - 1. First add portal for the IP address that has been entered. 

REM - 2. List Targets.

REM - 3. If only one target is listed, then logon.

REM - 4. Mark it persistent.

REM - 5. Done.

SET /p ipaddress="Enter IP: "

echo "Trying to add target %1 for discovery"

iscsicli QAddTargetPortal %ipaddress%

REM – Find out the number of Targets discovered for the portal address

SET _count=0

FOR /F "usebackq" %%G IN (`iscsicli ListTargets`) DO (

	SET _cmp=%%G

	SET _result=!_Cmp:~0,3!

	REM - Get a valid IQN Name.

	IF !_RESULT!==iqn (

		set TargetName=!_cmp!

		SET /a _count = _count + 1

	)

)

REM - Check if there is only one target.

if !_count! equ 1 (

	echo "Found A Target - %TargetName%: Attempt to login"

	iscsicli qlogintarget %TargetName%

	Echo “Mark the target as a persistent target”

	iscsicli PersistentLoginTarget %TargetName% * * * * * * * * * * * * * * * *

) ELSE (

	echo "Did not find a single Target to login"

)