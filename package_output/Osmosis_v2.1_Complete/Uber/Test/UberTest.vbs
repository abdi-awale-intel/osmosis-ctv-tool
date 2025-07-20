'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run SQL query via UNIQE
' Author: Anirudh Modi (July 1, 2014)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

StartInitTime = Timer

dataSource = "D1D_PROD_ARIES"
sql = "select lot, lao_start_ww, lao_test_end_date_time from a_lot_at_operation where rownum <= 10"

msg = msg & "DataSource = " & dataSource & VbCrLf
msg = msg & "SQL = " & sql & VbCrLf & VbCrLf

' Initialize UniqeClientHelper class
Set helper = CreateObject("Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper")
helper.ConnectionString = "Site=BEST;Metadata=VBScript sample;DataSource=" & dataSource

StartTime = Timer

' Run the query and get the handle to the IUberTable instance which contains the query result
Set uberTable = helper.GetUberTable(sql)	
' Parse IUberTable and convert it to string for display
msg = msg & ConvertUberTableToString(uberTable)

'call uberTable.SaveToCsvFile("C:\Temp\uberOut.csv", "yyyy/MM/dd HH:mm:ss.fff")

msg = msg & "Scan value was " & scan & VbCrLf & VbCrLf
msg = msg & "Total time = " & (Timer - StartInitTime) & " seconds" & VbCrLf

print msg

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
