'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run SQL query via UNIQE and write output to CSV file
' Author: Anirudh Modi (July 1, 2014)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''
StartInitTime = Timer

dataSource = "D1D_PROD_ARIES"
sql = "select lot, lao_start_ww, lao_test_end_date_time from a_lot_at_operation where rownum <= 100"

' Initialize UniqeClientHelper class
Set helper = CreateObject("Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper")
helper.ConnectionString = "Site=BEST;MetaData=VBscript;DataSource=" & dataSource

Set uberTable = helper.GetUberTable(sql)

outputCsvFile = "Output.csv" ' Could explicitly specify full path here (if null, a temp file is generated)
delimiter = ","
append = false
datasource = "D1D_PROD_ARIES"
outputDateFormat = "yyyy/MM/dd HH:mm:ss" ' Can use ww for Intel work-week (i.e., WW27) or ww.w for Intel work-week with day (i.e., WW27.4)

file = uberTable.SaveToFile(outputCsvFile, delimiter, outputDateFormat, append, false)
msg = "Output CSV File = [" & file & "]" & VbCrLf & VbCrLf

msg = msg & "SQL => " & sql & VbCrLf & VbCrLf   
msg = msg & "Total time = " & (Timer - StartInitTime) & " seconds" & VbCrLf

print msg

' Function to print message
sub print(s)
    Wscript.Echo s
end sub

