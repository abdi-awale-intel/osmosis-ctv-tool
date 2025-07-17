//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Linq;
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
        try
        {
            int N = 25;

            var inputArray = Enumerable.Range(1, N).ToArray();

            var param1 = new QueryParam
            {
                Name = "Number",
                CollectionType = UniqeParamCollectionType.AssociativeArray,
                Value = inputArray
            };
            var param2 = new QueryParam
            {
                Name = "IsPrime",
                Direction = ParameterDirection.Output,
                Type = UniqeParamType.Int32,
                CollectionType = UniqeParamCollectionType.AssociativeArray
            };

            new UniqeClientHelper
            {
                Site = "DEV2",
                DataSource = "D1D_STAG_MARS",
                Authentication = AuthMode.UPWD,
                UserId = "hr",
                Password = "xxx",
                DataAccessor = ""
            }.ExecuteStoredProcedure("UBER.RUN_SP_N", param1, param2);

            var outputArray = (int[])param2.Value;

            DataTable table = new DataTable("Output");
            table.Columns.Add(param1.Name, typeof(int));
            table.Columns.Add(param2.Name, typeof(int));
            for (int i = 0; i < outputArray.Length; i++)
            {
                table.Rows.Add(inputArray[i], outputArray[i]);
            }
            table.DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Exception");
        }
    }

}
