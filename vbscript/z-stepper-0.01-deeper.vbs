Dim currentZ, newZ
currentZ = GetOEMDRO(802)
newZ = currentZ-0.01
'print currentZ
Code "G90"
Code "G1Z" & newZ
Sleep 500
Call SetOEMDRO (802,currentZ)

Code "(Z-Index LOWERED by 0.01)" 