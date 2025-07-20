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

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string query = "select * from DataSources";
        //string query = File.ReadAllText(@"TestQuery.sql");

        try
        {
            var helper = new UniqeClientHelper
            {
                DataSource = "UNIQE_METADATA_GENERIC",
                Authentication = AuthMode.IWA,
                UserId = null,
                Password = null,
                DataAccessor = null,
                Site = null
            };

            var uberTable = helper.GetUberTable(query);
            DataTable table = uberTable.ConvertToDataTable();
            //uberTable.GetPropertiesTable().DisplayTable(); // Display IUberTable properties
            table.DisplayTable("Health Check Passed - " + uberTable.ServerFriendlyName);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Health Check Failed - Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
