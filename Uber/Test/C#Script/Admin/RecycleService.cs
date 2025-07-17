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

        try
        {
            string nodeToReboot = "xyz"; // e.g., DEV2, RF3STG1
            bool writeService = false;
            UniqeClientHelper.RecycleService(nodeToReboot, writeService);
            MessageBox.Show("Recycled UNIQE " + (writeService ? "WRITE" : "READ") + " Service successfully on " + nodeToReboot + ".", 
                "Done [took " + sw.ElapsedMilliseconds + " ms]");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
