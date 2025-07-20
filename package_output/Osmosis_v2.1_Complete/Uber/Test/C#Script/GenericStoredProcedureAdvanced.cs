//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using Intel.FabAuto.ESFW.DS.UBER;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core;
using System;
using System.Collections;
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

public static class UberTest
{
    static public void Main(string[] args)
    {
        try
        {
            decimal[] rowId = new decimal[] { 5408, 5415 };
            string[] PMName = new string[2] { "name1", "name2" };
            int[] schInt = new int[] { 1, 0 };

            var parameters = new QueryParam[]
            {
                new QueryParam
                {
                    CollectionType = UniqeParamCollectionType.AssociativeArray,
                    Value = rowId,
                    Size = rowId.Length
                },
                new QueryParam
                {
                    CollectionType = UniqeParamCollectionType.AssociativeArray,
                    Value = PMName,
                    Size = PMName.Length
                },
                new QueryParam
                {
                    CollectionType = UniqeParamCollectionType.AssociativeArray,
                    Value = schInt,
                    Size = schInt.Length
                },
                new QueryParam
                {
                    Direction = ParameterDirection.Output,
                    Type = UniqeParamType.Oracle_Clob
                },
                new QueryParam
                {
                    Direction = ParameterDirection.Output,
                    Type = UniqeParamType.Int32
                },
                new QueryParam
                {
                    Direction = ParameterDirection.Output,
                    Type = UniqeParamType.String
                }
            };

            new UniqeClientHelper
            {
                Site = "DEV2",
                DataSource = "D1D_DEV_FAB300"
            }.ExecuteStoredProcedure("INTC_PKG_T3S_UI.Test_Array", parameters);

            // Display the parameters
            parameters.ToDataTable().DisplayTable();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.ToString(), "Exception");
        }
    }

}
