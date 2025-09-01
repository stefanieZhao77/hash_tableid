# Template Files for ID Anonymization Tool

This directory contains template files to help you get started with the ID Anonymization Tool.

## 📁 Template Files Overview

### Enhanced Structure (Recommended)
- **`template_enhanced_mapping.csv`** - Configuration file for enhanced structure
- **`template_id_mapping_table.csv`** - Enhanced mapping table with person-centric approach
- **`template_output_example.md`** - Examples of expected output files

### Legacy Structure (Backward Compatible)
- **`template_legacy_mapping.csv`** - Configuration file for legacy structure
- **`template_legacy_id_table.csv`** - Legacy mapping table format

## 🚀 Getting Started

### Option 1: Enhanced Structure (Recommended)

1. **Copy and customize the enhanced mapping configuration:**
   ```bash
   cp template_enhanced_mapping.csv my_mapping.csv
   ```

2. **Copy and customize the enhanced mapping table:**
   ```bash
   cp template_id_mapping_table.csv my_id_mapping_table.csv
   ```

3. **Update the file paths** in `my_mapping.csv` to point to your actual files (use absolute paths)

4. **Configure your mapping table** in `my_id_mapping_table.csv` with your actual data

### Option 2: Legacy Structure

1. **Copy and customize the legacy mapping configuration:**
   ```bash
   cp template_legacy_mapping.csv my_mapping.csv
   ```

2. **Copy and customize the legacy mapping table:**
   ```bash
   cp template_legacy_id_table.csv my_legacy_mapping_table.csv
   ```

3. **Update the file paths** in `my_mapping.csv` to point to your actual files (use absolute paths)

## 🔧 Recent Improvements

The template files reflect the latest improvements to the ID processor:

### Enhanced Source Context Handling
- Each file now uses its individual source context for proper ID resolution
- Better handling of empty/NaN source context values
- Improved key format consistency for reliable lookups

### File-Specific ID Mapping
- Dynamic creation of ID mappings for different source contexts
- Enhanced lookup table generation with proper parsing
- Better conflict resolution for shared IDs

### Improved Error Handling
- Robust handling of empty source contexts
- Better validation of mapping table structures
- Enhanced error messages for troubleshooting

## 📋 Template File Descriptions

### Enhanced Structure Templates

#### `template_enhanced_mapping.csv`
Configuration file that defines:
- Which mapping table to use
- Which source files to process
- What ID columns to look for
- What source contexts to use
- Processing status tracking

#### `template_id_mapping_table.csv`
Enhanced mapping table with:
- Person-centric approach (`person_id` column)
- Multiple ID types per person
- Source context specification
- Priority-based conflict resolution
- Consent status tracking
- Temporal validity (effective dates)

#### `template_output_example.md`
Shows examples of:
- Expected input file formats
- Expected output file formats
- Hash consistency examples
- Key points about the processing

### Legacy Structure Templates

#### `template_legacy_mapping.csv`
Simple configuration file for legacy structure with:
- Basic file mapping
- ID column specification
- Processing status tracking

#### `template_legacy_id_table.csv`
Legacy mapping table with:
- Simple ID relationships
- Consent status column
- Basic conflict resolution

## ⚠️ Important Notes

1. **Absolute Paths Required**: All file paths in configuration files must be absolute paths
2. **Consent Status**: Use `granted`, `revoked`, `none`, or `ID not found` for consent status
3. **Source Context**: Leave empty if not needed, but be consistent across your mapping
4. **Priority**: Lower numbers = higher priority for conflict resolution
5. **Backup Safety**: Original files are automatically backed up before processing

## 🎯 Best Practices

1. **Use Enhanced Structure** for complex scenarios with shared IDs
2. **Use Legacy Structure** for simple scenarios with unique IDs
3. **Test with Small Files** before processing large datasets
4. **Check Backup Files** to ensure your original data is safe
5. **Review Training Files** to verify hashed IDs are correct
6. **Use Lookup Tables** to track ID relationships

## 🔍 Troubleshooting

If you encounter issues:

1. **Check file paths** - ensure all paths are absolute and files exist
2. **Verify consent status** - use valid values: `granted`, `revoked`, `none`
3. **Check source contexts** - ensure consistency or leave empty
4. **Review error messages** - they provide specific guidance
5. **Check backup files** - your original data is always preserved

## 📞 Support

For additional help:
1. Review the main README.md for detailed documentation
2. Check the troubleshooting section for common issues
3. Examine the template_output_example.md for expected results
4. Use the GUI interface for easier configuration and monitoring 