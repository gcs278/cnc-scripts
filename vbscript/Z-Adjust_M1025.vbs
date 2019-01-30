' Z Offset Adjustment script
' adjustment should be passed via OEM 2080

Dim currentZ, newZ, offset as Double
Dim prevAbsZ, realOffset, realOffsetRounded, offsetDiff as Double

' Note: Use DRO 178, 179, 180 for X, Y, Z
'       DRO 800, 801, 803 is the CURRENTLY display value, could be machine coordinates!
currentZ = GetOEMDRO(180)
offset = GetOEMDRO(2080)

' Validation
if offset = 0 or offset < -0.01 or offset > 0.01 Then
  Code "(Error: OEM 2080 for offset is " & offset & " which is out of acceptable range.)"
  Exit sub
elseif GetOEMLED(804) Then
  Code "(Error: Refusing to run while GCODE is running...)"
  Exit Sub

' This for some reason doesn't work...
'elseif IsMoving() Then
  'Code "(Error: Refusing to run while machine is moving...)"
  'Exit Sub
End If

prevAbsZ = GetABSPosition(2)
newZ = currentZ + offset
'print currentZ
' Move the Z Axis
Code "G90"
Code "G1Z" & newZ
' Wait for move to complete
While IsMoving()
  Sleep(100)
Wend

realOffset = GetABSPosition(2) - prevAbsZ
offsetDiff = Abs(realOffset - offset)
realOffsetRounded = round(realOffset,4)


if realOffsetRounded = 0.00 Then
  Code "(ERROR: Machine didn't move!)"
  'Exit Sub
End If


' Set the Z DRO to our previous value (so DRO effectively doesn't change, but Z position does)
Call SetOEMDRO (180,currentZ)

' Update Z offset counter
Dim currentOffset As Double
currentOffset = GetOEMDRO(2050)
Call SetOEMDRO(2050, currentOffset + offset)

Dim direction
if realoffset > 0 Then
  direction = "RAISED"
else
  direction = "LOWERED"
End If

Code "(Z-Index " & direction & " by " & offset & ")"
if offsetDiff > 0.001 Then
  Code "(WARNING: The machine didn't move quite as expected, it moved: " & realOffset &")"
End If