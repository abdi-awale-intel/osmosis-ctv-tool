'''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Sample VBScript to download files from FTP server via UNIQE
' Author: Anirudh Modi (Jul 1, 2013)
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''

dim site, dataSource, files, outputDirectory
site = "DEV"
dataSource = "D1D_DEV_TEST_FTP"
files = "*.out"
outputDirectory = "C:\Temp\TestFTP"


' Initialize UNIQE DataService factory
dim factory
Set factory = CreateObject("Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory")

dim downloadedFileList
Set downloadedFileList = factory.DownloadFilesUsingFTP(site, dataSource, files, outputDirectory)
'dim rs 'ADODB.Recordset
'Set rs = factory.GetFileInfoUsingFTP(site, dataSource, files)
'dim list 'ArrayList of string
'Set list = factory.GetFileListUsingFTP(site, dataSource, files)

Wscript.Echo "Downloaded " & downloadedFileList.RecordCount & " files."