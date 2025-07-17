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

public class UberTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string site = "DEV";
        string dataSource = "D1D_DEV_TEST_FTP";
        string fileList = "*.out";
        string outputDirectory = @"C:\Temp\TestFTP";

        try
        {
            var helper = new UniqeClientHelper { Site = site, DataSource = dataSource };
            var table = helper.DownloadFilesUsingFTP(fileList, outputDirectory);
            table.DisplayTable();
            //MessageBox.Show("Downloaded " + files.Count + " files using FTP:" + Environment.NewLine
            //    + Environment.NewLine + PrintList(files, Environment.NewLine), "FTP [Took " + sw.ElapsedMilliseconds + " ms]");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

}
