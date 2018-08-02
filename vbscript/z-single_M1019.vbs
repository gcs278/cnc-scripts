' This is the M1019 Script to execute single auto z zero
' I had to wrap this in a script due to double square jig
Dim doubleJigXoff, doubleJigYoff
doubleJigXoff = -0.06
doubleJigYoff = 15.73
Dim DEBUG
DEBUG = False
Set objFSO=CreateObject("Scripting.FileSystemObject")

' Check if we are in my Virtual Machine, if so DEBUG
If objFSO.FolderExists("Z:\grantspence On My Mac") Then
  DEBUG = True
End if

' Double jig variable
Dim doubleJig As Boolean
doubleJig = GetUserLED(1234)

Dim outFilePath As String
Dim doneFilePath As String
Dim timeString As String
timeString = Format(Date,"yyyymmdd") & Format(Time,"HHMMSS")
outFilePath="c:\Mach3\argFiles\z-multi." & timeString & ".txt"

doneFilePath=outFilePath & ".done"
Dim tmpFileId As String
tmpFileId = "_TEMPORARY_COPY.gcode"

' First check that we have a wrong gcode loaded
Dim gcodeFilePathFull As String
Dim gcodeFileName As String
Dim gcodeFileNameNoExtension As String
Dim gcodeFileMainDir As String
gcodeFileMainDir = GetloadedGCodeDir()
gcodeFileName = GetloadedGCodeFileName()
gcodeFilePathFull = gcodeFileMainDir & gcodeFileName
if doubleJig Then
  If Len(gcodeFilePathFull) = 0 Then
    Code "(ERROR: Load GCode file first, your trying to do a double jig)"
    Exit Sub
  ElseIf InStr(gcodeFilePathFull,tmpFileId) <> 0 Then
    Code "(ERROR: Don't use a TEMPORARY_COPY file!! Load the actual file yo)"
    Exit Sub
  End If
End If

' Set variable to 1 saying we DO want to zero
Call SetOEMDRO (2037, 1)

' Set variable to 0 saying this is NOT an internal process call
Call SetOEMDRO (2042, 0)

' Set variable to 0 saying WE WANT VALIDATION
Call SetOEMDRO (2043, 1)

' Reset 2050 z offset variable to 0
Call SetOEMDRO (2050, 0.00)

Dim currentX As Double, currentY As Double
currentX = GetOEMDRO(178)
currentY = GetOEMDRO(179)

Dim realZindex As Double
' This is our normal Z, with no double jig
realZindex = runZRoutine(currentX, currentY, true, false)

' Now determine if we want to execute same thing on additional square jig
if doubleJig Then
  ' Absolute Positioning
  Code "G90"

  Dim newX As Double, newY as Double
  newX = currentX + doubleJigXoff
  newY = currentY + doubleJigYoff
  
  Dim secondZindex As Double
  secondZindex = runZRoutine(newX, newY, false, false)

  ' Write the arguments to file
  Set argFile = objFSO.CreateTextFile(outFilePath,True)
  argFile.Write "DOUBLEJIG_SINGLE" & Chr(13) & Chr(10)
  argFile.Write doubleJigXoff & Chr(13) & Chr(10)
  argFile.Write doubleJigYoff & Chr(13) & Chr(10)
  argFile.Write realZindex & Chr(13) & Chr(10)
  argFile.Write secondZindex & Chr(13) & Chr(10)
  argFile.Write gcodeFilePathFull
  argFile.Close

  ' Now we wait for python to create the done file
  Dim fileExists As Boolean
  fileExists = False
  Dim fileTimeout
  fileTimeout = 25
  Speak("Waiting for python to complete post processing")
  While fileExists = False And fileTimeout <> 0
    fileExists = objFSO.FileExists(doneFilePath)
    Sleep 1000
    fileTimeout = fileTimeout - 1
  Wend

  If Not fileExists Then
    MsgBox "Error: Can't find the compilation file python was suppose to create. Something went wrong with the multi z process. Contact Grant. Do not continue unless you know what you are doing."
    Code "(ERROR: Can't find the file python was suppose to create)"
    Speak("ERROR: Post processing failed")
    Exit Sub
  End If

  ' Now read the done file to get the location of the compiled file
  Set doneFile = objFSO.OpenTextFile(doneFilePath)
  Dim count As Integer
  count = 1
  Do Until doneFile.AtEndOfStream
    if count = 1 Then
      compiledGcodeFile = doneFile.ReadLine
    Elseif count = 2 Then  
      compiledgcodeFileName = doneFile.ReadLine
    End If
   count= count +1
  Loop

  if compiledGcodeFile = "" or not objFSO.FileExists(compiledGcodeFile) Then
    MsgBox "Error: Done File doens't contain compiled path. Something went wrong with the multi z process. Contact Grant. Do not continue unless you know what you are doing."
    Code "(ERROR: Done file is missing compiled file path)"
    Exit Sub
  End If

  LoadFile(compiledGcodeFile)
  Code "(SUCCESSFULLY re-aligned Z indexs on the file)"

  Code "G0X0Y0Z1.00"
  While IsMoving()      
    Sleep 100
  Wend 
End If

'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DO NOT MODIFY HERE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'!!!!!!!!!! Modify in z-multi_M1020.vbs and copy over to here !!!!!!!!!!!!!!!!!!!!!!!!!!!
Function runZRoutine(zX As Double, zY As Double, realIndex As Boolean, skipVerify As Boolean) As Double
  If DEBUG Then
    Randomize ' Initialize random-number generator.
    runZRoutine = (3 * Rnd) + 1
    Exit Function
  End If

  ' If  we wanna skip the "tap" from z routine
  If skipVerify Then
    ' Set variable to 0 saying this We DON'T want z routine validation
    Call SetOEMDRO (2043, 1)
  Else
    ' Set variable to 0 saying this We WANT z routine validation
    Call SetOEMDRO (2043, 0)
  End If

  Speak("Moving to new z index")
  Code "G0X " & zX & "Y" & zY
  While IsMoving()      
    Sleep 1000
  Wend
  Dim Timer

  ' If y is zero point, then ACTUALLY ZERO
  ' OEM 2037 - Says whether to set the new Z index (incase you just want to get measurement)
  If realIndex Then
    Call SetOEMDRO (2037, 1)
  Else
    Call SetOEMDRO (2037, 0)
  End If
  
  Call SetUserDRO(2035, 0)     
  ' This calls the Z-zero routine with the touch plate
  Code "M1010"

  ' Debug make it quick
  If DEBUG Then
    Timer = 13
  Else
    Timer = 0
  End If

  ' 2035 = OEM that gets set to 1 when M1010 finishes, so we wait for finish
  While GetOEMDRO(2035) = 0 And Timer < 20
    Sleep 1000
    Timer = Timer + 1
  Wend

  If GetOEMDRO(2035) = 2 Then
    Code "(ERROR with touch routine)"
    Exit Sub
  End If
 

  If Timer = 15 And Not DEBUG Then
    Code "(Zero Script timed out. Exiting.)"
    Exit Sub
  End If

  ' OEM 85 = Z Current Index
  ' OEM 2036 = M1010 zabsolute value passed
  runZRoutine = GetOEMDRO(2036)

End Function