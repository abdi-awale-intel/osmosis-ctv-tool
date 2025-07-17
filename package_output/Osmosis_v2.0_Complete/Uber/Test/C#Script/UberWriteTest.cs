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

namespace TestWrite
{
    public class Program
    {
        static public void Main(string[] args)
        {
            Stopwatch sw = Stopwatch.StartNew();

            try
            {
                UniqeClientHelper helper = new UniqeClientHelper();
                {
                    helper.DataSource = "D1D_STAG_MARS";
                    helper.Authentication = AuthMode.UPWD;
                    helper.UserId = "HR";
                    helper.Password = "xxx";
                    helper.Site = "RF3STG";
                    helper.EnableWrites = true;
                    helper.EnableTransactionModeForWrites = true;
                };

                string sql = "Insert INTO F_TWDE_DISPATCH_PRIORITY (LOT) Values (:1)";

                Query query = new Query(sql);

                List<string> lot = new List<string>();

                for (int i = 0; i < 10; i++)
                {
                    lot.Add("TWD" + i);
                }

                // Set query parameters for bulk insert
                query.AddParameter("Lot", lot.ToArray());

                DataTable table = helper.GetDataTable(query);
                string csv = UniqeClientHelper.ConvertToCSV(table);

                MessageBox.Show("Num Rows Returned = " + table.Rows.Count
                    + Environment.NewLine + Environment.NewLine
                    + csv.Substring(0, Math.Min(1000, csv.Length)),
                    "Insert successful [Took " + sw.ElapsedMilliseconds + " ms]");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString(),
                    "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
            }
        }
    }
}