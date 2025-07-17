'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run SQL query via UNIQE
' Author: Anirudh Modi (July 1, 2014)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

StartInitTime = Timer

dataSource = "UNIQE_METADATA_GENERIC"
sql = "select TOP 10 * from DataSources"

msg = msg & "DataSource = " & dataSource & VbCrLf
msg = msg & "SQL = " & sql & VbCrLf & VbCrLf

' Initialize UniqeClientHelper class
Set helper = CreateObject("Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper")
helper.ConnectionString = "Site=BEST;DataSource=" & dataSource

' Define total number of iterations
iterations = 1
StartTime = Timer

For iter = 1 to iterations
   
    ' Run the query and get the handle to the IUberTable instance which contains the query result
	Set uberTable = helper.GetUberTable(sql)
	
	' Parse IUberTable and convert it to string for display
	'msg = msg & ConvertUberTableToString(uberTable)
	
	' Convert IUberTable to ADODB.Recordset (ideal for VBScript usage)
    Set recordset = uberTable.ConvertToRecordset()
    msg = msg & ConvertRecordSetToString(recordset) & VbCrLf

    'call uberTable.SaveToCsvFile("C:\Temp\uberOut.csv", "yyyy/MM/dd HH:mm:ss.fff")

Next ' End iteration

ElapsedTime = Timer - StartTime
AverageTimePerIteration = ElapsedTime / Iterations
msg = msg & "AverageTimePerIteration is " & AverageTimePerIteration & " seconds for " & Iterations & " iterations" & VbCrLf & VbCrLf
msg = msg & "Scan value was " & scan & VbCrLf & VbCrLf
msg = msg & "Total time = " & (Timer - StartInitTime) & " seconds" & VbCrLf

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

' Function to convert UberTable to string (for display)
Function ConvertUberTableToString(uberTable)

    Dim msg, numCols, col, colName, typeString, row, i, j
    
    msg = msg & "Type of table is " & typename(uberTable) & VbCrLf

    numCols = uberTable.ColumnCount
    msg = msg & " Number of columns is " & numCols & VbCrLf & VbCrLf

    For i = 0 to (numCols-1)
          Set col = uberTable.GetColumnByIndex(i)
          colName = col.Name
          typeString = col.TypeName
          msg = msg & colName & vbTab
    Next

    msg = msg & VbCrLf
    row = 0
 
    ' Retrieve row data from IUberTable instance
     do While True

            Dim curChunkData
            Dim numRowsInChunk

            curChunkData = uberTable.GetNextChunk2D()
            numRowsInChunk = UBound(curChunkData, 1) + 1

            if numRowsInChunk = 0 Then
                  Exit do ' no data exists, exit do loop
            End if

            row = row + numRowsInChunk

            For i = 0 to numRowsInChunk - 1
                 For j = 0 to numCols - 1
                    val = curChunkData(i,j)
                    msg = msg & val & vbTab
                 Next
                 msg = msg & VbCrLf
            Next
            
   Loop ' End Do Loop

   msg =  msg & VbCrLf & "Num rows is " & uberTable.RowCount & VbCrLf & VbCrLf

   ConvertUberTableToString = msg
   
End Function

' Function to print message
Sub print(s)
    Wscript.Echo s
End Sub
