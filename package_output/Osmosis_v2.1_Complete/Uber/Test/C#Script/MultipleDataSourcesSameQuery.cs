//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;
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

        string query = @"select * from A_LOT where ROWNUM <= 10";
        List<string> dataSources = new List<string> { "D1D_PROD_ARIES", "F24_PROD_ARIES", "F28_PROD_ARIES", "F32_PROD_ARIES" };

        try
        {
            const int NUM_THREADS = 5;
            var outputTables = new ConcurrentBag<DataTable>();

            Parallel.ForEach(dataSources, new ParallelOptions { MaxDegreeOfParallelism = NUM_THREADS }, (dataSource) =>
            {
                IUberTable table = new UniqeClientHelper
                {
                    DataSource = dataSource,
                    Authentication = AuthMode.IWA,
                    UserId = null,
                    Password = null
                }.GetUberTable(query);
                outputTables.Add(table.ConvertToDataTable());
            });

            List<DataTable> tables = new List<DataTable>(outputTables);
            DataTable masterTable = new DataTable();
            foreach (var table in tables)
            {
                Append(masterTable, table);
            }

            masterTable.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    public static void Append(DataTable table, DataTable childTable)
    {
        if (childTable == null) return;

        if (table.Columns.Count == 0 && childTable.Columns.Count > 0)
        {
            foreach (DataColumn col in childTable.Columns)
            {
                table.Columns.Add(col.ColumnName, col.DataType);
            }
        }

        foreach (DataRow row in childTable.Rows)
        {
            table.ImportRow(row);
        }
    }

}
