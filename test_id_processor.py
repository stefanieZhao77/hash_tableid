import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
from id_processor import IDProcessor


@pytest.fixture
def processor():
    return IDProcessor()


@pytest.fixture
def sample_data(tmp_path):
    # Create a nested directory structure
    (tmp_path / "subfolder").mkdir()
    (tmp_path / "subfolder/deeper").mkdir()
    
    # Create test files in different locations
    table1 = pd.DataFrame({
        'patientid': ['P001', 'P002', 'P003'],
        'data': ['a', 'b', 'c']
    })
    table1.to_csv(tmp_path / 'table1.csv', index=False)

    table2 = pd.DataFrame({
        'MRN': ['M001', 'M002', 'M003'],
        'data': ['x', 'y', 'z']
    })
    table2.to_csv(tmp_path / 'subfolder/table2.csv', index=False)

    table3 = pd.DataFrame({
        'mobi_id': ['MB001', 'MB002', 'MB003'],
        'data': ['1', '2', '3']
    })
    table3.to_csv(tmp_path / 'subfolder/deeper/table3.csv', index=False)

    # This is our mapping table that shows ID relationships
    table4 = pd.DataFrame({
        'mobi_id': ['MB001', 'MB002', 'MB003'],
        'MRN': ['M001', 'M002', 'M003']
    })
    table4.to_csv(tmp_path / 'table4.csv', index=False)

    # Mapping file that points to files in different directories
    mapping = pd.DataFrame([
        {
            'mapping_file': 'table4.csv',
            'mapping_id': 'MRN',
            'source_file': 'table1.csv',
            'source_id': 'patientid'
        },
        {
            'mapping_file': 'table4.csv',
            'mapping_id': 'MRN',
            'source_file': 'subfolder/table2.csv',
            'source_id': 'MRN'
        },
        {
            'mapping_file': 'table4.csv',
            'mapping_id': 'mobi_id',
            'source_file': 'subfolder/deeper/table3.csv',
            'source_id': 'mobi_id'
        }
    ])
    mapping.to_csv(tmp_path / 'mapping.csv', index=False)

    return tmp_path


def test_find_files(processor, sample_data):
    """Test finding files in nested directories."""
    mapping_df = pd.read_csv(sample_data / 'mapping.csv')
    files = processor.find_files(sample_data, mapping_df)
    
    assert len(files) == 4  # Should find all 4 CSV files
    assert any(f.name == 'table1.csv' for f in files)
    assert any(f.name == 'table2.csv' for f in files)
    assert any(f.name == 'table3.csv' for f in files)
    assert any(f.name == 'table4.csv' for f in files)


def test_id_mapping_creation(processor, sample_data):
    """Test creation of ID mapping from relationships."""
    mapping_df = pd.read_csv(sample_data / 'mapping.csv')
    mapping_file_path = sample_data / 'table4.csv'
    
    id_mapping = processor.create_id_mapping(mapping_file_path, mapping_df)
    
    # Check that related IDs get the same hash
    assert id_mapping['M001'] == id_mapping['MB001']
    assert id_mapping['M002'] == id_mapping['MB002']
    assert id_mapping['M003'] == id_mapping['MB003']


def test_mapping_file_update(processor, sample_data):
    """Test that mapping file gets hashed_id column without modifying original IDs."""
    mapping_df = pd.read_csv(sample_data / 'mapping.csv')
    mapping_file_path = sample_data / 'table4.csv'
    
    # Read original data
    original_df = pd.read_csv(mapping_file_path)
    original_mrn = original_df['MRN'].copy()
    original_mobi = original_df['mobi_id'].copy()
    
    # Update mapping file
    processor.update_mapping_file(mapping_file_path, mapping_df)
    
    # Read updated file
    updated_df = pd.read_csv(mapping_file_path)
    
    # Check original columns unchanged
    pd.testing.assert_series_equal(updated_df['MRN'], original_mrn)
    pd.testing.assert_series_equal(updated_df['mobi_id'], original_mobi)
    
    # Check new column added
    assert 'hashed_id' in updated_df.columns
    assert all(len(h) == 64 for h in updated_df['hashed_id'])  # SHA-256 length


def test_source_file_update(processor, sample_data):
    """Test that source files get new hashed columns."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Check each source file
    table1 = pd.read_csv(sample_data / 'table1.csv')
    table2 = pd.read_csv(sample_data / 'subfolder/table2.csv')
    table3 = pd.read_csv(sample_data / 'subfolder/deeper/table3.csv')
    
    # Check new columns exist
    assert 'patientid_hashed' in table1.columns
    assert 'MRN_hashed' in table2.columns
    assert 'mobi_id_hashed' in table3.columns
    
    # Check original columns still exist
    assert 'patientid' in table1.columns
    assert 'MRN' in table2.columns
    assert 'mobi_id' in table3.columns


def test_id_consistency(processor, sample_data):
    """Test that related IDs get the same hash value."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Read all files
    table2 = pd.read_csv(sample_data / 'subfolder/table2.csv')
    table3 = pd.read_csv(sample_data / 'subfolder/deeper/table3.csv')
    table4 = pd.read_csv(sample_data / 'table4.csv')
    
    # Get hashed values for IDs we know are related
    mrn_hash = table2.loc[0, 'MRN_hashed']  # First MRN hash
    mobi_hash = table3.loc[0, 'mobi_id_hashed']  # First mobi_id hash
    mapping_hash = table4.loc[0, 'hashed_id']  # First mapping hash
    
    # All related IDs should have the same hash
    assert mrn_hash == mobi_hash == mapping_hash


def test_lookup_table_creation(processor, sample_data):
    """Test creation of the ID lookup table."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Verify lookup table was created
    lookup_path = sample_data / 'id_lookup_table.csv'
    assert lookup_path.exists()
    
    # Read lookup table
    lookup_df = pd.read_csv(lookup_path)
    
    # Check structure
    assert 'original_id' in lookup_df.columns
    assert 'hashed_id' in lookup_df.columns
    assert 'from_mapping' in lookup_df.columns
    
    # Check mapping IDs are marked correctly
    mapping_ids = lookup_df[lookup_df['from_mapping']]
    assert len(mapping_ids) > 0
    assert all(mapping_ids['from_mapping'])


def test_backup_creation(processor, sample_data):
    """Test that backup files are created."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Check backup files exist
    assert (sample_data / 'table1.csv.backup').exists()
    assert (sample_data / 'subfolder/table2.csv.backup').exists()
    assert (sample_data / 'subfolder/deeper/table3.csv.backup').exists()
    assert (sample_data / 'table4.csv.backup').exists()


def test_error_handling(processor, sample_data):
    """Test error handling for missing or invalid files."""
    with pytest.raises(ValueError):
        processor.process_all_files(sample_data / 'nonexistent.csv')
    
    # Create invalid mapping file
    invalid_mapping = pd.DataFrame({
        'mapping_file': ['nonexistent.csv'],
        'mapping_id': ['MRN'],
        'source_file': ['also_nonexistent.csv'],
        'source_id': ['id']
    })
    invalid_path = sample_data / 'invalid_mapping.csv'
    invalid_mapping.to_csv(invalid_path, index=False)
    
    with pytest.raises(ValueError):
        processor.process_all_files(invalid_path) 


def test_mapping_file_preservation(processor, sample_data):
    """Test that mapping file is not modified."""
    mapping_path = sample_data / 'mapping.csv'
    mapping_file = 'table4.csv'
    
    # Read original mapping file
    original_df = pd.read_csv(sample_data / mapping_file)
    original_mrn = original_df['MRN'].copy()
    original_mobi = original_df['mobi_id'].copy()
    
    # Process all files
    processor.process_all_files(mapping_path)
    
    # Read mapping file after processing
    processed_df = pd.read_csv(sample_data / mapping_file)
    
    # Verify mapping file is unchanged
    pd.testing.assert_series_equal(processed_df['MRN'], original_mrn)
    pd.testing.assert_series_equal(processed_df['mobi_id'], original_mobi)
    assert set(processed_df.columns) == {'MRN', 'mobi_id'}  # No new columns added


def test_source_file_updates(processor, sample_data):
    """Test that source files are updated with hashed IDs."""
    mapping_path = sample_data / 'mapping.csv'
    
    # Store original IDs
    table1_orig = pd.read_csv(sample_data / 'table1.csv')
    table2_orig = pd.read_csv(sample_data / 'subfolder/table2.csv')
    table3_orig = pd.read_csv(sample_data / 'subfolder/deeper/table3.csv')
    
    original_ids = {
        'patientid': table1_orig['patientid'].iloc[0],
        'MRN': table2_orig['MRN'].iloc[0],
        'mobi_id': table3_orig['mobi_id'].iloc[0]
    }
    
    # Process files
    processor.process_all_files(mapping_path)
    
    # Read updated files
    table1 = pd.read_csv(sample_data / 'table1.csv')
    table2 = pd.read_csv(sample_data / 'subfolder/table2.csv')
    table3 = pd.read_csv(sample_data / 'subfolder/deeper/table3.csv')
    
    # Verify IDs are hashed
    assert table1['patientid'].iloc[0] != original_ids['patientid']
    assert table2['MRN'].iloc[0] != original_ids['MRN']
    assert table3['mobi_id'].iloc[0] != original_ids['mobi_id']
    
    # Verify hashed IDs are consistent
    assert table2['MRN'].iloc[0] == table3['mobi_id'].iloc[0]  # Related IDs should have same hash


def test_id_consistency_across_files(processor, sample_data):
    """Test that related IDs get the same hash value across all files."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Read processed files
    table1 = pd.read_csv(sample_data / 'table1.csv')
    table2 = pd.read_csv(sample_data / 'subfolder/table2.csv')
    table3 = pd.read_csv(sample_data / 'subfolder/deeper/table3.csv')
    
    # Get hashed values
    p1_hash = table1['patientid'].iloc[0]  # First patient ID hash
    m1_hash = table2['MRN'].iloc[0]        # First MRN hash
    mb1_hash = table3['mobi_id'].iloc[0]   # First mobi_id hash
    
    # All related IDs should have the same hash
    assert p1_hash == m1_hash == mb1_hash
    
    # Verify all hashes are SHA-256 length
    assert all(len(h) == 64 for h in [p1_hash, m1_hash, mb1_hash])


def test_lookup_table_creation(processor, sample_data):
    """Test creation of the ID lookup table."""
    mapping_path = sample_data / 'mapping.csv'
    processor.process_all_files(mapping_path)
    
    # Verify lookup table was created
    lookup_path = sample_data / 'id_lookup_table.csv'
    assert lookup_path.exists()
    
    # Read lookup table
    lookup_df = pd.read_csv(lookup_path)
    
    # Check structure
    assert 'original_id' in lookup_df.columns
    assert 'hashed_id' in lookup_df.columns
    assert 'from_mapping' in lookup_df.columns
    
    # Check mapping IDs are marked correctly
    mapping_ids = lookup_df[lookup_df['from_mapping']]
    assert len(mapping_ids) > 0
    assert all(mapping_ids['from_mapping'])
    
    # Verify ID relationships
    p1_hash = lookup_df[lookup_df['original_id'] == 'P001']['hashed_id'].iloc[0]
    m1_hash = lookup_df[lookup_df['original_id'] == 'M001']['hashed_id'].iloc[0]
    mb1_hash = lookup_df[lookup_df['original_id'] == 'MB001']['hashed_id'].iloc[0]
    assert p1_hash == m1_hash == mb1_hash 