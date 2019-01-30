Code "G90" ' Absolute Position
Dim safeZ As Double
Dim feedRateFast As Integer
Dim feedRateSlow As Integer
Dim jigY As Double
safeZ = -1.0
feedRateFast = 120
feedRateSlow = 20
jigY = 14.51

' Status variable, 777 is finished correctly
SetOEMDRO(2061,0)

' Instruction Variable on whether to retreive or to put away
' Variables other than 0 and 1 are used to ensure the operation is truly intentional
'   5545 = Retrieve
'   5575 = Put Away
Dim retrieve As Boolean
if GetOEMDRO(2060) = 5545 Then
  retrieve = true
elseif GetOEMDRO(2060) = 5575 Then
  retrieve = false
else
  Code "(ERROR: OEM DRO 2060 is " & GetOEMDRO(2060) & " and is invalid)"
  Begin Dialog ButtonSampleTest 16,32,150,96,"ERROR"
    Text 10,12,130,60, "ERROR: OEM DRO 2060 input is invalid"
    OKButton 30,70,40,14
    'CancelButton 80, 70,40,14
  End Dialog
  Dim Dlg1 As ButtonSampleTest
  Dialog Dlg1
  Call SetOEMDRO (2060, 0)
  Exit Sub
End If
' Very important! Reset back to normal state
Call SetOEMDRO (2060, 0)

if retrieve Then
  ' Retrieveing the auto z jig
  Code "F" & feedRateFast ' Feed Rate
  Code "G53Z" & safeZ
  Code "G53X2.45Y" & jigY
  Code "G53Z-3.0"

  Code "F" & feedRateSlow
  ' Position Z for entry
  Code "G53Z-3.7"

  ' Then enter and stop and reposition
  Code "G53X1.55"
  Code "G53Z-3.52"

  ' Grab it and remove it from hanger
  Code "G53X1.04"
  Code "G53Z-2.75"

  ' Move to Z Starting Position
  Code "F" & feedRateFast
  Code "G53Z" & safeZ
  SetOEMDRO(2061,777)
else
  ' Putting the auto z jig back into it's hanger

  ' Position to put back
  Code "G53Z" & safeZ
  Code "G53X1.1Y" & jigY
  Code "G53Z-2.5"

  ' Begin put back
  Code "F" & feedRateSlow
  Code "G53Z-3.5"

  ' Pull away, leaving clip
  Code "G53X2.5"

  Code "F" & feedRateFast
  Code "G53Z" & safeZ
  SetOEMDRO(2061,777)
End If