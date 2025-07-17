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
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core;

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string sql = @"SELECT * FROM A_LOT WHERE LOT IN (SELECT
  Regexp_substr(:lots, '[^,]+', 1, LEVEL) LOT
FROM
  dual
CONNECT BY LEVEL <= Length(Regexp_replace(:lots, '[^,]*')) + 1)";

        try
        {
            var helper = new UniqeClientHelper
            {
                DataSource = "D1D_STAG_ARIES",
                Authentication = AuthMode.IWA,
                UserId = null,
                Password = null,
                DataAccessor = null,
                Site = null
            };

            var lots = new List<string> { "Z535E560", "D542860E", "D330E3FA" };
            var query = new Query(sql);
            query.AddParameter("lots", PrintList(lots, ","));
            var uberTable = helper.GetUberTable(query);
            DataTable table = uberTable.ConvertToDataTable();
            //uberTable.GetPropertiesTable().DisplayTable(); // Display IUberTable properties
            table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    public static string PrintList(List<string> list, string separator)
    {
        if (list == null)
        {
            return string.Empty;
        }
        string output = string.Empty;
        foreach (string item in list)
        {
            if (output.Length > 0)
            {
                output += separator + item;
            }
            else
            {
                output = item;
            }
        }
        return output;
    }

}
