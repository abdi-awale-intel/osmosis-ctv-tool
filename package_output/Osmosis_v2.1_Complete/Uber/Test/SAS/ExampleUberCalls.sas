Libname Test "C:\Temp";

%let MySQL = 
Select * from a_testing_session ts where ts.lot = 'D345832A' and ts.operation = '6051' ;


%let MyDataSource = D1D_PROD_ARIES;

%GenericUberQuery(
	WorkLib=Test,
	DataSource=&MyDataSource,
	SQLCode = "&MySQL",
	OutData=VIPRPull_1,
	Timeout = 600
);

