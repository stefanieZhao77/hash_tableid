import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from id_processor import IDProcessor
import threading
import queue
import time

class IDProcessorGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ID Anonymization Tool")
        self.window.geometry("800x600")  # Made window larger
        
        # Instance variables
        self.processor = None
        self.processing = False
        self.process_thread = None
        self.update_queue = queue.Queue()
        self.processed_files = set()  # Track which files have been processed
        
        # Instructions
        self.instructions_frame = tk.LabelFrame(self.window, text="Instructions", padx=10, pady=5)
        self.instructions_frame.pack(fill="x", padx=10, pady=5)
        
        self.instructions = tk.Text(self.instructions_frame, height=8, width=70)
        self.instructions.pack(padx=10, pady=10)
        self.instructions.insert("1.0", """1. Create a mapping.csv file with these columns:
   - mapping_file: The file containing ID relationships (e.g., mapping.csv)
   - mapping_id: The ID column in the mapping file (e.g., id_a, id_b)
   - source_file: The file to be anonymized (e.g., table1.csv)
   - source_id: The ID column in the source file (e.g., id_a, id_b)

2. Click 'Browse' to select your mapping.csv file
3. Click 'Start Processing' to begin anonymization
4. Click 'Stop Processing' to stop the current processing operation""")
        self.instructions.config(state="disabled")
        
        # Mapping file path
        self.mapping_frame = tk.LabelFrame(self.window, text="Step 1: Select Mapping File", padx=10, pady=5)
        self.mapping_frame.pack(fill="x", padx=10, pady=5)
        
        self.mapping_path = tk.StringVar()
        self.mapping_label = tk.Label(self.mapping_frame, textvariable=self.mapping_path, width=50)
        self.mapping_label.pack(side="left", padx=5)
        
        self.mapping_button = tk.Button(self.mapping_frame, text="Browse", command=self.select_mapping_file)
        self.mapping_button.pack(side="right", padx=5)
        
        # Process and Stop buttons frame
        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack(pady=5)
        
        self.process_button = tk.Button(self.button_frame, text="Start Processing", command=self.process_files)
        self.process_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(self.button_frame, text="Stop Processing", command=self.stop_processing, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Progress bar and status
        self.progress_frame = tk.Frame(self.window)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = tk.Label(self.progress_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # Status Text Area
        self.status_frame = tk.LabelFrame(self.window, text="Processing Status", padx=10, pady=5)
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add scrollbar to status text
        self.status_scroll = tk.Scrollbar(self.status_frame)
        self.status_scroll.pack(side="right", fill="y")
        
        self.status_text = tk.Text(self.status_frame, height=10, width=70, yscrollcommand=self.status_scroll.set)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.status_scroll.config(command=self.status_text.yview)
        
        # Start the update checker
        self.window.after(100, self.check_updates)
    
    def add_status_message(self, message):
        """Add a message to the status text area."""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert("end", f"[{timestamp}] {message}\n")
        self.status_text.see("end")  # Scroll to bottom
    
    def clear_status_messages(self):
        """Clear all status messages."""
        self.status_text.delete("1.0", "end")
    
    def check_updates(self):
        """Check for updates from the processing thread."""
        try:
            while True:  # Process all pending updates
                update = self.update_queue.get_nowait()
                if isinstance(update, tuple):
                    update_type, value = update
                    if update_type == "progress":
                        self.progress_var.set(value)
                    elif update_type == "status":
                        self.status_var.set(value)
                        self.add_status_message(value)
                    elif update_type == "message":
                        self.add_status_message(value)
                    elif update_type == "complete":
                        self.processing_complete(value)
                    elif update_type == "error":
                        self.processing_error(value)
        except queue.Empty:
            pass
        finally:
            # Schedule the next check
            self.window.after(100, self.check_updates)
    
    def select_mapping_file(self):
        filename = filedialog.askopenfilename(
            title="Select Mapping File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")]
        )
        if filename:
            self.mapping_path.set(filename)
    
    def stop_processing(self):
        """Stop the current processing operation."""
        if self.processor and self.processing:
            self.processor.stop()
            self.status_var.set("Stopping... (will complete current file)")
            self.stop_button.config(state="disabled")
    
    def processing_thread(self):
        """Thread function for file processing."""
        try:
            # Fix the progress callback to handle only the progress value
            def progress_callback(progress):
                self.update_queue.put(("progress", progress))
            
            def status_callback(message):
                self.update_queue.put(("message", message))
                
            self.processor = IDProcessor(
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            self.processor.process_all_files(Path(self.mapping_path.get()))
            
            if not self.processor.is_running:  # If processing was stopped
                self.update_queue.put(("complete", "stopped"))
            else:
                self.update_queue.put(("complete", "success"))
        except Exception as e:
            self.update_queue.put(("error", str(e)))
    
    def processing_complete(self, status):
        """Handle completion of processing."""
        self.processing = False
        self.process_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if status == "stopped":
            message = "Processing stopped by user"
            self.status_var.set(message)
            self.add_status_message(message)
            messagebox.showinfo("Stopped", 
                "Processing was stopped.\n\n"
                "- Processed files have been saved\n"
                "- ID lookup table updated\n"
                "- You can resume processing later"
            )
        else:
            message = "Processing completed successfully!"
            self.status_var.set(message)
            self.add_status_message(message)
            messagebox.showinfo("Success", 
                "Files processed successfully!\n\n"
                "- Original files backed up with '.backup' extension\n"
                "- ID lookup table created as 'id_lookup_table.csv'"
            )
            self.status_var.set("Ready")
            self.progress_var.set(0)
    
    def processing_error(self, error_msg):
        """Handle processing error."""
        self.processing = False
        self.process_button.config(state="normal")
        self.stop_button.config(state="disabled")
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
        self.status_var.set("Error occurred")
        self.progress_var.set(0)
    
    def process_files(self):
        if not self.mapping_path.get():
            messagebox.showerror("Error", "Please select a mapping file first")
            return
            
        self.status_var.set("Processing files...")
        self.process_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set(0)
        self.processing = True
        self.clear_status_messages()  # Clear previous messages
        
        # Start processing in a separate thread
        self.process_thread = threading.Thread(target=self.processing_thread)
        self.process_thread.daemon = True  # Thread will be killed when main program exits
        self.process_thread.start()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = IDProcessorGUI()
    app.run() 