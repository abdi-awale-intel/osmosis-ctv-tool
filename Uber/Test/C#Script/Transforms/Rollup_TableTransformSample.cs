//css_ref Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.UberCommon.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.dll;
//css_ref Intel.FabAuto.ESFW.DS.UBER.Uniqe.QEClient.dll;
using System;
using System.Collections.Generic;
using System.Data;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using System.Xml;
using Intel.FabAuto.ESFW.DS.UBER;

namespace TestTransform
{
    public class RollupTransformTest : BaseTableTransform
    {
        /// <summary>
        /// Test harness
        /// </summary>
        [STAThread]
        public static void Main()
        {
            DataTable table = new RollupTransformTest().Test("RF3STG", "D1D_PROD_MARS", @"
SELECT /*+ ORDERED NO_EXPAND */
   s.LOT
  ,s.WAFER_ID            ""WAFER""
  ,s.PROGRAM_NAME        ""PROGRAM""
  ,s.DEVREVSTEP          ""PART""
  ,s.OPERATION
  ,s.TEST_END_DATE_TIME  ""TEST_END_DATE""
  ,s.FLOW_STEP           ""FLOW""
  ,s.PROCESS
  ,s.DEVICE_ITEMS_TESTED ""N_TESTED""
  ,s.FACILITY
  ,s.TESTER_ID           ""TESTER""
  ,s.PROBE_CARD_ID       ""PROBE_CARD""
  ,CASE WHEN r.BC_TYPE_OR_NAME IN ('IB','FB','DB') THEN r.BC_TYPE_OR_NAME || TO_CHAR(r.BIN_COUNTER_ID) ELSE r.BC_TYPE_OR_NAME END  ""ROLLUP_NAME""
  ,r.ROLLUP_VALUE ""ROLLUP_VALUE""
FROM ARIES.A_TESTING_SESSION             s
LEFT JOIN ARIES.A_TESTING_SESSION_ROLLUP r
  ON  r.LAO_START_WW=s.LAO_START_WW
  AND r.TS_ID=s.TS_ID
  AND r.BC_TYPE_OR_NAME IN ('#$%#','T_GOOD','BID_GOOD','NR_GOOD','NRF_GOOD','T_BAD','T_TOTAL','TF_GOOD','T_FUNC','IB'  )
  AND 1=1
WHERE s.LOT IN ('D2143630','D2153230','D2153240','D2153330','D2163460','D2163480','D2173380','D2173470','D2173490','D2173570','D2183440','D2183450','D2183470','D2183490'
)
  AND  (s.OPERATION='6051')
  AND 1=1
  AND s.DATA_DOMAIN='SORT'
  AND s.LATEST_FLAG='Y'
  AND s.VALID_FLAG='Y'
");
            table.DisplayTable();
        }

        private const string ROLLUP_NAME = "ROLLUP_NAME";
        private const string ROLLUP_VALUE = "ROLLUP_VALUE";
        //private const object DEFAULT_MISSING_VALUE = DBNull.Value;
        private readonly object DEFAULT_MISSING_VALUE = new Decimal(0.0);

        private Dictionary<string, Type> _cols = null;

        private int ROLLUP_NAME_INDEX = -1;
        private int ROLLUP_VALUE_INDEX = -1;
        private Type ROLLUP_VALUE_TYPE = null;

        private Dictionary<string, List<object>> _groupBys = new Dictionary<string, List<object>>();
        private Dictionary<string, List<KeyValuePair<string, object>>> _data = new Dictionary<string, List<KeyValuePair<string, object>>>();
        private Dictionary<string, int> _colIndex = new Dictionary<string, int>();

        public override Dictionary<string, Type> Initialize(Dictionary<string, Type> columns)
        {
            Dictionary<string, Type> cols = new Dictionary<string, Type>();
            List<string> keys = new List<string>(columns.Keys);

            for (int i = 0; i < keys.Count; i++)
            {
                string key = keys[i];
                Type val = columns[key];
                if (key.Equals(ROLLUP_NAME, StringComparison.CurrentCultureIgnoreCase))
                {
                    ROLLUP_NAME_INDEX = i;
                }
                else if (key.Equals(ROLLUP_VALUE, StringComparison.CurrentCultureIgnoreCase))
                {
                    ROLLUP_VALUE_INDEX = i;
                    ROLLUP_VALUE_TYPE = val;
                }
                else
                {
                    cols.Add(key, val);
                }
            }
            if (ROLLUP_NAME_INDEX < 0)
            {
                throw new Exception("Column [" + ROLLUP_NAME + "] not found in table.");
            }
            if (ROLLUP_VALUE_INDEX < 0)
            {
                throw new Exception("Column [" + ROLLUP_VALUE + "] not found in table.");
            }
            _cols = cols;
            return null;
        }

        public override List<List<object>> GetRow(List<object> rowData)
        {
            string key = ConvertToString(rowData[ROLLUP_NAME_INDEX]);
            object val = rowData[ROLLUP_VALUE_INDEX];
            if (ROLLUP_VALUE_INDEX > ROLLUP_NAME_INDEX)
            {
                rowData.RemoveAt(ROLLUP_VALUE_INDEX);
                rowData.RemoveAt(ROLLUP_NAME_INDEX);
            }
            else
            {
                rowData.RemoveAt(ROLLUP_NAME_INDEX);
                rowData.RemoveAt(ROLLUP_VALUE_INDEX);
            }
            string dictKey = GetKey(rowData);
            if (!_groupBys.ContainsKey(dictKey))
            {
                _groupBys.Add(dictKey, rowData);
            }
            List<KeyValuePair<string, object>> items;
            if (!_data.TryGetValue(dictKey, out items))
            {
                items = new List<KeyValuePair<string, object>>();
                _data.Add(dictKey, items);
            }
            items.Add(new KeyValuePair<string, object>(key, val));
            if (!_colIndex.ContainsKey(key))
            {
                _colIndex.Add(key, _cols.Count);
            }
            return null;
        }

        private static string GetKey(List<object> row)
        {
            const string SEPARATOR = "$*&3";
            string key = string.Empty;
            for (int i = 0; i < row.Count; i++)
            {
                key += ConvertToString(row[i]) + SEPARATOR;
            }
            return key;
        }

        private static string ConvertToString(object val)
        {
            return (val == null) ? string.Empty : val.ToString();
        }

        public override Dictionary<string, Type> PreFinalize()
        {
            List<string> newCols = new List<string>(_colIndex.Keys);
            newCols.Sort((x, y) =>
            {
                return ConvertColumnName(x).CompareTo(ConvertColumnName(y));
            });
            _colIndex.Clear();
            foreach (var col in newCols)
            {
                _colIndex.Add(col, _cols.Count);
                _cols.Add(col, ROLLUP_VALUE_TYPE);
            }
            return _cols;
        }

        private static string ConvertColumnName(string input)
        {
            Match match = Regex.Match(input, @"^(?<pre>[a-zA-Z_ ]+)(?<post>[0-9]+)$");
            if (match.Success) // e.g., to sort IB10 after IB9
            {
                string pre = match.Groups["pre"].Value;
                long post = Convert.ToInt64(match.Groups["post"].Value);
                input = pre + string.Format("{0:0000000}", post);
            }
            return input;
        }

        public override List<List<object>> Finalize()
        {
            List<List<object>> rows = new List<List<object>>();

            foreach (var item in _groupBys)
            {
                string dictKey = item.Key;
                List<object> row = item.Value;
                List<KeyValuePair<string, object>> data = _data[dictKey];
                int colsToAdd = _cols.Count - row.Count;
                for (int i = 0; i < colsToAdd; i++)
                {
                    row.Add(DEFAULT_MISSING_VALUE);
                }
                foreach (KeyValuePair<string, object> kvp in data)
                {
                    row[_colIndex[kvp.Key]] = kvp.Value;
                }
                rows.Add(row);
            }
            return rows;
        }
    }
}