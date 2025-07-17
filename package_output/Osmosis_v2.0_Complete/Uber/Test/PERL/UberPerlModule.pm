package UberPerlModule;

use Win32::OLE;
$Win32::OLE::Warn = 3;

sub GetDataFromUber {
    $outputCsvFile = ''; 
    $delimiter = "z\&\^0y";
    $append = 0;
    $datasource = $_[1];  # argument 2 is datasource
    $outputDateFormat = "yyyy/MM/dd HH:mm:ss"; 
    $site = "";
    $sql = $_[0] ; # argument 1 is sql


    #Initialize UNIQE DataService factory, operation and query
    $factory = Win32::OLE->new("Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory") ;
    $oper = Win32::OLE->new("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation");
    $query = Win32::OLE->new("Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query");
        
    #Populate the Query and add it to the Operation
    $query->{SQLStatement} = $sql;
    $query->{DataSource} = $datasource ;#Data-source to run query against
    $query->{TimeOutInSeconds} = 600;
    $oper->AddQuery($query);
     
    #Get AppInfo and Attribute List defined for UNIQE client
    $appInfo = $factory->GetAppInfo("UNIQE") ;

    #Get client proxy
    $proxy = $factory->Initialize($appInfo);
    
    #Set the call-level time-out. Uber will thrown an exception if the call does not complete in the time specified
    #$proxy->{CallTimeOutInSeconds} = 600;

    #Run the query and get the handle to the IUberTable instance which contains the query result
    $uberTable = $proxy->ExecuteOperForCOM($oper);
    # Write the output to temporary csv file
    $file = $uberTable->SaveToFile($outputCsvFile, $delimiter, $outputDateFormat, $append, 0);

    #Close the client proxy, else this will lead to handle leaks on server-sid
    $proxy->Close;

    # Read the data from csv file to perl table structure.
	  open (FH, $file) || die ("Could not open $file!");
	
    my @table;
    my @header;	
    $header_line= 1;
    while ($line = <FH>)
    {
      chomp;
      if ($header_line)
      {
        push @header,[split 'z\&\^0y', $line];
        $header_line = 0;
      }
      else
      {
        push @table, [split 'z\&\^0y', $line];
      }
    }
    close (FH);

    # Delete the temp CSV File
    unlink $file;
    
    #Return the result to client.
    return (\@header,\@table);

}

# Just to make sure the module is loaded correctly in pl file.
1;