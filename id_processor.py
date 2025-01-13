import pandas as pd
import networkx as nx
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Set, Union
from tqdm import tqdm


class IDProcessor:
    def __init__(self):
        self.hash_table: Dict[str, str] = {}
        
    def hash_id(self, id_value: str) -> str:
        """Hash an ID using SHA-256."""
        if not isinstance(id_value, str):
            id_value = str(id_value)
        if id_value not in self.hash_table:
            self.hash_table[id_value] = hashlib.sha256(id_value.encode()).hexdigest()
        return self.hash_table[id_value]

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

    def find_files(self, base_path: Path, mapping_df: pd.DataFrame) -> List[Path]:
        """Find all files mentioned in the mapping file, searching recursively if needed."""
        files = set()
        
        def find_file_in_directory(filename: str, search_path: Path) -> Path:
            """Search for a file recursively in all subdirectories."""
            # First try direct match
            if (search_path / filename).exists():
                return search_path / filename
                
            # Search in all subdirectories
            for path in search_path.rglob("*"):
                if path.is_dir():
                    potential_file = path / filename
                    if potential_file.exists():
                        return potential_file
            
            raise ValueError(f"File {filename} not found in {search_path} or its subdirectories")
        
        # Add the mapping file
        mapping_file = mapping_df['mapping_file'].iloc[0]
        try:
            mapping_path = find_file_in_directory(mapping_file, base_path)
            files.add(mapping_path)
        except ValueError as e:
            raise ValueError(f"Mapping file {mapping_file} not found in {base_path} or its subdirectories")
        
        # Add all source files
        for file_path in mapping_df['source_file'].unique():
            try:
                full_path = find_file_in_directory(file_path, base_path)
                files.add(full_path)
            except ValueError as e:
                # Try as absolute path if relative path search fails
                abs_path = Path(file_path)
                if abs_path.exists():
                    files.add(abs_path)
                else:
                    raise ValueError(f"Source file {file_path} not found in {base_path} or its subdirectories")
        
        return list(files)

    def create_id_mapping(self, mapping_file_path: Path, mapping_df: pd.DataFrame) -> Dict[str, str]:
        """Create a mapping of original IDs to hashed IDs based on relationships in mapping file."""
        # Read the mapping table (e.g., table4.csv)
        mapping_table = self.read_file(mapping_file_path)
        
        # Create a dictionary to store ID relationships
        id_mapping = {}
        
        # First, establish relationships from the mapping table
        for _, row in mapping_table.iterrows():
            ids_in_row = []
            for col in mapping_df['mapping_id'].unique():
                if col in row and pd.notna(row[col]):
                    ids_in_row.append(str(row[col]))
            
            # If we found related IDs, hash the first one and use it for all related IDs
            if ids_in_row:
                hashed_id = self.hash_id(ids_in_row[0])
                for id_val in ids_in_row:
                    id_mapping[id_val] = hashed_id
        
        return id_mapping

    def update_file_ids(self, file_path: Path, id_column: str, id_mapping: Dict[str, str]) -> None:
        """Update IDs in a file using the provided ID mapping."""
        df = self.read_file(file_path)
        
        if id_column not in df.columns:
            raise ValueError(f"Column {id_column} not found in {file_path}")
        
        # Update the ID column with hashed values
        df[id_column] = df[id_column].astype(str).map(lambda x: id_mapping.get(x, self.hash_id(x)))
        
        # Save back to file
        suffix = file_path.suffix.lower()
        if suffix == '.csv':
            df.to_csv(file_path, index=False)
        elif suffix == '.xlsx':
            df.to_excel(file_path, index=False, engine='openpyxl')
        elif suffix == '.xls':
            df.to_excel(file_path, index=False, engine='xlwt')

    def create_lookup_table(self, id_mapping: Dict[str, str]) -> pd.DataFrame:
        """Create a lookup table of original IDs and their hashed values."""
        records = []
        # First add all IDs from the mapping
        for original_id, hashed_id in id_mapping.items():
            records.append({
                'original_id': original_id,
                'hashed_id': hashed_id,
                'from_mapping': True
            })
        
        # Then add any additional IDs that were hashed
        for original_id, hashed_id in self.hash_table.items():
            if original_id not in id_mapping:
                records.append({
                    'original_id': original_id,
                    'hashed_id': hashed_id,
                    'from_mapping': False
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
        if not mapping_path.exists():
            raise ValueError(f"Mapping file {mapping_path} not found")
            
        # Read mapping file
        try:
            if mapping_path.suffix.lower() == '.csv':
                mapping_df = pd.read_csv(mapping_path)
            else:
                mapping_df = pd.read_excel(mapping_path, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"Could not read mapping file {mapping_path}: {str(e)}")
            
        required_cols = ['mapping_file', 'mapping_id', 'source_file', 'source_id']
        if not all(col in mapping_df.columns for col in required_cols):
            raise ValueError(f"Missing required columns {required_cols} in {mapping_path}")
        
        # Find all files
        base_path = mapping_path.parent
        files = self.find_files(base_path, mapping_df)
        
        # Create backups of source files before modification
        backups = {}
        for file_path in files:
            if file_path.name != mapping_df['mapping_file'].iloc[0]:  # Don't backup mapping file
                backups[file_path] = self.create_backup(file_path)
        
        try:
            # First, get the mapping file to establish ID relationships
            mapping_file = mapping_df['mapping_file'].iloc[0]
            mapping_file_path = next(f for f in files if f.name == mapping_file)
            
            # Create ID mapping based on relationships in mapping file
            id_mapping = self.create_id_mapping(mapping_file_path, mapping_df)
            
            # Process each source file
            for _, row in mapping_df.iterrows():
                source_file = row['source_file']
                source_id = row['source_id']
                source_path = next(f for f in files if f.name == Path(source_file).name)
                if source_path.name != mapping_file:  # Skip mapping file
                    self.update_file_ids(source_path, source_id, id_mapping)
            
            # Create and save lookup table
            lookup_df = self.create_lookup_table(id_mapping)
            lookup_path = base_path / 'id_lookup_table.csv'
            lookup_df.to_csv(lookup_path, index=False)
            print(f"Created lookup table at: {lookup_path}")
            print("Created backups of original files with '.backup' extension")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            print("Original files have been preserved with '.backup' extension")


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