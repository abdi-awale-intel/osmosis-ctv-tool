'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run SQL query via UNIQE and write JSL output
' Author: Anirudh Modi (September 26, 2011)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

datasource = "D1D_PROD_MARS"
sql = "select * from a_lot_at_operation where rownum <= 100"

StartInitTime = Timer

msg = "SQL => " & sql & vbCrLf & vbCrLf
outputDateFormat = ""
uniqeServerName = ""
authMode = "IWA"
userId = ""
password = ""

' Initialize UNIQE DataService factory
Set factory = CreateObject("Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory")

jslFile = factory.SaveQueryResultsToJslFileWithAuth(datasource, sql, outputDateFormat, uniqeServerName, authMode, userId, password)
 
Set fso = CreateObject("Scripting.FileSystemObject")
set file = fso.OpenTextFile(jslFile, 1)
jsl = file.ReadAll
call fso.CopyFile(jslFile, "Output.jsl")

msg = msg & jsl

print msg

' Function to print message
sub print(s)
    Wscript.Echo s
end sub

' Function to get UNIQE client attribute
function GetClientAttribute(attributeList, attrName)
   GetClientAttribute = ""
   for each attr in attributeList
       if (lcase(attr.AttributeName) = lcase(attrName)) then
            GetClientAttribute = attr.AttributeValue
            exit for
       end if
   next
end function

' Function to set UNIQE client attribute
sub SetClientAttribute(attributeList, attrName, attrValue)
   for each attr in attributeList
       if (lcase(attr.AttributeName) = lcase(attrName)) then
            attr.AttributeValue = attrValue
       end if
   next
end sub
