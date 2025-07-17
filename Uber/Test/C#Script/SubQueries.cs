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

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string subQuery = @"SELECT DISTINCT LOT, LAO_START_WW, OPERATION FROM A_LOT_AT_OPERATION WHERE ROWNUM <= 10";
        string mainQuery = @"SELECT * FROM A_LOT_AT_OPERATION WHERE ({SUBQUERY_TOKEN})";

        try
        {
            var helper = new UniqeClientHelper
            {
                DataSource = "D1D_PROD_MARS",
                Authentication = AuthMode.IWA,
                UserId = null,
                Password = null,
                DataAccessor = null,
                Site = "DEV2"
            };

            DataTable subQueryTable = helper.GetDataTable(subQuery);
            subQueryTable.DisplayTable();

            string sql = QueryHelper.CreateQuery(mainQuery, "{SUBQUERY_TOKEN}", subQueryTable, new List<SubQueryColumnInfo>
            {
                new SubQueryColumnInfo { SourceColumn = "LOT", TargetColumn = "LOT", AllowInList  = true },
                new SubQueryColumnInfo { SourceColumn = "LAO_START_WW", TargetColumn = "LAO_START_WW", AllowInList  = true },
                new SubQueryColumnInfo { SourceColumn = "OPERATION", TargetColumn = "OPERATION", AllowInList  = true }
            });

            MessageBox.Show(sql, "Modified SQL");

            DataTable table = helper.GetDataTable(sql);
            table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}