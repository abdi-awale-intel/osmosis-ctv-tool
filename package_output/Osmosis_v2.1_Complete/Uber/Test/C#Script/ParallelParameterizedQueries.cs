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

        string sql = "select LOT, FACILITY, OPERATION, PROCESS, LAO_START_WW from A_LOT_AT_OPERATION where OPERATION = :Oper AND ROWNUM <= 100";
        List<string> dataSources = new List<string> { "D1D_PROD_ARIES", "F32_PROD_ARIES", "F28_PROD_ARIES", "D1C_PROD_ARIES" };

        try
        {
            UniqeJob job = new UniqeJob();

            foreach (var dataSource in dataSources)
            {
                Query query = new Query(sql, dataSource);
                query.AddParameter("Oper", "TEST");
                job.AddOperation(new Operation(query, null));
            }
            
            // do this instead if you want the output combined into 1 DataTable as the schema is the same for all queries
            //Operation oper = new Operation();
            //foreach (var dataSource in dataSources)
            //{
            //    Query query = new Query(sql, dataSource);
            //    query.AddParameter("Oper", "TEST");
            //    oper.AddQuery(query);
            //}
            //job.AddOperation(oper);

            string site = "RF3STG";
            UniqeClient proxy = GetProxy(site);
            IUberTable[] uberTables = proxy.ExecuteJob(job);

            List<DataTable> tables = new List<IUberTable>(uberTables).ConvertAll(uberTable => uberTable.ConvertToDataTable());

            // Display each output DataTable
            tables.ForEach(table => table.DisplayTable());
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    private static UniqeClient GetProxy(string site)
    {
        UniqeClient proxy = new UniqeClientHelper
        {
            Site = site
        }.GetClient(true);
        return proxy;
    }

    private static void SetProperty(ApplicationInfo appInfo, string propertyName, object propertyValue)
    {
        foreach (ApplicationAttribute attr in appInfo.ApplicationAttributeArrayList)
        {
            if (attr.AttributeName.Equals(propertyName, StringComparison.CurrentCultureIgnoreCase))
            {
                attr.AttributeValue = propertyValue.ToString();
                return;
            }
        }
    }

}
