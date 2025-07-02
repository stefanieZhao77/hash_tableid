# Template Files Overview

This directory contains template files to help you set up the ID Anonymization Tool quickly and correctly.

## 📁 Template Files

### **Enhanced Structure Templates (Recommended for Complex Scenarios)**

#### 1. `template_enhanced_mapping.csv`
**Purpose**: Configuration file for enhanced ID mapping  
**Use**: Copy this file and update the paths to match your project  
**Features**: Handles shared IDs, context-aware processing, priority-based conflict resolution

#### 2. `template_id_mapping_table.csv`  
**Purpose**: ID mapping table with person-centric structure  
**Use**: Copy this file and add your actual person/ID relationships  
**Features**: Resolves ID conflicts, tracks consent per person, supports multiple contexts

### **Legacy Structure Templates (Simple Scenarios)**

#### 3. `template_legacy_mapping.csv`
**Purpose**: Configuration file for traditional ID mapping  
**Use**: Copy this file for simple scenarios without shared IDs  
**Features**: Backward compatible, straightforward setup

#### 4. `template_legacy_id_table.csv`
**Purpose**: Traditional ID relationship table  
**Use**: Copy this file for simple ID-to-ID mappings  
**Features**: Simple structure, easy to understand

## 🚀 Quick Start

### **For Enhanced Structure:**
1. Copy `template_enhanced_mapping.csv` → rename to `your_mapping.csv`
2. Copy `template_id_mapping_table.csv` → rename to `your_id_table.csv`
3. Update all file paths to absolute paths (C:\Full\Path\To\File.csv)
4. Add your actual person IDs and data mappings
5. Run the tool!

### **For Legacy Structure:**
1. Copy `template_legacy_mapping.csv` → rename to `your_mapping.csv`
2. Copy `template_legacy_id_table.csv` → rename to `your_id_table.csv`
3. Update all file paths to absolute paths
4. Add your actual ID relationships
5. Run the tool!

## ⚠️ Important Notes

- **Always use absolute file paths** (full paths from C:\ on Windows)
- **Close Excel files** before processing
- **Use FALSE** for the processed column (not False or false)
- **Test with small datasets** first to verify your setup

## 📧 Need Help?

See the complete `user_instruction_email.md` for detailed setup instructions, troubleshooting, and best practices.

---

*These templates are designed to get you started quickly while avoiding common setup mistakes.* 