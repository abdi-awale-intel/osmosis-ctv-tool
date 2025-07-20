//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
using System;
using System.Collections.Generic;
using System.Data;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using Intel.FabAuto.ESFW.DS.UBER;

public class RunScriptSample : IRunScript
{
    /// <summary>
    /// Test harness
    /// </summary>
    [STAThread]
    public static void Main()
    {
        MessageBox.Show(new RunScriptSample().Run("hello"), "Output");
    }

    public string Run(string argument)
    {
        return "Test " + (argument + string.Empty);
    }

}
