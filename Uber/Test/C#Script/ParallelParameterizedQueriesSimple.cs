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

        string sql = "select * from A_LOT_AT_OPERATION where OPERATION = :Oper AND ROWNUM <= 100";
        List<string> dataSources = new List<string> { "D1D_PROD_ARIES", "F32_PROD_ARIES", "F28_PROD_ARIES", "D1C_PROD_ARIES" };

        try
        {
            List<Query> queries = new List<Query>();
            foreach (var dataSource in dataSources)
            {
                Query query = new Query(sql, dataSource);
                query.AddParameter("Oper", "TEST");
                queries.Add(query);
            }

            List<DataTable> tables = new UniqeClientHelper
            {
                Authentication = AuthMode.IWA,
                UserId = null,
                Site = null
            }.GetDataTables(queries);

            // Display each output DataTable
            tables.ForEach(table => table.DisplayTable());
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
