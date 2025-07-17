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

        string query = @"select S.* from FDC.P_FDC_RUN_ENTITY E, FDC.P_FDC_summary_value S
                        where E.start_time between to_date('20130601 10:00:00', 'YYYYMMDD HH24:MI:SS') and to_date('20130601 10:15:00', 'YYYYMMDD HH24:MI:SS')
                        and E.tool_run_id = S.tool_run_id";
        try
        {
            var helper = new UniqeClientHelper
            {
                DataSource = "D1D_PROD_MARS",
                Authentication = AuthMode.IWA,
                UserId = null,
                Password = null,
                DataAccessor = null,
                MinThresholdPeriodInSecondsForQueryBreakUp = 120, // Break date-time range every 120 seconds
                MaxNumOfChildThreads = 5, // Maximum number of threads to be spawned on the server when doing SQL break-up
                IgnoreOrderBy = true, // Continue to split the query even if it uses ORDER BY, GROUP BY, DISTINCT or OR conditions
                Site = "DEV2"
            };

            IUberTable uberTable = helper.GetUberTable(query);
            DataTable table = uberTable.ConvertToDataTable();

            // Display output IUberTable properties (data received, bandwidth, compression ratio, etc.)
            uberTable.GetPropertiesTable().DisplayTable();
            table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
