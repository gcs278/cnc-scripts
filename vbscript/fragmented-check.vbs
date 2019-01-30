' Check we are running the right gcode
Dim gcodeFilePathFull As String
Dim gcodeFileName As String
Dim gcodeFileNameNoExtension As String
Dim gcodeFileMainDir As String
gcodeFileMainDir = GetloadedGCodeDir()
gcodeFileName = GetloadedGCodeFileName()
gcodeFilePathFull = gcodeFileMainDir & gcodeFileName
Print(GetloadedGCodeDir)

Dim dirs (10) As String 
Dim temp As String
temp = GetloadedGCodeDir
Dim count
count = 0
While temp <> "" And count < 10
  temp = Right(temp, Len(temp) - Len(Left(temp,InStr(temp,"\"))))
  Dim CurDir As String
  CurDir = Left(temp,InStr(temp,"\")-1)
  If InStr(1,Left(temp,Len(temp)-1),"\") = 0 Then
    temp = ""
  End If
  dirs (count) = CurDir
  count = count + 1
Wend

' If we aren't directly in a *_Signs Dir
' and the dir name has fragments
If dirs(count-2) <> "GCode" And InStr(dirs(count-1), "fragment") = 0 Then
  Code"(ERROR: Don't run non-fragmented files!)"
End If


