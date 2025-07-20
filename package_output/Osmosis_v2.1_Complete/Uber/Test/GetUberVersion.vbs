'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to check Uber Client Version
' Author: Anirudh Modi (Oct 17, 2013)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''
ON ERROR RESUME NEXT
dim factory, version
Set factory = CreateObject("Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory")
version = factory.GetVersion
Wscript.Echo "Version = [" & version & "]"