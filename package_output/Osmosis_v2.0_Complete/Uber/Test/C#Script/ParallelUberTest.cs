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

public class ParallelUberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        List<string> queries = new List<string> { 
            "select * from A_LOT where ROWNUM <= 100",
            "select * from A_LOT_AT_OPERATION where ROWNUM <= 100"
        };

        try
        {
            List<DataTable> tables = RunQueries(queries, "D1D_PROD_ARIES");

            string csv = string.Empty;
            int totalRows = 0;
            for (int i = 0; i < tables.Count; i++)
            {
                totalRows += tables[i].Rows.Count;
                csv = UniqeClientHelper.ConvertToCSV(tables[i]);
                File.WriteAllText(@"output" + (i + 1) + ".csv", csv);
            }

            MessageBox.Show("Num Rows Returned = " + totalRows
                + Environment.NewLine + Environment.NewLine
                + csv.Substring(0, Math.Min(1000, csv.Length)),
                "Output data [Took " + sw.ElapsedMilliseconds + " ms]");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    public static List<DataTable> RunQueries(List<string> queries, string dataSource)
    {
        return new UniqeClientHelper
        {
            DataSource = dataSource,
            Authentication = AuthMode.IWA,
            UserId = null,
            Password = null,
            Site = null
        }.GetDataTables(queries);
    }

}
