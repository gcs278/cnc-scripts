Option Explicit
Dim DEBUG
DEBUG = False

Dim tmpDir As String
tmpDir = "c:\Mach3\argFiles\"

' Start file tell python to start GUI
Dim mixerStartFile As String
' End file tells Mach3 to load Gcode or just quit blocking
Dim mixerDoneFile As String


Set objFSO=CreateObject("Scripting.FileSystemObject")

' Write to a file that python will monitor, and execute when created
Dim timeString As String
timeString = Format(Date,"yyyymmdd") & Format(Time,"HHMMSS")
mixerStartFile=tmpDir & "gcodeMixer." & timeString & ".txt"
mixerDoneFile=mixerStartFile & ".DONE"
Set objFile = objFSO.CreateTextFile(mixerStartFile,True)

' Now we wait for python to create our end file
Dim fileExists As Boolean
fileExists = False
While fileExists = False
  fileExists = objFSO.FileExists(mixerDoneFile)
  Sleep 1000
Wend

' Read end file for GCode file we should load now
Set f = objFSO.OpenTextFile(mixerDoneFile,1)
Dim gcodeFile As String
Do While Not f.AtEndOfStream
     gcodeFile = f.ReadLine()
Loop
f.Close
Set objFileToRead = Nothing


LoadFile(gcodeFile)


'If GetloadedGCodeFileName() <> tempGcodeFileBase Then
  'Code "(Failed to load GCode, do it by hand)"
  'Exit Sub
'End If



