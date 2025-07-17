'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to run test C# Script
' Author: Anirudh Modi (Oct 28, 2012)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

' Initialize UNIQE DataService factory
dim factory, result, scriptCode, argument
Set factory = CreateObject("Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory")

Set fso = CreateObject("Scripting.FileSystemObject")      
Set file = fso.OpenTextFile("C#Script\RunScriptSample.cs", 1, false)
scriptCode = file.ReadAll
file.Close

argument = "helloX"
result = factory.RunScript(scriptCode, argument)
print result

' Function to print message
sub print(s)
    Wscript.Echo s
end sub
