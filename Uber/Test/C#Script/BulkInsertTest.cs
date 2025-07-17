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

public class UNIQEClientHelper
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        try
        {
            string sql = "Insert INTO TESTXTAB (CNT, TYP, APP) Values (:1, :2, :3)";
            Query query = new Query(sql);

            // Set query parameters for bulk insert
            query.AddParameter("CNT", new int[] { 203, 204, 205 });
            //query.AddParameter("CNT", new int[] { 203, 204, 205 }, UniqeParamType.Int32);
            query.AddParameter("TYP", new string[] { "Uber1", "Uber2", "Uber3" });
            query.AddParameter("APP", new string[] { "ABC1", "ABC2", "ABC3" });

            DataTable table = new UniqeClientHelper
            {
                DataSource = "D1D_DEV_PCSA",
                Authentication = AuthMode.IWA,
                Application = "PCSA5",
                UserId = "PCSA",
                Password = "xxxx",
                Site = "DEV",
                EnableWrites = true
            }.GetDataTable(query);

            string csv = UniqeClientHelper.ConvertToCSV(table);

            MessageBox.Show("Num Rows Returned = " + table.Rows.Count
                + Environment.NewLine + Environment.NewLine
                + csv.Substring(0, Math.Min(1000, csv.Length)),
                "Insert successful [Took " + sw.ElapsedMilliseconds + " ms]");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
