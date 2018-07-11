Option Explicit
Dim safeZ
safeZ = 1.5
Dim tmpFileId As String
tmpFileId = "_TEMPORARY_COPY.gcode"
Dim DEBUG
DEBUG = False
Set objFSO=CreateObject("Scripting.FileSystemObject")

' Set variable to 1 saying this IS an internal process call
Call SetOEMDRO (2042, 1)

' Set variable to default 0 saying this We want z routine validation
Call SetOEMDRO (2043, 0)

' Write to a file that python will monitor, and execute when created
Dim outFilePath As String
Dim doneFilePath As String
Dim timeString As String
timeString = Format(Date,"yyyymmdd") & Format(Time,"HHMMSS")
outFilePath="c:\Mach3\argFiles\z-multi." & timeString & ".txt"
doneFilePath=outFilePath & ".done"

' Coordinates passed via 2038-2041 OEMDRO
Dim yCenter As Double
Dim xCenter As Double
Dim width As Double
Dim yZeros

Set yZeros = CreateObject("System.Collections.ArrayList")
yZeros.Add GetOEMDRO(2038)
yZeros.Add GetOEMDRO(2039)
yZeros.Add GetOEMDRO(2040)

width = GetOEMDRO(2041)
yCenter = GetOEMDRO(2039)
If width = 0 Then
  If DEBUG Then
    width = 9.5
  Else
    Code "(ERROR: OEMDRO 2041 for width not set)"
    Exit Sub
  End If
End If
If yCenter = 0 Then
  If DEBUG Then
    yCenter = 5.5
  Else
    Code "(ERROR: OEMDRO 2039 for yCenter not set)"
    Exit Sub
  End If
End If
xCenter = width/2

' Reset these variables
Call SetOEMDRO (2038, 0)
Call SetOEMDRO (2039, 0)
Call SetOEMDRO (2040, 0)
Call SetOEMDRO (2041, 0)  

' First check that we have a wrong gcode loaded
Dim gcodeFilePathFull As String
Dim gcodeFileName As String
Dim gcodeFileNameNoExtension As String
Dim gcodeFileMainDir As String
gcodeFileMainDir = GetloadedGCodeDir()
gcodeFileName = GetloadedGCodeFileName()
gcodeFilePathFull = gcodeFileMainDir & gcodeFileName
If Len(gcodeFilePathFull) = 0 Then
  Code "(ERROR: Load GCode file first)"
  Exit Sub
ElseIf InStr(gcodeFilePathFull,tmpFileId) <> 0 Then
  Code "(ERROR: Don't use a TEMPORARY_COPY file!! Load the actual file yo)"
  Exit Sub
ElseIf InStr(gcodeFilePathFull,"COMPILEDFRAGMENTS") <> 0 Then
  ' If we are using a compiled fragment, we are going to use the base gcode name
  ' TODO: figure out how to convert COMPILEDFRAGMENTS gcode name into base gcode file
  ' Remove _COMPILEDFRAGMENTS_20180610-135243.gcode from file name base
  gcodeFileName = Left(gcodeFileName, (Len(gcodeFileName)-40)) & ".gcode"

  ' Now go back up a dir level, the sub dir should = gcodeFileName minus .gcode now
  gcodeFileMainDir = Left(GetloadedGCodeDir(), Len(GetloadedGCodeDir())-Len(gcodeFileName)+5)
  gcodeFilePathFull = gcodeFileMainDir & gcodeFileName

  If Not objFSO.FileExists(gcodeFilePathFull) Then
    Code "(ERROR: " & gcodeFileName & " does not exist)"
    Begin Dialog ButtonSampleTest 16,32,150,96,"ERROR"
      Text 10,12,130,60, "ERROR: Could not convert COMPILEDFRAGMENTS file to main GCode File. Try reloading main GCode file." 
      OKButton 30,70,40,14
      'CancelButton 80, 70,40,14
    End Dialog
    Dim Dlg2 As ButtonSampleTest
    Dialog Dlg2
    Exit Sub
  End If
End If

gcodeFileNameNoExtension = Left(gcodeFileName, (Len(gcodeFileName)-6))

' Remove Extension and replace with temp identifier
Dim compiledGcodeFile As String
Dim compiledgcodeFileName As String

' Check if we have a fragmented setup (2nd generation multi Z)
Dim fragmentDir As String
fragmentDir = gcodeFileMainDir & gcodeFileNameNoExtension  
Dim zinfoFile As String
zinfoFile = fragmentDir & "\" & gcodeFileNameNoExtension & ".zinfo"

' If we have fragmentation setup
If objFSO.FolderExists(fragmentDir) Then
  If objFSO.FileExists(zinfoFile) Then
    ' First get the real Z in the middle
    Dim zRealIndex As Double
    ' Absolute Positioning
    Code "G90"
    ' Safe Z
    Code "G0Z " & safeZ
    zRealIndex = runZRoutine(xCenter, yCenter, True, False)
    
    Dim argFileString As String
    argFileString = "FRAGMENTED" & Chr(13) & Chr(10)
    argFileString = argFileString & fragmentDir & Chr(13) & Chr(10)
    argFileString = argFileString & "RealIndex " & zRealIndex  & Chr(13) & Chr(10)

    ' Multi Z Fragment loop
    ' This is stupid, i can't find a way to split an array so I had to use new lines
    Dim fileName As String
    Dim zX As Double
    Dim zY As Double
    zX = 0
    zY = 0
    Set zFile = objFSO.OpenTextFile(zinfoFile)
    Do Until zFile.AtEndOfStream
      Dim infoLine As String
      infoLine = zFile.ReadLine
      If Not IsNumeric(infoLine) Then
        fileName = Str(infoLine)
      ElseIf zX > width or zY > (yCenter*2) Then
        Code "(ERROR: Value in Zinfo is larger than width or height)"
        Begin Dialog ButtonSampleTest1 16,32,150,96,"ERROR"
          Text 10,12,130,60, "ERROR: Value in Zinfo is larger than width or height. Something is wrong contact Grant." 
          OKButton 30,70,40,14
          'CancelButton 80, 70,40,14
        End Dialog
        Dim Dlg3 As ButtonSampleTest1
        Dialog Dlg3
        Exit Sub
      ElseIf zX = 0 Then
        zX = CDbl(infoLine)
      Else
        zY = CDbl(infoLine)
        'Print("got it: " & fileName & " " & Str(zX) & " " & Str(zY))
        Dim curZIndex As Double
        curZIndex = runZRoutine(zX,zY,False, True)
        argFileString = argFileString & fileName & " " & curZIndex & Chr(13) & Chr(10)
        zX = 0
        zY = 0
      End If
    Loop
    zFile.Close

    ' Write everything at once
    Set argFile = objFSO.CreateTextFile(outFilePath,True)
    argFile.Write argFileString
    argFile.Close
  Else
    Code "(ERROR: The fragmented folder exists, but no info file found)"
    Begin Dialog ButtonSample 16,32,150,96,"ERROR"
      Text 10,12,130,60,"ERROR: The fragmented folder exists, but no info file found. This is an issue." 
      OKButton 30,70,40,14
      'CancelButton 80, 70,40,14
    End Dialog
    Dim Dlg1 As ButtonSample
    Dialog Dlg1 
  End If
else
  ' Absolute Positioning
  Code "G90"
  ' Safe Z
  Code "G0Z " & safeZ
  ' Arguments to pass to python
  Dim zArgs As String
  zArgs = ""
  Dim yArgs As String
  yArgs = ""

  Dim y
  For Each y In yZeros
    Dim realIndex As Boolean
    If y = yCenter Then
      realIndex = True
    Else
      realIndex = False
    End If
    Dim midPoint As Double
    midPoint = width/2
    Dim zOffset As Double
    yArgs = yArgs & y & " "
    zOffset = runZRoutine(midPoint, y, realIndex, False)
    zArgs = zArgs & zOffset & " "
  Next

  ' Write the arguments to file
  Set argFile = objFSO.CreateTextFile(outFilePath,True)
  argFile.Write "THREEPOINT" & Chr(13) & Chr(10)
  argFile.Write zArgs & Chr(13) & Chr(10)
  argFile.Write yArgs & Chr(13) & Chr(10)
  argFile.Write yCenter & Chr(13) & Chr(10)
  argFile.Write gcodeFilePathFull
  argFile.Close
End If

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

' Function that runs the Z Routine and retrieves the offset
' Params:
'          zX = X location of to index
'          zY = Y location of to index
'          realIndex = Really apply the index (actually applies the ZERO)
'!!!!!!!!!!!!!!!!! If you modify, make sure z-single_1019.vbs stays up to date too !!!!!!!!!!!!!!!!!!!
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