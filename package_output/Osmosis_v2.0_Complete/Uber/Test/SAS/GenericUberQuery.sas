/******************************************* GenericUberQuery.sas ****************************************************/
/*   SAS Macro to invoke Uber Function SaveQueryResultsToCSVFileWithAuth()                                           */
/*   Author : Thomas S Leahy, STTD                                                                                   */
/*   Rev 1.0 11/27/13                                                                                                */
/*                                                                                                                   */
/*   Macro accepts arguments of WorkLibary to use, DataSource to query, SQL to run, output SAS dataset to create     */
/*   and a query timeout value.                                                                                      */
/*   The SQL should be provided as a macro variable                                                                  */
/*   The macro creates a global macro variable, UBEREXCEPTION. Calling code should check this = 0. If > 0, an error  */
/*   has occured and there will be no dataset created                                                                */
/*   Rev 1.1 03/07/14 : added a format of IBw.d ( used a width of 5 ) for the 9th arg to the DLL function, which is  */
/*                      the timeout value. Turned out it wasn't being passed correctly to the DLL without this       */
/*********************************************************************************************************************/

%Macro GenericUberQuery(
	 WorkLib		=	Work			/* SAS library the macro will operate in. Defaults to system Work lib if not provided */
	,DataSource		=					/* Database to connect to  . for eg D1D_PROD_XEUS                                     */
	,SQLCode		=					/* SQL code to submit. Should be a macro variable                                     */
	,OutData		=	QueryResults	/* SAS dataset to contain data from query. Defaults to "QueryResults"                 */
	,Timeout		=	7200			/* Default timeout value = 2 hrs													  */
);

	/* Create the SAS attribute data file to describe the Uber functions that will be called from the DLL */
	/* See SAS online help documentation for details :
	   Using SAS Software in your operating environment
		-> SAS 9.3 Companion for Windows
			-> Using SAS with Other Windows Applications
				-> Accessing External DLLs from SAS under Windows
	   See also : http://www.nesug.org/Proceedings/nesug10/cc/cc25.pdf  and  http://www.devenezia.com/downloads/sas/sascbtbl/

	*/
	Filename SASCBTBL catalog 'WORK.UBER_FUNCTIONS.ATTRIBUTE_TABLE.SOURCE';

	Data _NULL_;
		File SASCBTBL;
		Put "********** SASCBTBL FILE ***********;";
		Put;
		Put "ROUTINE SaveQueryResultsToCsvFileWithAuth";
		Put "minarg=9 maxarg=9";
		Put "callseq=byaddr stackorder=R2L";
		Put "returns=char128;";
		Put ;
		Put "ARG 1 CHAR INPUT;";
		Put "ARG 2 CHAR INPUT;";
		Put "ARG 3 CHAR INPUT;";
		Put "ARG 4 CHAR INPUT;";
		Put "ARG 5 CHAR INPUT;";
		Put "ARG 6 CHAR INPUT;";
		Put "ARG 7 CHAR INPUT;";
		Put "ARG 8 CHAR INPUT;";
		Put "ARG 9 NUM INPUT BYVALUE Format=IB5.;";
	Run;
	
	/* Find where the UBER DLL is located on the system. Do this by looking for the environment variable %Uber_JMP_Dir% that
	   gets created when Uber is installed. SAS function sysget() looks for environment variables */
	Data _NULL_;
		call symput('Uber_DLL',sysget('Uber_JMP_Dir')||"\UberWinLib.dll");
	Run;

	/* Call the Uber function with the supplied arguments */
	Data _NULL_;
		Length DataPath $128.; /* for the output file the Uber function creates */
		DataPath = " ";
		SQL = &SQLCode;
		CSVFile = " ";
		DataSource = "&DataSource";
		DateFmt = "yyyy/MM/dd HH:mm:ss";
		Site = " ";
		AuthMode = "IWA";
		UID = " ";
		PWD = " ";
		DataPath = modulec("*i","&Uber_DLL,SaveQueryResultsToCsvFileWithAuth",DataSource,SQL,CSVFile,DateFmt,Site,AuthMode,UID,PWD,&Timeout);
		call symput('DataPath',DataPath);
	Run;

	/* Check for UberException */
	%global UBEREXCEPTION; /* will be > 0 if there was an exception */
	Data _NULL_;
		Call symput('UBEREXCEPTION',find("&DataPath","UberException",'i'));
	Run;
	%if &UBEREXCEPTION > 0 %then %do;
		%put ERROR: &DataPath; /* Echo the exception to the SAS log */
		%goto MacroEnd;
	%end;
	
	/* otherwise import the resulting CSV file */
	Proc Import 
		DataFile="&DataPath" 
		DBMS=CSV 
		Out=&WorkLib..&OutData
		Replace;
		Getnames=YES;
		DataRow=2; 
	Run;

	/* first row = headers, second row = dummy row to define data types, data starts 3rd row. If no data found, will still be a dummy row present */
	/* so this works to ensure we get an empty SAS dataset with correct columns in that case */
	Data &WorkLib..&OutData;
		Set &WorkLib..&OutData(Firstobs=2); 
	Run;
	
	/* Delete the temporary Uber CSV file */
	Filename TempCSV "&DataPath";
	Data _NULL_;
		fname = "TmpFile";
		rc = fdelete('TempCSV');
	Run;

	%MacroEnd:;
%Mend;
