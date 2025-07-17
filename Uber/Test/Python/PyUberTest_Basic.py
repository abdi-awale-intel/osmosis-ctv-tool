########################################################################
#Please refer to the following website for PyUber Installation & Usage
#           https://github.intel.com/fabnet/PyUber
########################################################################
import PyUber

#Connect to MARS
print("Connecting to D1D_PROD_MARS")
conn = PyUber.connect(datasource="D1D_PROD_MARS")

cursor = conn.execute('select l.lot from MC_1_F_LOT l where rownum < 10')

for r in cursor:
    print(r)
    
#Connect to XEUS
print("Connecting to D1D_PROD_XEUS")
conn = PyUber.connect(datasource="D1D_PROD_XEUS")

cursor = conn.execute('select lot from F_LOT where rownum < 10')

for r in cursor:
    print(r)
