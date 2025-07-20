//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
//css_ref ICSharpCode.SharpZipLib.dll;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.Serialization.Formatters.Binary;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml;
using ICSharpCode.SharpZipLib.Core;
using ICSharpCode.SharpZipLib.Zip;
using Intel.FabAuto.ESFW.DS.UBER;
using Intel.FabAuto.ESFW.DS.UBER.Interfaces;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core;
using Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient;

public static class ZipTest
{
    static public void Main(string[] args)
    {
        Stopwatch sw = Stopwatch.StartNew();

        string query = @"select * from A_LOT where ROWNUM <= 10";
        List<string> dataSources = new List<string> { "D1D_PROD_ARIES", "D1C_PROD_ARIES", "F32_PROD_ARIES" };

        try
        {
            const int NUM_THREADS = 5;
            var outputTables = new ConcurrentBag<KeyValuePair<string, DataTable>>();
            Parallel.ForEach(dataSources, new ParallelOptions { MaxDegreeOfParallelism = NUM_THREADS }, (dataSource) =>
                {
                    IUberTable table = new UniqeClientHelper
                    {
                        DataSource = dataSource,
                        Authentication = AuthMode.IWA,
                        UserId = null,
                        Password = null
                    }.GetUberTable(query);
                    outputTables.Add(new KeyValuePair<string, DataTable>(dataSource, table.ConvertToDataTable()));
                });

            const string ZIPFILE = @"C:\Temp\test.zip";
            SerializeToZipFile(ZIPFILE, outputTables);

            // Extract specific item
            const string ITEM_TO_EXTRACT = "D1C_PROD_ARIES";
            var specificItem = DeserializeFromZipFile<DataTable>(ZIPFILE, ITEM_TO_EXTRACT);
            specificItem.DisplayTable(ITEM_TO_EXTRACT);

            // Extract all items
            var list = DeserializeFromZipFile<DataTable>(ZIPFILE);
            DataTable masterTable = new DataTable();
            list.ForEach(item => masterTable.Append(item.Value));
            masterTable.DisplayTable("All tables combined");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message,
                "Exception [Took " + sw.ElapsedMilliseconds + " ms]");
        }
    }

    /// <summary>
    /// Serialize a list to a ZIP file
    /// </summary>
    /// <typeparam name="T">object type</typeparam>
    /// <param name="fileName">Name of target zip file</param>
    /// <param name="list">List of name/value pair for the objects to be serialized</param>
    public static void SerializeToZipFile<T>(string fileName, IEnumerable<KeyValuePair<string, T>> list)
    {
        using (var outputStream = File.Create(fileName))
        {
            using (ZipOutputStream zipStream = new ZipOutputStream(outputStream))
            {
                zipStream.SetLevel(5); //0-9, 9 being the highest level of compression

                foreach (var item in list)
                {
                    ZipEntry newEntry = new ZipEntry(item.Key);
                    newEntry.DateTime = DateTime.Now;
                    zipStream.PutNextEntry(newEntry);
                    new BinaryFormatter().Serialize(zipStream, item.Value);
                    zipStream.CloseEntry();
                }
                zipStream.IsStreamOwner = false;
            }
        }
    }

    public static T DeserializeFromZipFile<T>(string fileName, string name)
    {
        var list = DeserializeFromZipFile<T>(fileName, new List<string> { name });
        if (list.Count > 0)
        {
            return list[0].Value;
        }
        else
        {
            return default(T);
        }
    }

    public static List<KeyValuePair<string, T>> DeserializeFromZipFile<T>(string fileName, List<string> names = null)
    {
        List<KeyValuePair<string, T>> list = new List<KeyValuePair<string, T>>();

        var inputStream = File.OpenRead(fileName);
        ZipInputStream zipStream = new ZipInputStream(inputStream);
        ZipEntry theEntry;
        while ((theEntry = zipStream.GetNextEntry()) != null)
        {
            if (names == null || names.FindIndex(item => item.Equals(theEntry.Name, StringComparison.CurrentCultureIgnoreCase)) >= 0)
            {
                var obj = (T) new BinaryFormatter().Deserialize(zipStream);
                list.Add(new KeyValuePair<string, T>(theEntry.Name, obj));
            }
        }

        return list;
    }

    public static void Append(this DataTable table, DataTable childTable)
    {
        if (childTable == null) return;

        if (table.Columns.Count == 0 && childTable.Columns.Count > 0)
        {
            foreach (DataColumn col in childTable.Columns)
            {
                table.Columns.Add(col.ColumnName, col.DataType);
            }
        }

        foreach (DataRow row in childTable.Rows)
        {
            table.ImportRow(row);
        }
    }

}
