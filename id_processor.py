import pandas as pd
import networkx as nx
import hashlib
import uuid
from pathlib import Path
import tempfile
import os
import shutil
from typing import Dict, List, Set, Union
from tqdm import tqdm
import time
import gc
import random


class IDProcessor:
    def __init__(self, progress_callback=None, status_callback=None):
        self.hash_table: Dict[str, str] = {}
        self.not_hashed_ids: Set[str] = set()  # Track IDs that weren't hashed
        self.processed_files: Set[Path] = set()  # Track processed files
        self.is_running: bool = False
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self._load_existing_lookup_table()
        
    def _send_status(self, message: str) -> None:
        """Send a status message to the GUI."""
        if self.status_callback:
            self.status_callback(message)
        print(message)  # Also print to console
        
    def _load_existing_lookup_table(self) -> None:
        """Load existing lookup table if it exists."""
        lookup_path = Path('id_lookup_table.csv')
        if lookup_path.exists():
            try:
                lookup_df = pd.read_csv(lookup_path)
                # Create bidirectional mapping
                for _, row in lookup_df.iterrows():
                    original_id = str(row['original_id'])
                    hashed_id = str(row['hashed_id'])
                    self.hash_table[original_id] = hashed_id
                self._send_status(f"Loaded {len(lookup_df)} existing ID mappings from lookup table")
            except Exception as e:
                self._send_status(f"Warning: Could not load existing lookup table: {str(e)}")

    def stop(self) -> None:
        """Stop the processing."""
        self.is_running = False
        print("Processing will stop after current file completes...")

    def hash_id(self, id_value: str) -> str:
        """Hash an ID using SHA-256."""
        if not isinstance(id_value, str):
            id_value = str(id_value)
            
        # If the ID is already in our hash table (either as original or hashed), return the hashed value
        if id_value in self.hash_table:
            return self.hash_table[id_value]
            
        # Check if the input looks like a SHA-256 hash (64 hex characters)
        if len(id_value) == 64 and all(c in '0123456789abcdef' for c in id_value.lower()):
            self.hash_table[id_value] = id_value
            return id_value
            
        # If not found and not a hash, create new hash
        hashed_value = hashlib.sha256(id_value.encode()).hexdigest()
        self.hash_table[id_value] = hashed_value
        return hashed_value

    def read_file(self, file_path: Path) -> pd.DataFrame:
        """Read CSV or Excel file."""
        try:
            suffix = file_path.suffix.lower()
            if suffix == '.csv':
                return pd.read_csv(file_path)
            elif suffix == '.xlsx':
                return pd.read_excel(file_path, engine='openpyxl')
            elif suffix == '.xls':
                return pd.read_excel(file_path, engine='xlrd')
            else:
                raise ValueError(f"Unsupported file format: {suffix}")
        except Exception as e:
            raise ValueError(f"Failed to read file {file_path}: {str(e)}")

    def find_files(self, mapping_df: pd.DataFrame) -> List[Path]:
        """Find all files mentioned in the mapping file."""
        files = set()
        
        def resolve_file_path(file_path: str) -> Path:
            """Resolve file path, checking if it's absolute or relative."""
            path = Path(file_path)
            if path.is_absolute() and path.exists():
                return path
            raise ValueError(f"File {file_path} not found or is not an absolute path")
        
        # Add the mapping file
        mapping_file = mapping_df['mapping_file'].iloc[0]
        try:
            mapping_path = resolve_file_path(mapping_file)
            files.add(mapping_path)
        except ValueError as e:
            raise ValueError(f"Mapping file {mapping_file} not found or is not an absolute path")
        
        # Add all source files
        for file_path in mapping_df['source_file'].unique():
            try:
                full_path = resolve_file_path(file_path)
                files.add(full_path)
            except ValueError as e:
                raise ValueError(f"Source file {file_path} not found or is not an absolute path")
        
        return list(files)

    def create_id_mapping(self, mapping_file_path: Path, mapping_df: pd.DataFrame) -> tuple[Dict[str, str], Dict[str, str]]:
        """Create a mapping of original IDs to hashed IDs based on relationships in mapping file."""
        # Read the mapping table
        mapping_table = self.read_file(mapping_file_path)
        
        # Create dictionaries to store ID relationships and consent status
        id_mapping = {}
        consent_status_mapping = {}
        
        # First, establish relationships from the mapping table
        for _, row in mapping_table.iterrows():
            ids_in_row = []
            for col in mapping_df['mapping_id'].unique():
                if col in row and pd.notna(row[col]):
                    ids_in_row.append(str(row[col]))
            
            # Get consent status for this row, default to "none" if not present
            consent_status = str(row.get('consent_status', 'none')).lower()
            if consent_status not in ['granted', 'revoked', 'none', 'id not found']:
                consent_status = 'none'
            
            # If we found related IDs, process them based on consent status
            if ids_in_row:
                # Only hash IDs if consent is granted
                if consent_status == 'granted':
                    hashed_id = self.hash_id(ids_in_row[0])
                    for id_val in ids_in_row:
                        id_mapping[id_val] = hashed_id
                # Store consent status for all IDs in the row
                for id_val in ids_in_row:
                    consent_status_mapping[id_val] = consent_status
        
        return id_mapping, consent_status_mapping

    def update_file_ids(self, file_path: Path, id_column: str, id_mapping: Dict[str, str], consent_status_mapping: Dict[str, str]) -> None:
        """Update IDs in a file using the provided ID mapping and create training table."""
        if not self.is_running:
            self._send_status(f"Skipping {file_path} as processing was stopped")
            return

        # Check if file has already been processed
        if file_path in self.processed_files:
            self._send_status(f"Skipping {file_path} - already processed")
            return

        self._send_status(f"Processing file: {file_path}")
        df = self.read_file(file_path)
        
        if id_column not in df.columns:
            raise ValueError(f"Column {id_column} not found in {file_path}")
        
        # Count how many IDs will be updated
        original_ids = df[id_column].astype(str).unique()
        self._send_status(f"Found {len(original_ids)} unique IDs to process in {file_path}")
        
        # Add consent_status column to original table
        df['consent_status'] = df[id_column].astype(str).map(lambda x: consent_status_mapping.get(x, 'ID not found'))
        
        # Track IDs that aren't being hashed
        for id_val in original_ids:
            if str(id_val) not in id_mapping:
                self.not_hashed_ids.add(str(id_val))
        
        # Create training table with only granted consent records and hashed IDs
        training_df = df[df['consent_status'] == 'granted'].copy()
        # Update IDs in training table only
        training_df[id_column] = training_df[id_column].astype(str).map(lambda x: id_mapping.get(x, x))
        training_file_path = file_path.parent / f"{file_path.stem}_training{file_path.suffix}"
        
        # Create a temporary file in the same directory as the target file
        temp_dir = file_path.parent
        suffix = file_path.suffix.lower()
        
        # Generate a unique temporary filename
        temp_suffix = f"_{random.randint(1000, 9999)}{suffix}"
        temp_path = temp_dir / f"temp{temp_suffix}"
        
        try:
            self._send_status(f"Saving updated files: {file_path} and {training_file_path}")
            # First, write to the temporary file
            if suffix == '.csv':
                df.to_csv(temp_path, index=False)
                training_df.to_csv(training_file_path, index=False)
            elif suffix == '.xlsx':
                with pd.ExcelWriter(str(temp_path), engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                with pd.ExcelWriter(str(training_file_path), engine='openpyxl') as writer:
                    training_df.to_excel(writer, index=False)
            elif suffix == '.xls':
                with pd.ExcelWriter(str(temp_path), engine='xlwt') as writer:
                    df.to_excel(writer, index=False)
                with pd.ExcelWriter(str(training_file_path), engine='xlwt') as writer:
                    training_df.to_excel(writer, index=False)
            
            # Force sync to ensure file is written
            if hasattr(os, 'sync'):
                os.sync()
            
            # Give some time for the file system to finish writing
            time.sleep(1)
            
            # Now try to replace the original file
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # First, try to remove the original file if it exists
                    if file_path.exists():
                        os.remove(file_path)
                        time.sleep(0.5)  # Wait a bit after deletion
                    
                    # Now try to rename the temp file
                    os.rename(temp_path, file_path)
                    self._send_status(f"Successfully updated {file_path} and created {training_file_path}")
                    self.processed_files.add(file_path)  # Mark file as processed
                    break
                except Exception as e:
                    if attempt == max_attempts - 1:  # Last attempt
                        raise
                    self._send_status(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # Wait before retry
                    gc.collect()  # Force garbage collection
                
        except Exception as e:
            # Clean up temporary file if it exists
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise Exception(f"Failed to update file {file_path}: {str(e)}")
        finally:
            # Final cleanup
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except:
                    pass
            gc.collect()

    def create_lookup_table(self, id_mapping: Dict[str, str], consent_status_mapping: Dict[str, str]) -> pd.DataFrame:
        """Create a lookup table of original IDs and their hashed values."""
        records = []
        processed_ids = set()
        
        # First add all IDs from the mapping that have granted consent
        for original_id, hashed_id in id_mapping.items():
            if consent_status_mapping.get(original_id) == 'granted':
                records.append({
                    'original_id': original_id,
                    'hashed_id': hashed_id,
                    'consent_status': 'granted',
                    'from_mapping': True
                })
                processed_ids.add(original_id)
        
        # Then add any additional IDs that were hashed and have granted consent
        for original_id, hashed_id in self.hash_table.items():
            if original_id not in processed_ids and consent_status_mapping.get(original_id) == 'granted':
                records.append({
                    'original_id': original_id,
                    'hashed_id': hashed_id,
                    'consent_status': 'granted'
                })
                processed_ids.add(original_id)
        
        # Add all remaining IDs from consent_status_mapping that weren't processed
        for original_id, status in consent_status_mapping.items():
            if original_id not in processed_ids:
                records.append({
                    'original_id': original_id,
                    'hashed_id': original_id,  # Use original ID as no hashing was done
                    'consent_status': status
                })
                processed_ids.add(original_id)
        
        # Add all non-hashed IDs that we found in the data tables
        for original_id in self.not_hashed_ids:
            if original_id not in processed_ids:
                records.append({
                    'original_id': original_id,
                    'hashed_id': original_id,  # Use original ID as no hashing was done
                    'consent_status': 'ID not found',
                })
        
        return pd.DataFrame(records)

    def create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file before modifying it."""
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path

    def process_all_files(self, mapping_path: Path) -> None:
        """Process all files based on the mapping file."""
        self.is_running = True
        self._send_status(f"Starting processing with mapping file: {mapping_path}")
        
        if not mapping_path.exists():
            raise ValueError(f"Mapping file {mapping_path} not found")
            
        # Read mapping file
        try:
            if mapping_path.suffix.lower() == '.csv':
                mapping_df = pd.read_csv(mapping_path)
            else:
                mapping_df = pd.read_excel(mapping_path, engine='openpyxl')
                
            # Initialize or update the processed column
            if 'processed' not in mapping_df.columns:
                # If the column doesn't exist, add it and set all values to False
                mapping_df.loc[:, 'processed'] = False
                # Save the updated mapping file with the new column
                if mapping_path.suffix.lower() == '.csv':
                    mapping_df.to_csv(mapping_path, index=False)
                else:
                    mapping_df.to_excel(mapping_path, index=False)
                self._send_status("Added 'processed' column to mapping file to record file status")
            else:
                # Convert existing processed column to boolean, treating NaN as False
                mapping_df['processed'] = mapping_df['processed'].fillna(False).astype(bool)
                
            self._send_status(f"Successfully read mapping file with {len(mapping_df)} entries")
        except Exception as e:
            raise ValueError(f"Could not read mapping file {mapping_path}: {str(e)}")
            
        required_cols = ['mapping_file', 'mapping_id', 'source_file', 'source_id']
        if not all(col in mapping_df.columns for col in required_cols):
            raise ValueError(f"Missing required columns {required_cols} in {mapping_path}")
        
        # Find all files using paths from mapping file
        files = self.find_files(mapping_df)
        total_files = len(files)
        
        # Get unprocessed rows using boolean indexing
        unprocessed_rows = mapping_df[mapping_df['processed'] == False]
        self._send_status(f"Found {len(unprocessed_rows)} files to process ({len(mapping_df) - len(unprocessed_rows)} already processed)")
        
        if len(unprocessed_rows) == 0:
            self._send_status("No files to process - all files are marked as processed")
            if self.progress_callback:
                self.progress_callback(100)
            return
        
        # Create backups of source files before modification
        backups = {}
        for i, (_, row) in enumerate(unprocessed_rows.iterrows()):
            source_path = Path(row['source_file'])
            if source_path.name != mapping_df['mapping_file'].iloc[0] and not row['processed']:
                backups[source_path] = self.create_backup(source_path)
                self._send_status(f"Created backup of {source_path}")
            if self.progress_callback:
                self.progress_callback(int((i / total_files) * 20))  # First 20% for backups
        
        try:
            # First, get the mapping file to establish ID relationships
            # Get mapping file from unprocessed rows
            mapping_file = unprocessed_rows['mapping_file'].iloc[0]
            mapping_file_path = next(f for f in files if f.name == Path(mapping_file).name)
            
            # Create ID mapping based on relationships in mapping file
            self._send_status("Creating ID mappings from relationships...")
            id_mapping, consent_status_mapping = self.create_id_mapping(mapping_file_path, mapping_df)
            self._send_status(f"Created {len(id_mapping)} ID mappings")
            if self.progress_callback:
                self.progress_callback(25)  # 25% after creating ID mapping
            
            # Process each source file
            total_rows = len(unprocessed_rows)
            processed_files = 0
            
            for i, (idx, row) in enumerate(unprocessed_rows.iterrows()):
                if not self.is_running:
                    self._send_status("Processing stopped by user")
                    break
                
                source_file = row['source_file']
                source_id = row['source_id']
                source_path = next(f for f in files if f.name == Path(source_file).name)
                
                if source_path.name != mapping_file and not row['processed']:  # Skip mapping file and processed files
                    self.update_file_ids(source_path, source_id, id_mapping, consent_status_mapping)
                    processed_files += 1
                    # Update processed status in the DataFrame
                    mapping_df.loc[idx, 'processed'] = True
                    
                    # Save the updated mapping file after each successful file processing
                    if mapping_path.suffix.lower() == '.csv':
                        mapping_df.to_csv(mapping_path, index=False)
                    else:
                        mapping_df.to_excel(mapping_path, index=False)
                    self._send_status(f"Updated processing status in mapping file")
                    
                if self.progress_callback:
                    # Progress from 25% to 90% during file processing
                    progress = 25 + int((i + 1) / total_rows * 65)
                    self.progress_callback(progress)

             # Update lookup table after each file is processed
            lookup_df = self.create_lookup_table(id_mapping, consent_status_mapping)
            lookup_path = Path('id_lookup_table.csv')
            lookup_df.to_csv(lookup_path, index=False)
            self._send_status(f"Updated lookup table with {len(lookup_df)} entries")

            if self.progress_callback:
                self.progress_callback(100)  # Complete
            
            if not self.is_running:
                self._send_status("Processing was stopped by user. All processed files and IDs have been saved.")
            else:
                self._send_status(f"Processing complete: {processed_files} files processed")
                self._send_status("All files have been backed up with '.backup' extension")
            
        except Exception as e:
            self._send_status(f"Error during processing: {str(e)}")
            raise
        finally:
            self.is_running = False


def main():
    """Main function that processes files based on a mapping file."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hash IDs in CSV/Excel files based on mapping file.')
    parser.add_argument('mapping_file', type=str, help='Path to the mapping CSV file')
    
    args = parser.parse_args()
    mapping_path = Path(args.mapping_file)
    
    try:
        processor = IDProcessor()
        processor.process_all_files(mapping_path)
        print("Successfully processed all files.")
    except Exception as e:
        print(f"Error processing files: {str(e)}")
        raise


if __name__ == "__main__":
    main()