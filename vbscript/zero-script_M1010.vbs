'     Z-AXIS TOUCHPLATE ZERO
'     Author: Kent Janes
'     October 11, 2009
'     Version 1.4

'     This routine is used to zero the Z-axis using a touch probe.
'     The probe must be ungrounded when this routine starts.
'     The user is given 15 seconds to touch the probe to the bit.
'     Once the bit is touched, the z axis will be moved up then down by a small 
'     amount to let the user know that the touch was successful. The routine 
'     will then pause for 1/2 second to allow the user to move the probe to the
'     top of the workpiece. The system will then move the probe downward until 
'     it contacts the touchplate. Once touched,the z-axis DRO is set to the 
'     plate thickness (specified by the user and entered on the Mach screen). 
'     The z-axis will then be moved upward by the distance specified as 
'     Final_Back_Off constant.
  
Dim Final_Backoff 
Dim Inital_Backoff
Dim Probing_feed_rate
Dim Plate_Offset
Dim Touched_Flag
Dim Initial_Incremental_Flag
Dim Initial_Machine_Coordinates_Flag
Dim Initial_G_State
Dim Initial_Feed_Rate
Dim Initial_Back_Off
Dim Final_Back_Off
Dim New_Z
Dim i
Dim setZindex
setZindex = GetOEMDRO(2037)

Dim isInternalCall
isInternalCall = GetOEMDRO(2042)

Dim skipVerify
skipVerify = GetOEMDRO(2043)


' First check if loaded gcode has multi z in the name
Dim gcodeFile As String
Dim gcodeFileBase As String
gcodeFileBase = GetloadedGCodeFileName()
gcodeFile = GetloadedGCodeDir() & gcodeFileBase
If InStr(gcodeFile,"MULTIZ") <> 0 and isInternalCall = 0 Then
  MsgBox "Error: This file is marked to use the multi z process. Press the MULTI Z button, Mom."
  Exit Sub
End If
'     Initialize constants.
   Speak("Connect the clip to the spindle")
   Speak("Tap cutter with touch plate")
   
   Final_Back_Off = 0.20
   Initial_Back_Off = 0.02
   Probing_Feed_Rate = 8
   
'     Display a message and exit if the user has not specified a plate offset.

   Plate_Offset = 0.745 'GetUserDRO(1151)
   If Plate_Offset <= 0 Then
      Code "(A positive value must be entered for the Plate Offset.)"
      Call SetUserDRO(2035, 2)
      Exit Sub
   End If
   
'     Test to see if the touchplate is already grounded or faulty.
'     Display a message and exit if it is grounded.

   If GetOEMLed (825) <> 0 Then       
      Code "(Touchplate is grounded...Trying again....)"
      Sleep 2000
      If GetOEMLed (825) <> 0 Then
        Code "(Touchplate is grounded, still. Exiting.)"
        Call SetUserDRO(2035, 2)
        Exit Sub
      End If
   End If
   
'   Set the Z-Setter Plate to Material Offset DRO to -999 so that the
'   Z-Setter Tool Change routine will be able to detect that the users
'   is trying to run it when they should not. Some users won't have this
'   DRO so skip this if an error occurs.

   On Error Resume Next
   Call SetUserDRO(1102,-999) 
   On Error GoTo 0
   
 '    Loop for a maximum of 15 seconds to let the user touch the probe to the bit.
 '    Exit if the user does not touch the probe to the bit within 15 seconds.
 
   Touched_Flag = False
   If skipVerify = 1 Then
      Touched_Flag = True
   Else 
      Code "(Briefly touch the probe to the bit to start probing for zero.)"
      For i = 1 To 600
         If GetOEMLed (825) <> 0 Then
            Touched_Flag = True 
            Exit For
         End If
         Sleep 25
      Next i
   End If

   If Touched_Flag = False Then
      Code "(The touchplate routine timed out.)"
      Speak "Time out"
      Call SetUserDRO(2035, 2)
      Exit Sub
   End If
 
'     Save the incremental mode, the machine coordinates mode,
'     the G0/G1 state, and the feed rate. Then set the system to 
'     absolute mode (G90) and to work coordinates mode.

   Initial_Incremental_Flag = GetOEMLed(49)
   Initial_Machine_Coordinates_Flag = GetOEMLEd(16)
   Initial_G_State = GetOEMDRO(819)
   Initial_Feed_Rate = GetOEMDRO(818)
   
   DoOEMButton (180)
   Code "G90"
   While IsMoving()      
      Sleep 100
   Wend
   
'     Move the z-axis upward by the Inital_Back_Off_Amount and then back down.
'     This lets the user know tha they made the inital contact that starts the 
'     final probing.
 
   ' Don't do that tap shaky thing
   If skipVerify = 0 Then
      New_Z = GetOEMDRO(802) + Initial_Back_Off
      Code "G0"
      While IsMoving()      
         Sleep 100
      Wend
      Code "G0 Z" & New_Z
      While IsMoving()      
         Sleep 100
      Wend

      New_Z = New_Z - Initial_Back_Off
      Code "G0 Z" & New_Z
      While IsMoving()      
         Sleep 100
      Wend
   End If

'     Change the feed rate to the Probing_Feed_Rate and start probing downward 
'     after a 1/2 second pause. Also place in G1 mode.
  
   New_Z = GetOEMDRO(802) - 6
   Code "F" & Probing_Feed_Rate 
   Code "G1"
   While IsMoving()      
      Sleep 100
   Wend
   Sleep 500      
   Code "G31Z" & New_Z
   While IsMoving()      
      Sleep 100
   Wend
   
'     Move back to the hit point in case there was overshoot.
'     Set the z-DRO to the Plate_Offset. Display a message
'     stating the z-axis is zeroed. Return to the original
'     feed rate.

   New_Z = GetVar(2002)
   Old_Z = New_Z
   Code "G1 Z" & New_Z
   While IsMoving ()
      Sleep 100
   Wend

   ' Only store if we have varaible setZIndex to store
   If setZindex = 1 Then
     Call SetOEMDRO (802,Plate_Offset)
   End If
   Dim zAbsolute
   zAbsolute = GetOEMDRO(85)
   Call SetOEMDRO (2036,zAbsolute)
   sleep 250
   Code "G0"
   While IsMoving()      
      Sleep 100
   Wend

   ' Very important! If not setting, then use absolute position, G53
   If setZindex = 1 Then
     New_Z = Plate_Offset + Final_Back_Off
     Code "G0 Z" & New_Z
   Else
     New_Z = zAbsolute + Final_Back_Off
     Code "G0 G53 Z" & New_Z
   End If

   If setZindex = 1 Then
      Code "(Z Zeroed. The offset is " & Old_Z & ")"
      Speak("Successfully stored the z index")
   Else
      Code "(Z NOT Zeroed)"
      Speak ("NO ZERO")
   End If
   While IsMoving ()
      Sleep 100
   Wend

'     Restore the feed rate, the incremental/absolute mode setting, the 
'     work coordinates/machine coordinates setting, and the G0/G1 setting
'     to what they were in the beginning.

   Code "F" & Initial_Feed_Rate

   If Initial_Incremental_Flag = True Then
      Code "G91"
   End If
   
   If Initial_Machine_Coordinates_Flag = True Then
      DoOEMButton(179)
   End If

   If Initial_G_State = 0 Then
      Code "G0"
   Else
      Code "G1"
   End If 

   ' Set the DRO so other programs monitoring this will know
   Call SetUserDRO(2035, 1)      
