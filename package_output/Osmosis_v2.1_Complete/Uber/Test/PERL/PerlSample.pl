# Location for UberPerl Module

use lib $ENV{'UBER_INSTALL_DIR'} .'Test\PERL';

#Module containing GetDataFromUber subroutine
use UberPerlModule;

# Have to be references else Perl does not behave the expected way so make the function call same way as below
#Call to function to get column name and data from backend
($header,$data) = UberPerlModule::GetDataFromUber("select lot, lao_start_ww, lao_test_end_date_time from a_lot_at_operation where rownum <= 10","D1D_PROD_ARIES");

#Getting the column names to an array 
@header_row= @$header;

#Getting the actual data to an array reference
@result = @$data;


#just a check to see if expected data is obatined
print $header_row[0][1];
print $result[1][1];
