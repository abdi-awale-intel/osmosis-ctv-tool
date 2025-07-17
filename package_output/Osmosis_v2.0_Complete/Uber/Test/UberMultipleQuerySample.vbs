'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run multiple SQL queries via UNIQE
' Author: Anirudh Modi (July 1, 2014)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

StartInitTime = Timer

' Initialize UniqeClientHelper class
Set helper = CreateObject("Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper")
helper.ConnectionString = "Site=BEST;MetaData=Multi-query sample vbscript"

ElapsedTimeForInit = Timer - StartInitTime

Dim StartTime, ElapsedTime, msg

msg = msg & "Client proxy initialization time is " & ElapsedTimeForInit & " seconds [AuthMode = " & cstr(helper.Authentication) & "]" & VbCrLf & VbCrLf

StartTime = Timer

' Create a new Uber objects
Dim job, oper1, oper2, query1, query2, tables

Set job = CreateObject("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.UniqeJob")

Set oper1 = CreateObject("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation")
Set oper2 = CreateObject("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation")

Set query1 = CreateObject("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query")
Set query2 = CreateObject("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query")

query1.DataSource = "D1D_PROD_ARIES"
query1.SQLStatement = "select * from A_LOT where ROWNUM <= 100"
query1.TimeOutInSeconds = 10 

query2.DataSource = "F32_PROD_ARIES" ' Can be any other data-source as well (i.e., F32_PROD_ARIES)
query2.SQLStatement = "select * from A_LOT_AT_OPERATION where ROWNUM <= 200"
query2.TimeOutInSeconds = 30

oper1.AddQuery(query1)
oper2.AddQuery(query2)

job.AddOperation(oper1)
job.AddOperation(oper2)

' Set the call-level time-out. Uber will thrown an exception if the call does not complete in the time specified
helper.TimeOutInSeconds = 600

set tables = helper.ExecuteJobForCOM(job) ' Asynchronous, returns immediately

'Save output tables
' If you simply want to wait until output from Operation 1 is completely received, call tables(0).GetColumns()
' Check tables(0).IsDataAvailable to see if data is available for processing

' Blocks until the output from Operation 1 is completely received and converted to CSV
call tables(0).SaveToFile("Output1.csv", ",", "yyyy/MM/dd HH:mm:ss", false, false)

' Blocks until the output from Operation 2 is completely received and converted to CSV
call tables(1).SaveToFile("Output2.csv", ",", "yyyy/MM/dd HH:mm:ss", false, false)

msg = msg & VbCrLf & "# of rows for oper 1 = " & tables(0).RowCount
msg = msg & VbCrLf & "# of rows for oper 2 = " & tables(1).RowCount

ElapsedTime = Timer

msg = msg & VbCrLf & VbCrLf & "Total time taken = " & (ElapsedTime - StartTime) & " seconds."

print msg

' Function to print message
sub print(s)
    Wscript.Echo s
end sub
