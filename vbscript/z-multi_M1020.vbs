Option Explicit
Dim safeZ
If GetABSPosition(0) > 14.0 Then
  safeZ = -1.5
else 
  safeZ = -2.0
End If
Dim tmpFileId As String
tmpFileId = "_TEMPORARY_COPY.gcode"
Dim DEBUG
DEBUG = False
Set objFSO=CreateObject("Scripting.FileSystemObject")
Dim skipVerifyTap as Boolean

' Variables for Auto Z jig
Dim autoZJigSafeZ As Double
Dim feedRateFast As Integer
Dim feedRateSlow As Integer
Dim autoZJigY As Double
autoZJigSafeZ = -1.0
feedRateFast = 120
feedRateSlow = 20
autoZJigY = 14.51

' Double jig variable
Dim numberOfJigs As Integer
numberOfJigs = GetOEMDRO(2090)

' Auto Z Jig Variable
Dim autoZJig As Boolean
autoZJig = GetUserLED(1235)

if autoZJig then
  safeZ = -2.0
End if

' Define the square jigs that we have
Dim numOfJigs As Integer
Static jigs (5,5) As Double
numOfJigs = GetOEMDRO(2090)
jigs(0,0) = 0
jigs(0,1) = 0
jigs(1,0) = -0.03
jigs(1,1) = 15.74
jigs(2,0) = 0.32
jigs(2,1) = 31.23

' Check if we are in my Virtual Machine, if so DEBUG
If objFSO.FolderExists("Z:\grantspence On My Mac") Then
  DEBUG = True
End if

' Set variable to 1 saying this IS an internal process call to the single z process
Call SetOEMDRO (2042, 1)

' Set variable to default 0 saying this We want z routine validation
Call SetOEMDRO (2043, 0)

' Reset 2050 z offset variable to 0
Call SetOEMDRO (2050, 0.00)

' Write to a file that python will monitor, and execute when created
Dim outFilePath As String
Dim doneFilePath As String
Dim timeString As String
timeString = Format(Date,"yyyymmdd") & Format(Time,"HHMMSS")
outFilePath="c:\Mach3\argFiles\z-multi." & timeString & ".txt"
doneFilePath=outFilePath & ".done" 

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
ElseIf InStr(gcodeFilePathFull,"COMPILEDFRAGMENTS") <> 0 Or InStr(gcodeFilePathFull,"COMPILEDMULTI") <> 0 Then
  ' If we are using a compiled fragment, we are going to use the base gcode name
  ' TODO: figure out how to convert COMPILEDFRAGMENTS gcode name into base gcode file
  ' Remove _COMPILEDFRAGMENTS_20180610-135243.gcode from file name base
  if InStr(gcodeFilePathFull,"COMPILEDFRAGMENTS") <> 0 Then
    gcodeFileName = Left(gcodeFileName, (Len(gcodeFileName)-40)) & ".gcode"
    ' Now go back up a dir level, the sub dir should = gcodeFileName minus .gcode now
    gcodeFileMainDir = Left(GetloadedGCodeDir(), Len(GetloadedGCodeDir())-Len(gcodeFileName)+5)
    gcodeFilePathFull = gcodeFileMainDir & gcodeFileName

  else
    gcodeFileName = Left(gcodeFileName, (Len(gcodeFileName)-36)) & ".gcode"
    ' Now go back up a dir level, the sub dir should = gcodeFileName minus .gcode now
    gcodeFileMainDir = Left(GetloadedGCodeDir(), Len(GetloadedGCodeDir())-Len("multi_compiled\"))
    gcodeFilePathFull = gcodeFileMainDir & gcodeFileName
  End If



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

' Coordinates passed via 2038-2041 OEMDRO
Dim yCenter As Double
Dim xCenter As Double
Dim width As Double
Dim height As Double
Dim edgePadding As Double
edgePadding = 1.5

' Get Width and Height arguments
height = GetOEMDRO(2038)
width = GetOEMDRO(2039)

' Y Zero Values
Dim zZeroTop, zZeroMiddle, zZeroBottom As Double
zZeroTop = height - edgePadding
zZeroMiddle = height / 2
zZeroBottom = edgePadding
' Special logic for dynamic Z (use the gcode max values to determine area)
If zZeroTop = 0 Then
  zZeroTop = ( GetOEMDRO(11) - edgePadding ) ' Max Value of GCode minus 1.5
End If
If zZeroMiddle = 0 Then
  zZeroMiddle = ( GetOEMDRO(11) / 2 ) ' Max value of gcode in half
End If
If zZeroBottom = 0 Then
  zZeroBottom = edgePadding ' Standard value
End If

yCenter = zZeroMiddle
If width = 0 Then
  width = GetOEMDRO(10) ' Max value of X loaded gcode
End If
xCenter = width/2

' X Zero Values
Dim zZeroLeft, zZeroRight As Double
zZeroLeft = edgePadding
zZeroRight = width - edgePadding

' Dictionary of AXIS,value points to take a reading
' Keys can't be the same, just append number (we will remove later)
Dim multiZeroPoints
Set multiZeroPoints = CreateObject("Scripting.Dictionary")
multiZeroPoints.Add "YPOINT2", zZeroBottom
multiZeroPoints.Add "XPOINT1", zZeroLeft
multiZeroPoints.Add "YPOINT1", zZeroTop
multiZeroPoints.Add "XPOINT2", zZeroRight
multiZeroPoints.Add "CENTERPOINT1", 0 ' Logic should use xCenter and yCenter

' Reset these variables
Call SetOEMDRO (2038, 0)
Call SetOEMDRO (2039, 0)
Call SetOEMDRO (2040, 0)
Call SetOEMDRO (2041, 0) 

gcodeFileNameNoExtension = Left(gcodeFileName, (Len(gcodeFileName)-6))

' Remove Extension and replace with temp identifier
Dim compiledGcodeFile As String
Dim compiledgcodeFileName As String

' Check if we have a fragmented setup (2nd generation multi Z)
Dim fragmentDir As String
fragmentDir = gcodeFileMainDir & gcodeFileNameNoExtension  
Dim zinfoFile As String
zinfoFile = fragmentDir & "\" & gcodeFileNameNoExtension & ".zinfo"
Dim argFileString As String

'''''''''''''''''''''''' AUTO Z Jig Pick up ''''''''''''''''''''''''''''''
if autoZJig Then
  Dim retrieveAutoZJigRet As Boolean
  retrieveAutoZJigRet = retrieveAutoZJig()
end if

Dim xJigOffset As Double, yJigOffset As Double
Dim I as Integer

''''''''''''''''''''''''''' FRAGMENTED Multi Z '''''''''''''''''''''''''''
If objFSO.FolderExists(fragmentDir) Then
  If objFSO.FileExists(zinfoFile) Then
    ' Contents of the argument file
    argFileString = "FRAGMENTED" & Chr(13) & Chr(10)
    argFileString = argFileString & fragmentDir & Chr(13) & Chr(10)
   
    ' For each of the jigs, do multi Z
    For I = 0 To (numOfJigs-1)
      ' Detect Emergency Stop
      If GetOEMLED(800) Then
        Exit Sub
      End If
      Dim firstJig As Boolean
      firstJig = True

      ' First navigate to our default offset
      xJigOffset = jigs(I,0)
      yJigOffset = jigs(I,1)
      if I > 0 Then
        firstJig = False
        ' Commented out, this didn't work anyways
      '  ' Now Selective second x and y
      '  Code "G0X" & xJigOffset & "Y" & yJigOffset
      '  While IsMoving()      
      '    Sleep 100
      '  Wend
      '  Begin Dialog ButtonJig 16,32,150,96,"ZERO"
      '    Text 10,12,130,60, "Zero X and Y for the second jig and then hit okay." 
      '    OKButton 30,70,40,14
      '    'CancelButton 80, 70,40,14
      '  End Dialog
      '  Dim Dlg4 As ButtonJig
      '  Dialog Dlg4
      '  xJigOffset = GetOEMDRO(800)
      '  yJigOffset = GetOEMDRO(801)
      End If

      ' First get the real Z in the middle
      Dim zRealIndex As Double
      ' Absolute Positioning
      Code "G90"
      ' Safe Z
      Code "G53Z " & safeZ
      zRealIndex = runZRoutine(xCenter + xJigOffset, yCenter + yJigOffset, firstJig, autoZJig)
      
      ' Only write RealIndex for first first jig
      if firstJig then
        argFileString = argFileString & "RealIndex " & zRealIndex  & Chr(13) & Chr(10)
      End If
      argFileString = argFileString & "xJigOffset " & xJigOffset & Chr(13) & Chr(10)
      argFileString = argFileString & "yJigOffset " & yJigOffset & Chr(13) & Chr(10)

      ' Multi Z Fragment loop
      ' This is stupid, i can't find a way to split an array so I had to use new lines
      Dim fileName As String
      Dim zX As Double
      Dim zY As Double
      zX = 0
      zY = 0
      Set zFile = objFSO.OpenTextFile(zinfoFile)
      Do Until zFile.AtEndOfStream
        ' Detect Emergency Stop
        If GetOEMLED(800) Then
          Exit Sub
        End If
        Dim infoLine As String
        infoLine = zFile.ReadLine
        If Not IsNumeric(infoLine) Then
          fileName = Str(infoLine)
        'ElseIf (zX + xJigOffset) > (width+ xJigOffset) Or (zY + yJigOffset) > ((yCenter*2)+yJigOffset) Then
        '  Code "(ERROR: Value in Zinfo is larger than width or height)"
        '  Begin Dialog ButtonSampleTest1 16,32,150,96,"ERROR"
        '    Text 10,12,130,60, "ERROR: Value in Zinfo is larger than width or height. Something is wrong contact Grant." 
        '    OKButton 30,70,40,14
        '    'CancelButton 80, 70,40,14
        '  End Dialog
        '  Dim Dlg3 As ButtonSampleTest1
        '  Dialog Dlg3
          'Exit Sub
        ElseIf zX = 0 Then
          zX = CDbl(infoLine) + xJigOffset
        Else
          zY = CDbl(infoLine) + yJigOffset
          'Print("got it: " & fileName & " " & Str(zX) & " " & Str(zY))
          Dim curZIndex As Double
          curZIndex = runZRoutine(zX,zY,False, True)
          argFileString = argFileString & fileName & " " & curZIndex & Chr(13) & Chr(10)
          zX = 0
          zY = 0
        End If
      Loop
      zFile.Close
    Next

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

Else
  ''''''''''''''''''''''''''' FIVEPOINT MULTI Z ''''''''''''''''''''''''''''''''
  argFileString = ""

  ' For each of the jigs, do multi Z
  For I = 0 To (numOfJigs-1)
    ' Absolute Positioning
    Code "G90"
    ' Safe Z
    Code "G53Z " & safeZ
    
    ' Repeated code FYI
    xJigOffset = jigs(I,0)
    yJigOffset = jigs(I,1)

    argFileString = argFileString & "xJigOffset " & xJigOffset & Chr(13) & Chr(10)
    argFileString = argFileString & "yJigOffset " & yJigOffset & Chr(13) & Chr(10)

    Dim notFirst As Boolean
    notFirst = False
    Dim pointType, key
    Dim keyStr as String
    For Each key In multiZeroPoints
      ' Detect Emergency Stop
      If GetOEMLED(800) Then
        Exit Sub
      End If
      ' This is really stupid, but vbs won't work without copying!
      keyStr = key
      ' Remove the last character (the number)
      pointType = Left(str(keyStr), (Len(keyStr) ))
      pointType = Trim(pointType)

      ' Only take the index when it's in the center and it's the first Jig
      Dim realIndex As Boolean
      If pointType = "CENTERPOINT" And I = 0 Then
        realIndex = True
      Else
        realIndex = False
      End If

      Dim targetX, targetY
      if pointType = "XPOINT" Then
        targetX = multiZeroPoints(key) + xJigOffset
        targetY = yCenter + yJigOffset
      Elseif pointType = "YPOINT" Then
        targetX = xCenter + xJigOffset
        targetY = multiZeroPoints(key) + yJigOffset
      Elseif pointType = "CENTERPOINT" Then
        targetX = xCenter + xJigOffset
        targetY = yCenter + yJigOffset
      End If
      targetX = Round(targetX,1)
      targetY = Round(targetY,1)

      Dim zOffset As Double
      if autoZJig Then
        skipVerifyTap = True
      else
        skipVerifyTap = notFirst
      end if
      zOffset = runZRoutine(targetX, targetY, realIndex, skipVerifyTap)
      argFileString = argFileString & pointType & " " & targetX & "," & targetY & "," & zOffset & Chr(13) & Chr(10)

      notFirst = True
    Next
  Next

  ' Write the arguments to file
  Set argFile = objFSO.CreateTextFile(outFilePath,True)
  argFile.Write "FIVEPOINT_MULTI" & Chr(13) & Chr(10)
  argFile.Write gcodeFilePathFull & Chr(13) & Chr(10)
  argFile.Write argFileString
  argFile.Close
End If

'''''''''''''''''''''''' AUTO Z Jig Place Back ''''''''''''''''''''''''''''''
if autoZJig Then
  Dim putBackAutoZJigRet As boolean
  putBackAutoZJigRet = putBackAutoZJig()
end if

' Now we wait for python to create the done file
Dim fileExists As Boolean
fileExists = False
Dim fileTimeout
fileTimeout = 35
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
  If count = 1 Then
    compiledGcodeFile = doneFile.ReadLine
  Elseif count = 2 Then  
    compiledgcodeFileName = doneFile.ReadLine
  End If
  count= count +1
Loop

If compiledGcodeFile = "" Or Not objFSO.FileExists(compiledGcodeFile) Then
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


' Function that runs retrieves the auto z jig
' Params:
Function retrieveAutoZJig() As Boolean
 ' Retrieveing the auto z jig
  Code "F" & feedRateFast ' Feed Rate
  Code "G0G53Z" & autoZJigSafeZ
  Code "G0G53X2.45Y" & autoZJigY
  Code "G0G53Z-3.0"

  Code "F" & feedRateSlow
  ' Position Z for entry
  Code "G1G53Z-3.7"

  ' Then enter and stop and reposition
  Code "G1G53X1.55"
  Code "G1G53Z-3.52"

  ' Grab it and remove it from hanger
  Code "G1G53X1.04"
  Code "G1G53Z-2.75"

  ' Move to Z Starting Position
  Code "F" & feedRateFast
  Code "G0G53Z" & autoZJigSafeZ  

  Code "G0G53X" & xCenter
  Code "G0G53Z-1.75"
  
  While IsMoving()      
    Sleep 100
  Wend

  retrieveAutoZJig = True
End Function

' Function that places the auto z jig back in it's holder
' Params:
Function putBackAutoZJig() As Boolean
  ' Putting the auto z jig back into it's hanger
  Code "F" & feedRateFast ' Feed Rate
  
  ' Position to put back
  Code "G0G53Z" & autoZJigSafeZ
  Code "G0G53X5.5Y" & autoZJigY
  Code "G0G53X6.5Y" & autoZJigY ' Pull Wire straight
  Code "G0G53X1Y" & autoZJigY
  Code "G0G53Z-2.5"

  ' Begin put back
  Code "F" & feedRateSlow
  Code "G1G53Z-3.5"

  ' Pull away, leaving clip
  Code "G1G53X2.5"

  Code "F" & feedRateFast
  Code "G0G53Z" & autoZJigSafeZ 
  
  While IsMoving()      
    Sleep 100
  Wend
   
  putBackAutoZJig = True
End Function

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
    ' Set variable to 1 saying this We DON'T want z routine validation
    Call SetOEMDRO (2043, 1)
  Else
    ' Set variable to 0 saying this We WANT z routine validation
    Call SetOEMDRO (2043, 0)
  End If

  'Speak("Moving to new z index")
  Code "G0X " & zX & "Y" & zY
  While IsMoving()      
    Sleep 100
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

