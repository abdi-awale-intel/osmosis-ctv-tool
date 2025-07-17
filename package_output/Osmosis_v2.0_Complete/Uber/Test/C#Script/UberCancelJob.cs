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

        string query = "select * from A_LOT where ROWNUM <= 100";
        //string query = File.ReadAllText(@"TestQuery.sql");

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

            // Submit long-running job
            var uberTable = helper.GetUberTable(query);

            // Do other processing

            // Cancel job if still running
            var status = uberTable.GetJobStatus();
            bool canceled = false;
            if (status.State == JobStatus.Status.Executing || status.State == JobStatus.Status.Pending)
            {
                canceled = uberTable.CancelJob();
            }
            MessageBox.Show("Status = " + status.State.ToString() + " from " + uberTable.Server + " [" + uberTable.ServerFriendlyName + "] [Canceled = " + canceled + "]", "Job Status");

            //var table = uberTable.ConvertToDataTable();
            //table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
