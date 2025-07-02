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

## Enhanced ID Management for Shared IDs

### 🚀 NEW: Enhanced Structure (Recommended)

**Problem Solved**: Multiple people sharing the same ID values (e.g., two different patients with mobi_id = 2)

**Solution**: Person-centric mapping with intelligent conflict resolution

#### Enhanced Mapping Table Structure (e.g., `id-map-new-format.csv`):
```csv
person_id,id_value,id_type,source_context,priority,consent_status,effective_date,notes
PERSON_001,2,mobi_id,study_main,1,granted,2024-01-01,Primary mobi_id for person 1
PERSON_001,DD-0100-6247,mrn,study_main,1,granted,2024-01-01,Primary MRN for person 1
PERSON_002,2,mobi_id,study_secondary,1,revoked,2024-01-15,Different person with same mobi_id
PERSON_001,100,mobi_id,study_followup,2,granted,2024-06-01,Secondary ID for same person
```

#### Enhanced Configuration File (e.g., `mapping-new-format.csv`):
```csv
mapping_file,mapping_id,source_file,source_id,id_type,source_context,processed
id-map-new-format.csv,,data_table1.csv,mobi_id,mobi_id,study_main,False
id-map-new-format.csv,,data_table2.csv,mrn,mrn,study_main,False
id-map-new-format.csv,,data_table3.csv,patient_id,mobi_id,study_secondary,False
```

### ✨ Benefits of Enhanced Structure:
- **🔧 Resolves ID Conflicts**: Same ID can belong to different people in different contexts
- **⚡ Priority-Based Resolution**: Automatic conflict resolution using priority levels
- **🎯 Context Awareness**: IDs resolved within specific study/system contexts  
- **👤 Person-Centric Consent**: Consent tracked per individual, not per ID
- **📅 Temporal Validity**: Track when ID relationships became effective
- **🔗 Relationship Tracking**: One person can have multiple IDs across studies
- **⚖️ Conflict Resolution**: Intelligent handling of duplicate IDs

### 🎯 Real-World Example:
```
Scenario: Patient John has mobi_id=2 in main study, but mobi_id=2 also assigned to Patient Jane in secondary study

Enhanced Solution:
- PERSON_001 (John): mobi_id=2, context=study_main, priority=1, consent=granted
- PERSON_002 (Jane): mobi_id=2, context=study_secondary, priority=1, consent=revoked

Result: System correctly identifies John's data for hashing, keeps Jane's unhashed
```

### Legacy Structure (Still Supported)

The original structure continues to work for backward compatibility:

**Consent Status Types**:
- `granted`: IDs will be hashed in training tables
- `revoked`: IDs will not be hashed, original values preserved
- `none`: IDs will not be hashed, original values preserved
- `ID not found`: Automatically assigned to IDs not in the mapping table

**How It Works**:
- Add a `consent_status` column to your mapping table (the file specified in `mapping_file` column, e.g., table4.csv)
- Only IDs with 'granted' status will be hashed in training tables
- Original tables keep original IDs with added consent status column
- Training tables (`<filename>_training.<extension>`) are created with only 'granted' consent records and hashed IDs

## Usage

### 🖥️ Graphical Interface (Recommended)

1. **Run the GUI application:**
   ```bash
   python gui.py
   ```

2. **Create your configuration file** (choose format based on your needs):

   #### For Enhanced Structure (Recommended for shared IDs):
   Create `mapping-new-format.csv` with **absolute paths**:
   ```csv
   mapping_file,mapping_id,source_file,source_id,id_type,source_context,processed
   D:\Code\hash_tableid\id-map-new-format.csv,,D:\Code\hash_tableid\data_table1.csv,mobi_id,mobi_id,study_main,False
   ```
   
   > ⚠️ **Important**: All file paths must be absolute paths, not relative paths!
   
   And your mapping table `id-map-new-format.csv`:
   ```csv
   person_id,id_value,id_type,source_context,priority,consent_status,effective_date,notes
   PERSON_001,2,mobi_id,study_main,1,granted,2024-01-01,Primary ID
   ```

   #### For Legacy Structure:
   Create `mapping.csv` with **absolute paths**:
   ```csv
   mapping_file,mapping_id,source_file,source_id,processed
   D:\Code\hash_tableid\table4.csv,id_b,D:\Code\hash_tableid\table1.csv,id_a,False
   ```

3. **Configure consent status** in your mapping table:
   - `granted`: IDs will be hashed in training tables
   - `revoked`: IDs will not be hashed, original values preserved  
   - `none`: IDs will not be hashed, original values preserved

4. **Use the GUI interface:**
   - 📁 Click 'Browse' to select your configuration file
   - ▶️ Click 'Start Processing' to begin anonymization
   - ⏹️ Click 'Stop Processing' to pause at any time
   - 📊 Monitor real-time progress and status messages

### Command Line Interface (Advanced)

If you prefer using the command line:
```
python id_processor.py mapping.csv
```

## 📋 Output

The tool generates several output files depending on the structure used:

### Standard Outputs (Both Structures):
1. **Backup files** with `.backup` extension (safety first!)
2. **Updated original files** with added `consent_status` column (original IDs preserved)
3. **Training tables** (`<filename>_training.<extension>`) with only 'granted' consent records and hashed IDs
4. **Updated configuration file** with processing status tracking

### Enhanced Structure Additional Outputs:
5. **Enhanced lookup table** (`id_lookup_table.csv`) with additional metadata:
   ```csv
   person_id,original_id,hashed_id,id_type,source_context,consent_status,from_mapping
   PERSON_001,2,abc123def456...,mobi_id,study_main,granted,True
   PERSON_001,DD-0100-6247,abc123def456...,mrn,study_main,granted,True
   ```

### Output Structure Example:
```
📂 Your Project Folder
├── 📄 data_table1.csv (updated with consent_status column)
├── 📄 data_table1.csv.backup (original file backup)
├── 📄 data_table1_training.csv (hashed IDs, granted consent only)
├── 📄 id-map-new-format.csv (your mapping table)
├── 📄 mapping-new-format.csv (updated with processing status)
└── 📄 id_lookup_table.csv (comprehensive ID mappings)
```

## Safety Features

- Original files are automatically backed up
- Consistent hashing ensures related IDs get the same hash
- Clear error messages if something goes wrong
- Lookup table for tracking ID relationships
- Process tracking to avoid reprocessing files
- Safe handling of already hashed IDs (preserves existing hashes)
- Consent status tracking for compliance with data usage requirements


