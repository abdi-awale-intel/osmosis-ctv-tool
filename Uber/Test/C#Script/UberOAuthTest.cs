//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using Intel.FabAuto.ESFW.DS.UBER;
using Intel.FabAuto.ESFW.DS.UBER.Interfaces;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient;

public class UberOAuthTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string sql = "select * from A_LOT where ROWNUM <= 1000";

        // You will generally be getting this token from the client browser using IAM-WS. 
        // curl --ntlm -u : https://iamws-i.intel.com/api/v1/Windows/Auth -k -i
        // This is just for testing and will only work on machines with Kerberos/NTLM setup
        var winAuthToken = UniqeClientHelper.GetWinAuthToken(); 

        try
        {
            var helper = new UniqeClientHelper
            {
                Site = "RF3STG",
                DataSource = "D1D_STAG_MARS",
                Authentication = AuthMode.OAuth,
                UserId = winAuthToken, // Reusing UserId property to pass either WinAuthToken or UberAuthToken
                // Parameters below are optional. Used if UberAuthToken token needs to be portlable across machines. 
                // If portability needed, then this user/pwd combo has to be passed in all subsequent calls along with the UberAuthToken 
                OAuthBearerUserId = "", 
                OAuthBearerPassword = ""
            };

            var uberAuthToken = helper.GetUberAuthToken(); // If valid OAuthBearer UserId/Password combo is specified, this token can be stored and is portable across machines
            Console.WriteLine("Got Uber Auth Token with TTL of " + uberAuthToken.TTLInSeconds + " seconds. Token = " + uberAuthToken.Token);

            var uberTable = helper.GetUberTable(sql);
            DataTable table = uberTable.ConvertToDataTable();
            uberTable.GetPropertiesTable().DisplayTable(); // Display IUberTable properties
            table.DisplayTable("Success [using OAuth user {" + uberTable.UserID + "}] - " + uberTable.ServerFriendlyName);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Got Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
