# ID Anonymization Tool

A simple tool to anonymize IDs across multiple files while maintaining relationships between different ID types. Supports csv and xlsx files.

## Installation

1. Make sure you have Python 3.10 or later installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Understanding ID Relationships

### Example Scenario
```
Data Files:
┌─────────────────┐    ┌────────────────┐    ┌────────────────┐
│   table1.csv    │    │   table2.csv   │    │   table3.csv   │
├─────────────────┤    ├────────────────┤    ├────────────────┤
│ id_a: A001      │    │ id_b: B123     │    │ id_c: C01      │
│ data1: value1   │    │ data2: value2  │    │ data3: value3  │
└─────────────────┘    └────────────────┘    └────────────────┘
         │                     │                     │
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│                    mapping.csv                          │
├───────────┬──────────┬──────────────┬─────────────────┤
│mapping_file│mapping_id│ source_file  │   source_id     │
├───────────┬──────────┬──────────────┬─────────────────┤
│table4.csv │   id_b   │ table1.csv   │   id_a          │
│table4.csv │   id_b   │ table2.csv   │   id_b          │
│table4.csv │   id_c   │ table3.csv   │   id_c          │
└───────────┴──────────┴──────────────┴─────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────┐
│              table4.csv (Mapping Table)               │
├───────────┬──────────┬────────────────┬──────────────┤
│   id_b    │   id_c   │ consent_status │              │
├───────────┬──────────┬────────────────┬──────────────┤
│   B123    │   C01    │    granted     │ ← Same entity│
└───────────┴──────────┴────────────────┴──────────────┘

After processing:
1. Only IDs with 'granted' consent will be hashed in training tables
2. Original tables will keep original IDs with added consent status
3. All IDs for the same entity with 'granted' consent will have the same hash
4. IDs not in the mapping file will be marked as 'ID not found'
```

## Consent Status Feature

The tool now supports consent status management:

1. **Consent Status Types**:
   - `granted`: IDs will be hashed in training tables
   - `revoked`: IDs will not be hashed, original values preserved
   - `none`: IDs will not be hashed, original values preserved
   - `ID not found`: Automatically assigned to IDs not in the mapping table

2. **How It Works**:
   - Add a `consent_status` column to your mapping table (the file specified in `mapping_file` column, e.g., table4.csv)
   - Only IDs with 'granted' status will be hashed in training tables
   - Original tables keep original IDs with added consent status column
   - Training tables (`<filename>_training.<extension>`) are created with only 'granted' consent records and hashed IDs

## Usage

### Graphical Interface (Recommended)

1. Run the GUI application:
   ```
   python gui.py
   ```

2. Create a mapping.csv file with these columns:
   - `mapping_file`: The file containing ID relationships (e.g., table4.csv)
   - `mapping_id`: The ID column in the mapping file (e.g., id_b, id_c)
   - `source_file`: The file to be anonymized (e.g., table1.csv)
   - `source_id`: The ID column in the source file (e.g., id_a)
   - `processed`: (Optional) Boolean column to track processing status, don't recommend changing it manually unless you want to reprocess the file again

3. Ensure your mapping table (specified in `mapping_file` column) has a `consent_status` column with values:
   - `granted`: For IDs that should be hashed
   - `revoked`: For IDs that should not be hashed
   - `none`: For IDs with no specific consent status

4. Use the GUI to:
   - Click 'Browse' to select your mapping.csv file
   - Click 'Start Processing' to begin anonymization
   - Click 'Stop Processing' to pause at any time
   - Monitor progress in real-time through status messages

### Command Line Interface (Advanced)

If you prefer using the command line:
```
python id_processor.py mapping.csv
```

## Output

The tool will:
1. Create backup files with '.backup' extension
2. Update the original files with added consent status column (original IDs preserved)
3. Create training tables (`<filename>_training.<extension>`) with only 'granted' consent records and hashed IDs
4. Create and maintain 'id_lookup_table.csv' showing original and hashed IDs with consent status
5. Update the mapping file with processing status

## Safety Features

- Original files are automatically backed up
- Consistent hashing ensures related IDs get the same hash
- Clear error messages if something goes wrong
- Lookup table for tracking ID relationships
- Process tracking to avoid reprocessing files
- Safe handling of already hashed IDs (preserves existing hashes)
- Consent status tracking for compliance with data usage requirements


