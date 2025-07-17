# 🚀[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/abdi-awale-intel/osmosis-ctv-tool/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)]()
[![Size](https://img.shields.io/badge/size-54MB-green.svg)]()
[![Database](https://img.shields.io/badge/database-Oracle%20PyUber-orange.svg)]()

## 📥 Quick Download

**[⬇️ Download Latest Release (v2.0)](https://github.com/abdi-awale-intel/osmosis-ctv-tool/releases/latest/download/Osmosis_v2.0_Complete.zip)** v2.0 - CTV Data Processing Tool

**Advanced CTV data processing and analysis tool with complete PyUber database integration**

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/[YOUR-USERNAME]/osmosis-ctv-tool/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)]()
[![Size](https://img.shields.io/badge/size-54MB-green.svg)]()
[![Database](https://img.shields.io/badge/database-Oracle%20PyUber-orange.svg)]()

## 📥 Quick Download

**[⬇️ Download Latest Release (v2.0)](https://github.com/[YOUR-USERNAME]/[REPOSITORY-NAME]/releases/latest/download/Osmosis_v2.0_Complete.zip)**

> 🔥 **New in v2.0:** Complete PyUber integration with Oracle database connectivity!

## 🎯 What's This Tool?

Osmosis is a professional CTV (Clock Tree Verification) data processing application that connects to Intel's production Oracle databases to retrieve, process, and analyze semiconductor test data. Perfect for test engineers, data analysts, and validation teams.

### ✨ Key Features

- 🗄️ **Database Integration** - Direct Oracle connectivity via PyUber library
- ⚡ **Smart Processing** - Automated CTV decoding and SmartCTV configuration
- 📊 **Data Export** - Professional CSV/Excel output with advanced formatting
- 🖥️ **User-Friendly GUI** - Modern interface for easy operation
- 🔧 **Enterprise Ready** - Built for Intel internal production use

## 🚀 Quick Start

1. **Download** the [latest release](https://github.com/abdi-awale-intel/osmosis-ctv-tool/releases/latest)
2. **Extract** `Osmosis_v2.0_Complete.zip` to any folder
3. **Install** by running `Install_Osmosis.bat` as Administrator
4. **Launch** using the desktop shortcut

## 💻 System Requirements

| Requirement | Specification |
|-------------|---------------|
| **OS** | Windows 10/11 (64-bit) |
| **RAM** | 4 GB minimum (8 GB recommended) |
| **Storage** | 1 GB free space |
| **Network** | Oracle database access required |
| **Permissions** | Administrator rights for installation |

## 🔧 What's Included

```
📦 Osmosis v2.0 Complete Package (54MB)
├── 🎯 Osmosis.exe                 # Main application with GUI
├── 🔧 Install_Osmosis.bat         # Automated installer
├── ⚡ Launch_Osmosis.bat          # Quick launch script
├── ⚙️ config.json                # Configuration file
├── 📚 README.md                  # Documentation
├── 🗄️ PyUber/                    # Database library
└── 🏗️ Uber/                      # Oracle configuration
```

## 🆕 What's New in v2.0

### ✅ Major Improvements
- **Complete PyUber Integration** - Full Oracle database connectivity restored
- **Error Resolution** - Fixed `'NoneType' object has no attribute 'uber_request'`
- **Enhanced Performance** - Optimized data processing with chunked queries
- **Better Reliability** - Robust error handling and recovery mechanisms

### 📈 Performance Metrics
- **Startup Time:** 5-10 seconds (with PyUber initialization)
- **Query Speed:** 2-60 seconds (depends on data volume)
- **Memory Usage:** 200-500MB during processing
- **Package Size:** ~54MB (includes all database libraries)

## 🛠️ Troubleshooting

<details>
<summary><strong>🔴 Installation Issues</strong></summary>

- **Permission denied:** Run installer as Administrator
- **Antivirus blocking:** Add Osmosis folder to AV exceptions  
- **Installation fails:** Verify Windows 10/11 64-bit system
</details>

<details>
<summary><strong>🔶 Database Connection</strong></summary>

- **Connection failed:** Verify network access to Oracle databases
- **Authentication error:** Check database credentials and permissions
- **Firewall blocking:** Allow Oracle client through firewall
</details>

<details>
<summary><strong>⚡ Performance Issues</strong></summary>

- **Slow queries:** Check network connectivity to database servers
- **High memory usage:** Normal for large datasets (200-500MB expected)
- **Startup delay:** PyUber initialization takes 5-10 seconds (normal)
</details>

## 📊 Database Support

Osmosis connects to Intel's production Oracle databases:
- **D1D_PROD_XEUS** - Primary production database
- **F24_PROD_XEUS** - Secondary production database

> ⚠️ **Note:** Requires Intel network access and proper database permissions

## 🏗️ For Developers

### Building from Source
```bash
# Clone repository
git clone https://github.com/abdi-awale-intel/osmosis-ctv-tool.git
cd osmosis-ctv-tool

# Install dependencies
pip install -r requirements.txt

# Build executable
python build_app.py
```

### Project Structure
```
📁 Project Root
├── 🐍 osmosis_main.py           # Main application entry
├── 🖥️ ctvlist_gui.py            # GUI interface
├── 🗄️ pyuber_query.py           # Database operations
├── 📊 smart_json_parser.py      # Configuration parser
├── 🔧 build_app.py              # Build system
└── 📦 deployment_package/       # Distribution files
```

## 📄 License

Internal Intel tool - for Intel employees and authorized contractors only.

## 🤝 Support

- 🐛 **Bug Reports:** [Create an issue](https://github.com/abdi-awale-intel/osmosis-ctv-tool/issues)
- 💡 **Feature Requests:** [Submit enhancement](https://github.com/abdi-awale-intel/osmosis-ctv-tool/issues)
- 📧 **Direct Support:** Contact development team

---

<div align="center">

**🏆 Osmosis v2.0** | Built with ❤️ for Intel | Last Updated: July 17, 2025

[📥 Download](https://github.com/abdi-awale-intel/osmosis-ctv-tool/releases/latest) | [📖 Documentation](https://github.com/abdi-awale-intel/osmosis-ctv-tool/wiki) | [🐛 Issues](https://github.com/abdi-awale-intel/osmosis-ctv-tool/issues)

</div>
