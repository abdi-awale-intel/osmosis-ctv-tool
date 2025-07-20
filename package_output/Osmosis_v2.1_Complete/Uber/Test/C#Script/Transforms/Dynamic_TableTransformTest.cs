//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient.dll;
using System;
using System.Collections.Generic;
using System.Data;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using Intel.FabAuto.ESFW.DS.UBER;

public class DynamicTableTransformTest : BaseTableTransform
{
    /// <summary>
    /// Test harness
    /// </summary>
    [STAThread]
    public static void Main()
    {
        DataTable table = new DynamicTableTransformTest().Test(null, "D1D_PROD_MARS", "SELECT * from A_LOT WHERE ROWNUM <= 30000");
        table.DisplayTable();
    }

    private Dictionary<string, Type> _cols = null;
    private List<List<object>> _rows = new List<List<object>>();

    public override Dictionary<string, Type> Initialize(Dictionary<string, Type> columns)
    {
        Dictionary<string, Type> cols = new Dictionary<string, Type>();
        int index = 0;
        foreach (var item in columns)
        {
            cols.Add(item.Key, item.Value);
            if (index++ == 0)
            {
                cols.Add(item.Key + "_2", item.Value); // duplicate first column
            }
        }
        _cols = cols;
        return null;
    }

    public override List<List<object>> GetRow(List<object> rowData)
    {
        List<List<object>> rows = new List<List<object>>();
        List<object> row = new List<object>();
        int index = 0;
        foreach (var item in rowData)
        {
            row.Add(item);
            if (index++ == 0)
            {
                row.Add(item.ToString() + "_2");  // duplicate first column
            }
        }
        if (row.Count > 0)
        {
            _rows.Add(row);
        }
        return null;
    }

    public override Dictionary<string, Type> PreFinalize()
    {
        return _cols;
    }

    public override List<List<object>> Finalize()
    {
        return _rows;
    }
}
