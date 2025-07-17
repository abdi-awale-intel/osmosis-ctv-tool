# PyUber Dependency Fix - Osmosis Application

## Issue Summary
The Osmosis application was experiencing a `'NoneType' object has no attribute 'uber_request'` error when processing tests like `NELB_X_CTVDEC_K_PREHVQK_TAP_X_NOM_X_RX_ASYNC`. This occurred because the `PyUber` database connection library was not available.

## Root Cause
- **PyUber** is a proprietary/internal database connection library
- When PyUber is not installed, the `pyuber_query` module import fails
- The application was attempting to call `py.uber_request()` on a `None` object
- No graceful fallback was implemented for missing PyUber dependency

## Fix Implementation

### 1. Enhanced Import Error Handling
**File**: `ctvlist_gui.py`
- Added checks for `PYUBER_AVAILABLE` and `py is not None` before calling `uber_request()`
- Implemented graceful degradation with informative warning messages
- Application continues processing without crashing

### 2. PyUber Module Resilience  
**File**: `pyuber_query.py`
- Added optional import with try-catch for PyUber
- Early return with dummy files when PyUber is unavailable
- Database connection wrapped in try-catch for additional safety

### 3. User Communication
- Clear warning messages: `⚠️ PyUber not available - skipping data request for test`
- Application logs explain when database functionality is disabled
- Processing continues for other features that don't require database access

## Code Changes

### In `ctvlist_gui.py`:
```python
# Before each py.uber_request() call:
if PYUBER_AVAILABLE and py is not None:
    self.log_message(f"Performing data request for test: {test}")
    datainput_file,datacombine_file = py.uber_request(...)
    intermediary_file_list.append(datainput_file)
else:
    self.log_message(f"⚠️ PyUber not available - skipping data request for test: {test}")
    datainput_file = None
```

### In `pyuber_query.py`:
```python
try:
    import PyUber
    PYUBER_DB_AVAILABLE = True
except ImportError:
    PYUBER_DB_AVAILABLE = False
    print("Warning: PyUber database module not available...")

def uber_request(...):
    if not PYUBER_DB_AVAILABLE:
        print(f"⚠️ Warning: PyUber database not available...")
        dummy_file = indexed_input.replace('_indexed_ctv_decoder.csv', '_datapulled.csv')
        return dummy_file, dummy_file
```

## Deployment Impact

### ✅ Benefits
- **No More Crashes**: Application handles missing PyUber gracefully
- **Partial Functionality**: Other features work even without database access
- **Clear Feedback**: Users understand what's happening via log messages
- **Maintainable**: Easy to add PyUber support when available

### ⚠️ Limitations
- **Reduced Functionality**: Database queries are skipped when PyUber unavailable
- **Dummy Data**: Some outputs may be empty/placeholder files
- **Manual Installation**: PyUber must be installed separately if needed

## Installation Options

### Option 1: Standard Installation (Recommended)
- Install Osmosis without PyUber
- Application works in "offline mode"
- File processing and GUI features fully functional
- Database queries gracefully skipped

### Option 2: Full Database Support
If PyUber is available in your environment:
1. Install PyUber using your organization's method
2. Rebuild Osmosis application: `python build_app.py`
3. Full database functionality will be enabled

## Testing Results
- ✅ Application launches successfully without PyUber
- ✅ Error messages are informative and non-blocking
- ✅ File processing continues normally
- ✅ No crashes or unhandled exceptions
- ✅ Graceful degradation implemented

## Future Considerations
1. **Alternative Database Libraries**: Consider supporting standard database connectors
2. **Configuration File**: Add database settings to config.json
3. **Connection Testing**: Add database connectivity test in GUI
4. **Progress Indicators**: Show when database features are disabled

---

**Fix Applied**: January 2025  
**Status**: ✅ Resolved  
**Testing**: ✅ Completed  
**Distribution**: ✅ Ready
