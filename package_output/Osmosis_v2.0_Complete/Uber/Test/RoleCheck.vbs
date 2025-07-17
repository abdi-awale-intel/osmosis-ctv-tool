'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run SQL query via UNIQE and convert to RecordSet
' Author: Anirudh Modi (July 1, 2014)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

dataSource = "UNIQE_ROLE_HELPER"
sql = "select * from RoleInfo where Site IN ( 'ActiveDirectory' ) AND User IN ( 'jmclarke' )"

msg = msg & "DataSource = " & dataSource & VbCrLf
msg = msg & "SQL = " & sql & VbCrLf & VbCrLf

' Initialize UniqeClientHelper class
Set helper = CreateObject("Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper")
helper.ConnectionString = "DataSource=" & dataSource

' Run the query and get the handle to the IUberTable instance which contains the query result
Set uberTable = helper.GetUberTable(sql)
		
' Convert IUberTable to ADODB.Recordset (ideal for VBScript usage)
Set recordset = uberTable.ConvertToRecordset()
msg = msg & ConvertRecordSetToString(recordset) & VbCrLf

print msg

' Function to convert the recordset to string (for display)
Function ConvertRecordSetToString(rs) 

Dim output, field, j         
output = ""

    if rs.Fields.Count > 0 Then
        rs.MoveFirst()
        ' Column Header
         For j = 0 to (rs.Fields.Count-1)
		    	  Set field = rs.Fields(j)
		    	  output = output & field.Name & " "
		 Next
		  output = output & VbCrLf
		  
		  ' Row Data
        While Not rs.EOF 
                For j = 0 to (rs.Fields.Count-1)
		    	  Set field = rs.Fields(j)
		          output = output & field & " "
                Next
                rs.MoveNext()
               output = output & VbCrLf
         wend
     End if

ConvertRecordSetToString = output

End Function

' Function to print message
Sub print(s)
    Wscript.Echo s
End Sub