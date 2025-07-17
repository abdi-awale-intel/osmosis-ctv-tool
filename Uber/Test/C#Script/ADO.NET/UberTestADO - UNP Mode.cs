//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.Common;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using ADO = Intel.FabAuto.ESFW.DS.UBER.ADO;
using Intel.FabAuto.ESFW.DS.UBER;
using Intel.FabAuto.ESFW.DS.UBER.Interfaces;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient;

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        try
        {
            string dataSource = "D1D_PROD_XEUS";
            string site = "BEST";
            string sql = "select * from A_LOT_AT_OPERATION where Operation = :OPER and ROWNUM <= 100";
            string user = @"AMR\amodi"; // User to run the query as

            string connectionString = "DataSource=" + dataSource + ";Site=" + site + ";Authentication=UNP" + ";UserID=" + user;
            using (var con = new ADO.UberConnection(connectionString))
            {
                using (var cmd = con.CreateCommand(sql))
                {
                    cmd.Parameters.Add(new ADO.UberDbParameter { ParameterName = "OPER", Value = "6031" });
                    using (var reader = cmd.ExecuteReader())
                    {
                        DataTable table = ConvertToDataTable(reader);
                        table.DisplayTable(dataSource + " [" + sw.ElapsedMilliseconds + " ms]");
                    }
                }
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    private static DataTable ConvertToDataTable(IDataReader reader)
    {
        DataTable table = new DataTable();
        using (DataReaderAdapter dar = new DataReaderAdapter())
        {
            dar.FillFromReader(table, reader);
        }
        return table;
    }

    private class DataReaderAdapter : DataAdapter
    {
        public int FillFromReader(DataTable dataTable, IDataReader dataReader)
        {
            return Fill(dataTable, dataReader);
        }
    }
}