% Get the Uber install location and add path for required methods.
installpath = getenv('UBER_INSTALL_DIR');
methodspath = strcat(installpath ,'Test\MATLAB');
addpath(methodspath) ;

% Call GetDataFromUber to get the data in output (cellarray) 
% output variable can be manipulated in any desired way.
datasource = 'D1D_STAG_ARIES';

% To put multiline sql use the format shown below
% sql may also contain quote '' within it 
% sql statement should not be on same line as %{ or %}
sql = verbatim;
%{
    select * 
    from a_lot_at_operation 
    where rownum <=10 
%}

output = GetDataFromUber(datasource , sql);

% For sample , just displaying the output in a uitable
table = uitable;
colnames = output(1,:);
data = output(2:end,:);
set(table,'ColumnName',colnames)
set(table,'Data',data)