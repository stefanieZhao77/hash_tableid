import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from id_processor import IDProcessor

class IDProcessorGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ID Anonymization Tool")
        self.window.geometry("600x400")
        
        # Mapping file path
        self.mapping_frame = tk.LabelFrame(self.window, text="Step 1: Select Mapping File", padx=10, pady=5)
        self.mapping_frame.pack(fill="x", padx=10, pady=5)
        
        self.mapping_path = tk.StringVar()
        self.mapping_label = tk.Label(self.mapping_frame, textvariable=self.mapping_path, width=50)
        self.mapping_label.pack(side="left", padx=5)
        
        self.mapping_button = tk.Button(self.mapping_frame, text="Browse", command=self.select_mapping_file)
        self.mapping_button.pack(side="right", padx=5)
        
        # Instructions
        self.instructions = tk.Text(self.window, height=10, width=60)
        self.instructions.pack(padx=10, pady=10)
        self.instructions.insert("1.0", """Instructions:

1. Create a mapping.csv file with these columns:
   - mapping_file: The file containing ID relationships (e.g., mapping.csv)
   - mapping_id: The ID column in the mapping file (e.g., MRN, mobi_id)
   - source_file: The file to be anonymized (e.g., patient_data.csv)
   - source_id: The ID column in the source file

2. Click 'Browse' to select your mapping.csv file

3. Click 'Start Processing' to begin anonymization

Note: Original files will be backed up with '.backup' extension""")
        self.instructions.config(state="disabled")
        
        # Process button
        self.process_button = tk.Button(self.window, text="Start Processing", command=self.process_files)
        self.process_button.pack(pady=10)
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = tk.Label(self.window, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
    def select_mapping_file(self):
        filename = filedialog.askopenfilename(
            title="Select Mapping File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")]
        )
        if filename:
            self.mapping_path.set(filename)
    
    def process_files(self):
        if not self.mapping_path.get():
            messagebox.showerror("Error", "Please select a mapping file first")
            return
            
        try:
            self.status_var.set("Processing files...")
            self.window.update()
            
            processor = IDProcessor()
            processor.process_all_files(Path(self.mapping_path.get()))
            
            messagebox.showinfo("Success", 
                "Files processed successfully!\n\n"
                "- Original files backed up with '.backup' extension\n"
                "- ID lookup table created as 'id_lookup_table.csv'"
            )
            self.status_var.set("Ready")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_var.set("Error occurred")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = IDProcessorGUI()
    app.run() 