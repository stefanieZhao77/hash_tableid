# ID Anonymization Tool

A simple tool to anonymize IDs across multiple files while maintaining relationships between different ID types.

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
┌─────────────────────────────────────────────┐
│              table4.csv                     │
├───────────┬──────────┬────────────────────┤
│   id_b    │   id_c   │                    │
├───────────┬──────────┬────────────────────┤
│   B123    │   C01    │  ← Same entity     │
└───────────┴──────────┴────────────────────┘

After processing, all IDs for the same entity will be replaced 
with the same hashed value across all files.
All unique IDs (not in the mapping file) will be replaced with a new set of unique IDs.
```

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

3. Use the GUI to:
   - Click 'Browse' to select your mapping.csv file
   - Click 'Start Processing' to begin anonymization
   - Check the success message for results

### Command Line Interface (Advanced)

If you prefer using the command line:
```
python id_processor.py mapping.csv
```

## Output

The tool will:
1. Create backup files with '.backup' extension
2. Update the original files with hashed IDs
3. Create 'id_lookup_table.csv' showing original and hashed IDs

## Safety Features

- Original files are automatically backed up
- Consistent hashing ensures related IDs get the same hash
- Clear error messages if something goes wrong
- Lookup table for tracking ID relationships

## Support

For assistance, please contact your IT support team.