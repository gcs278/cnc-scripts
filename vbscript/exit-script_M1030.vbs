' Get Job Time, stored in 2020 and 2021
SetUserDRO(2021, Timer()) 
Dim Tnow As Single
Dim Telap As Single
Dim Tref As Single
Dim Tthen As Single
Tnow = GetUserDRO(2021)
Tthen = GetUserDRO(2020)
Telap = ((Tnow-Tthen)/60)
TotTime = Telap
TimeConvert(TotTime)

' Current date&time
curDateNice =  MonthName(Month(Date)) & " " & Day(Date) & "_" & Year(Date) & "_" & Time
curDate =  Month(Date) & "/" & Day(Date) & "/" & Year(Date)
timeString = Time

' Get filename
Dim fullFileNameString As String
fullFileNameString = FileName()
Dim filesys, fileNameString
Set filesys = CreateObject("Scripting.FileSystemObject")
fileNameString = filesys.GetBaseName(fullFileNameString)

' Add data to jobs file
Dim dataFile
dataFile = "C:\Users\Shop\Google Drive\GS_Custom_Woodworking\CNC_Data\job_stats_data.csv"
'dataFile = "C:\Mach3\atest.csv"
If Not filesys.FileExists( dataFile ) Then
	filesys.CreateTextFile( dataFile )
End If
Open dataFile For Append As #1   ' Open to write file.
	Print #1, """" & fileNameString  & """,""" & Converted_Time & """,""" & curDate & """,""" & timeString & """,""" & GetParam("TotalHours") & """"
Close #1

'objFSO.OpenTextFile(dataFile)
'Set csvFile = objFSO.OpenTextFile(dataFile, 8, False, True)
'csvFile.WriteLine(fileNameString & "," & ConvertedTime & "," & curDate & "," & timeString )

' Generate message
EmailSubject = "CNC Job Finished!"
EmailBody = "The job " & fileNameString & " has just completed.<br>" & vbCRLF & _
        Converted_Time

Set objFSO=CreateObject("Scripting.FileSystemObject")
Dim PasswordFilePath As String
Set PasswordFilePath = "c:\Mach3\gmail-password.txt"
If Not objFSO.FileExists(PasswordFilePath) Then
        Code "(ERROR: " & PasswordFilePath & " does not exist)"
        Exit Sub
End If

' Password File
Set passwordFile = objFSO.OpenTextFile(PasswordFilePath)
Dim password As String
password = passwordFile.ReadLine

Const EmailFrom = "self@gmail.com"
Const EmailFromName = "Grant Spence"
Const EmailTo = "7579994134@mms.att.net"
Const SMTPServer = "smtp.gmail.com"
Const SMTPLogon = "gscustomwoodworking@gmail.com"
Const SMTPSSL = True
Const SMTPPort = 465

Const cdoSendUsingPickup = 1    'Send message using local SMTP service pickup directory.
Const cdoSendUsingPort = 2  'Send the message using SMTP over TCP/IP networking.

Const cdoAnonymous = 0  ' No authentication
Const cdoBasic = 1  ' BASIC clear text authentication
Const cdoNTLM = 2   ' NTLM, Microsoft proprietary authentication

' First, create the message

Set objMessage = CreateObject("CDO.Message")
objMessage.Subject = EmailSubject
objMessage.From = """" & EmailFromName & """ <" & EmailFrom & ">"
objMessage.To = EmailTo
objMessage.HTMLBody = EmailBody

' Second, configure the server

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/sendusing") = 2

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/smtpserver") = SMTPServer

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/smtpauthenticate") = cdoBasic

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/sendusername") = SMTPLogon

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/sendpassword") = password

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/smtpserverport") = SMTPPort

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/smtpusessl") = SMTPSSL

objMessage.Configuration.Fields.Item _
("http://schemas.microsoft.com/cdo/configuration/smtpconnectiontimeout") = 10

objMessage.Configuration.Fields.Update
'Now send the message!
'On Error Resume Next
' objMessage.Send
' objMessage.To = "gcs278@vt.edu"
' objMessage.Send
objMessage.To = "7579994134@mms.att.net"
objMessage.Send

' Cole ESVA
' Dim gcodeFile As String
' Dim gcodeFileBase As String
' gcodeFileBase = GetloadedGCodeFileName()
' gcodeFile = GetloadedGCodeDir() & gcodeFileBase
' If InStr(gcodeFile,"ESVA_REV_A1") <> 0 Then
'   objMessage.To = "7576930266@mms.att.net"
'   objMessage.Send
' End If

'If Err Then
'    MsgBox Err.Description,16,"Error Sending Mail"
'Else 
'    MsgBox "Mail was successfully sent !",64,"Information"
'End If	

Sub TimeConvert (Decimal_Time)
        Hours = (Int(Decimal_Time) / 60)
        Minutes = (Decimal_Time - ((Int(Hours)*60)))    
        seconds = (Minutes - Int(Minutes) ) * 60
        Converted_Time = Int(Hours) & "h " & Int(Minutes) & "m " & Int(seconds) & "s"   
        End Sub       

End      
