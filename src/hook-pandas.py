# Custom PyInstaller hook for pandas
# This ensures pandas and its dependencies are properly included

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all pandas submodules
hiddenimports = collect_submodules('pandas')

# Collect pandas data files
datas = collect_data_files('pandas')

# Add specific pandas modules that might be missed
hiddenimports += [
    'pandas._libs.tslib',
    'pandas._libs.tslibs.base',
    'pandas._libs.tslibs.timestamps',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.parsing',
    'pandas._libs.tslibs.strptime',
    'pandas.io.formats.format',
    'pandas.core.dtypes.common',
    'pandas.core.dtypes.generic',
    'pandas.core.dtypes.inference',
]
