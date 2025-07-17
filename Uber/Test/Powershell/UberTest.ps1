param (
$dataSource = "D1D_DEV_PCSA", #Data-source to run query against
$sql = "Insert INTO TESTXTAB (CNT, TYP, APP) Values (:1, :2, :3)",
$sql_p = @("1203,1204,1205","JQ-UBER1,JQ-UBER2,JQ-UBER3","JQ-A1,JQ-A2,JQ-A3"),
$site ="RF3STG", 
$authMode = "UPWD", 
$userId = "PCSA", 
$password = "PCSA",
$scan = 1, # Define whether each cell data in output should be scanned
$iterations = 1, #Define total number of iterations
$mode = 2 # 0: RunQuery; 1:RunQueryDataTable; 2:RunQueryParameters
)

Set-PSDebug -Strict

# Function to get UBER client attribute
function GetClientAttribute ($attributeList,$attrName){
	$a = ""
	foreach ($item in $attributeList) {
		if ($item.AttributeName -ieq $attrName) {
			$a = $item.AttributeValue
			break
		}
	}
	return $a
}

# Function to set UBER client attribute
function SetClientAttribute ($attributeList,$attrName,$attrValue) {
	foreach ($item in $attributeList) {
		if ($item.AttributeName -ieq $attrName) {
			$item.AttributeValue = $attrValue
			break
		}
	}	
}

# Function to connect to UBER server (aka UNIQE)
function ConnectToUNIQE {
	# [Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient.UniqeClient]$proxy = $null
	#Initialize UNIQE DataService factory
	$factory = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory"

	#Get AppInfo and Attribute List defined for UNIQE client
	$appInfo = $factory.GetAppInfo("UNIQE")
	$attrList = $appInfo.ApplicationAttributeArrayList
	
	# change UBER server from default to specified one
	if ($site) {
		SetClientAttribute $attrList "Site" $site
	}
	
	# change connection mode to UBER server
	if ($authMode) {
		SetClientAttribute $attrList "AuthenticationMode" $authMode 
	}
	if ($authMode -ieq "UPWD") {
		if ($userId) {
			SetClientAttribute $attrList "UserId" $userId
		}
		if ($password) {
			SetClientAttribute $attrList "Password" $password
		}
	}
	
	#Get UNIQE client proxy
	$proxy = $factory.Initialize($appInfo)
	
	$a = GetClientAttribute $attrList "Site"
	$script:msgFunc = "connecting to UBER server [$a]`n"
	$a = GetClientAttribute $attrList "AuthenticationMode"
	$script:msgFunc += "[AuthMode = $a]`n"

	return $proxy
}

# Run READ query against data source
# retrieve data from UBER server into DataTable
function RunQuery {
	param(
		$sql,
		$dataSource
	)
	
	# Create a new Operation object
	$oper = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation" 

	# Create a new Query object
	$query = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query"
		
	# Populate the Query and add it to the Operation
	$query.SQLStatement = $sql
	$query.DataSource = $dataSource #Data-source to run query against
	$oper.AddQuery($query)
		
	# Run the query and get the handle to the IUberTable instance which contains the query result
	$uberTable = $proxy.ExecuteOper($oper)

	$script:msgFunc = "Type of table is " + $uberTable.GetType().Name + "`n"

	$numCols = $uberTable.ColumnCount
	
	$script:msgFunc += "Number of columns is $numCols `n"
	
	for ($i = 0; $i -lt $numCols; $i++) {
		$col = $uberTable.GetColumnByIndex($i)
		$colName = $col.Name
		$typeCodeInt = $col.TypeCodeInt
		
		$script:msgFunc += "	Column " + ($i+1) + " name is $colName, Type code is: $typeCodeInt`n"
	}
	
	$row = 0
	# Retrieve row data from IUberTable instance
	
	do {
		$curChunkData = $uberTable.GetNextChunk2D()
		$numRowsInChunk = $curChunkData.GetUpperBound(0) + 1
		
		if ($numRowsInChunk -eq 0) {
			break	#no data exists, exit do loop
		}
		
		$row += $numRowsInChunk
		
		if ($scan -eq 1) {
			for ($i = 0; $i -lt $numRowsInChunk; $i++) {
				for ($j = 0; $j -lt $numCols; $j++) {
					$val = $curChunkData[$i,$j]
				}
			}
		}
		
	} while ($true)
	
	$script:msgFunc += "Num of Rows is $row`n`n"
}
function RunQueryDataTable {
	param(
		$sql,
		$dataSource
	)

	[System.Data.DataTable] $data_table = New-Object System.data.DataTable
	
	# Create a new Operation object
	$oper = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation" 

	# Create a new Query object
	$query = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query"
		
	# Populate the Query and add it to the Operation
	$query.SQLStatement = $sql
	$query.DataSource = $dataSource #Data-source to run query against
	$oper.AddQuery($query)
		
	# Run the query and get the handle to the IUberTable instance which contains the query result
	$uberTable = $proxy.ExecuteOper($oper)

	$script:msgFunc = "Type of table is " + $uberTable.GetType().Name + "`n"

	$numCols = $uberTable.ColumnCount
	
	$script:msgFunc += "Number of columns is $numCols `n"
	
	for ($i = 0; $i -lt $numCols; $i++) {
		$col = $uberTable.GetColumnByIndex($i)
		$colName = $col.Name
		$typeCodeInt = $col.TypeCodeInt
		$data_table.Columns.Add($colName, $col.Type)
	
		$script:msgFunc += "	Column " + ($i+1) + " name is $colName, Type code is: $typeCodeInt`n"
	}
	
	$row = 0
	# Retrieve row data from IUberTable instance
	
	do {
		$curChunkData = $uberTable.GetNextChunk2D()
		$numRowsInChunk = $curChunkData.GetUpperBound(0) + 1
		
		if ($numRowsInChunk -eq 0) {
			break	#no data exists, exit do loop
		}
		
		$row += $numRowsInChunk
		

		if ($scan -eq 1) {
			for ($i = 0; $i -lt $numRowsInChunk; $i++) {
				$tmp = @()
				for ($j = 0; $j -lt $numCols; $j++) {
					$tmp += $curChunkData[$i,$j]
				}
				[Void]$data_table.Rows.Add($tmp)
			}
		}
		
	} while ($true)
	
	$script:msgFunc += "Num of Rows is $row`n`n"
	
	return $data_table
}
# Run Write query against data source
function RunQueryParmeters {
	param(
		$sql,
		$dataSource
	)
	
	# Create a new Operation object
	$oper = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation" 

	# Create a new Query object
	$query = New-Object -ComObject "Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query"
		
	# Populate the Query and add it to the Operation
	$query.SQLStatement = $sql
	$query.DataSource = $dataSource #Data-source to run query against
	
#	$a = @(1203,1204,1205)
#	$query.AddParameter("CNT", $a)
#	
#	$a = @("JQ-UBER1", "JQ-UBER2", "JQ-UBER3")
#	$query.AddParameter("TYP", $a)
#	
#	$a = @("JQ-A1", "JQ-A2", "JQ-A3")
#	$query.AddParameter("APP", $a)

	for ($index = 0; $index -lt $sql_p.Count; $index++) {
		$query.AddParameter(":$index", (($sql_p[$index] -split ",") | % {$_.trim("'")}))
	}
	
	$oper.AddQuery($query)
	
	$oper.EnableWrites = $true
	$oper.EnableSequentialModeForWrites = $true
	$oper.EnableTransactionModeForWrites = $true
		
	# Run the query and get the handle to the IUberTable instance which contains the query result
	$uberTable = $proxy.ExecuteOper($oper)

	$script:msgFunc = "Type of table is " + $uberTable.GetType().Name + "`n"

	$numCols = $uberTable.ColumnCount
	
	$script:msgFunc += "Number of columns is $numCols `n"
	
	for ($i = 0; $i -lt $numCols; $i++) {
		$col = $uberTable.GetColumnByIndex($i)
		$colName = $col.Name
		$typeCodeInt = $col.TypeCodeInt
		
		$script:msgFunc += "	Column " + ($i+1) + " name is $colName, Type code is: $typeCodeInt`n"
	}
	
	$row = 0
	# Retrieve row data from IUberTable instance
	
	do {
		$curChunkData = $uberTable.GetNextChunk2D()
		$numRowsInChunk = $curChunkData.GetUpperBound(0) + 1
		
		if ($numRowsInChunk -eq 0) {
			break	#no data exists, exit do loop
		}
		
		$row += $numRowsInChunk
		
		if ($scan -eq 1) {
			for ($i = 0; $i -lt $numRowsInChunk; $i++) {
				for ($j = 0; $j -lt $numCols; $j++) {
					$val = $curChunkData[$i,$j]
				}
			}
		}
		
	} while ($true)
	
	$script:msgFunc += "Num of Rows is $row`n`n"
}
$msgFunc = $null
$result = Measure-Command -Expression {
	$msg = "SQL => $sql`n"
	$proxy = ConnectToUNIQE
}

$elapsedTimeForInit = $result.TotalSeconds
$msg += "Client proxy initialization time is $elapsedTimeForInit seconds`n"
$msg += "`n$msgFunc`n"
$msgFunc = $null

$msg += "`n Starting table iteration - $iterations times against [$dataSource]`n`n"

$result = Measure-Command -Expression {
	for ($index = 0; $index -lt $iterations; $index++) {
		switch ($mode) {
			0 {
				RunQuery $sql $dataSource
				break
			}
			1 {
				$data = RunQueryDataTable $sql $dataSource
				break
			}
			2 {
				RunQueryParmeters $sql $dataSource
				break
			}
			default {
				RunQuery $sql $dataSource
			}
		}		
	}
}

# Close the client proxy, else this will lead to handle leaks on server-side
$proxy.Close()

$msg += " $msgFunc`n"
Write-Host $msg
Write-Host "Query average execution elapse time = " ($result.TotalSeconds/$iterations) " seconds`n"

trap {
	# You can access the error that got you here through the $_ variable
	Write-Host $_
	if ($proxy) {
		$proxy.Close()
	}
}

