SetUserDRO(2020, Timer()) 

'Dim currentZ, newZ
' Check if RAISE0.01 is in the file name, we will do the Raise if so
'If InStr(UCase(gcodeFileBase),"RAISE0.01") Then
  'currentZ = GetOEMDRO(802)
  'newZ = currentZ+0.01
  'print currentZ
  'Code "G90"
  'Code "G1Z" & newZ
  'Sleep 500
  'Call SetOEMDRO (802,currentZ)
  'Code"(SUCCESS: Raising 0.1)"
'End If

' Check if RAISE0.2 is in the file name, we will do the Raise if so
'If InStr(UCase(gcodeFileBase),"RAISE0.02") Then
  'currentZ = GetOEMDRO(802)
  'newZ = currentZ+0.02
  'print currentZ
  'Code "G90"
  'Code "G1Z" & newZ
  'Sleep 500
  'Call SetOEMDRO (802,currentZ)
  'Code"(SUCCESS: Raising 0.2)"
'End If