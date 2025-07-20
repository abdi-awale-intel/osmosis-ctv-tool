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

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string sql = "select * from A_LOT where ROWNUM <= 100";
        //string query = File.ReadAllText(@"TestQuery.sql");

        try
        {
            IUberTable uberTable = new UniqeClientHelper
            {
                DataSource = "D1D_STAG_ARIES",
                Authentication = AuthMode.IWA,
                UserId = null,
                Password = null,
                DataAccessor = null,
                Site = null
            }.GetUberTable(sql);

            //uberTable.GetPropertiesTable().DisplayTable();
            DataTable table = ConvertToDataTable(uberTable);
            table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    private static DataTable ConvertToDataTable(IUberTable uberTable)
    {
        DataTable dataTable = new DataTable(uberTable.Name);
        foreach (var column in uberTable.GetColumns())
        {
            dataTable.Columns.Add(column.Name, column.Type);
        }
        while (uberTable.NextRow())
        {
            object[] rowData = uberTable.GetCurRowData();
            dataTable.Rows.Add(rowData);
        }
        return dataTable;
    }
   
}
