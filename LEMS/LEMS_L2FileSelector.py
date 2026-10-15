# Helper for Level 2 file selection across LEMS tools
import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox


def find_l2_files(folder_path):
    """
    Search recursively for files ending with 'UnFormattedDataL2.csv' in folder_path.
    Matches files ending with 'UnFormattedDataL2.csv' (same pattern as LEMS_DataEntry_L3).
    """
    found = []
    if not folder_path or not os.path.isdir(folder_path):
        return found
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('UnFormattedDataL2.csv'):
                found.append(os.path.join(root, file))
    return sorted(found)


def read_saved_l2_paths(folder_path, csv_filename="UnformattedDataL2FilePaths.csv"):
    """
    Reads existing file paths from UnformattedDataL2FilePaths.csv in folder_path.
    """
    saved = []
    csv_path = os.path.join(folder_path, csv_filename)
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        saved.append(row[0].strip())
        except Exception as e:
            print(f"Warning: could not read {csv_path}: {e}")
    return saved


def write_saved_l2_paths(folder_path, paths, csv_filename="UnformattedDataL2FilePaths.csv"):
    """
    Writes selected file paths to UnformattedDataL2FilePaths.csv in folder_path.
    """
    csv_path = os.path.join(folder_path, csv_filename)
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for path in paths:
                writer.writerow([path])
        return True
    except Exception as e:
        print(f"Warning: could not write {csv_path}: {e}")
        return False


def select_l2_files_gui(initial_dir=None):
    """
    GUI file selector matching LEMS_DataEntry_L3 behavior:
    1. Prompts user to select a folder containing Level 2 outputs.
    2. Searches for UnFormattedDataL2.csv files in that folder.
    3. Reads any existing selections in UnformattedDataL2FilePaths.csv.
    4. Displays a multi-select Tkinter dialog with existing files preselected.
    5. On OK, writes selection to UnformattedDataL2FilePaths.csv and returns (folder_path, selected_paths).
       If cancelled, returns (None, []).
    """
    root = tk.Tk()
    root.withdraw()

    current_folder = initial_dir
    while not current_folder:
        selected_dir = filedialog.askdirectory(
            title="Select folder containing Level 2 test outputs",
            initialdir=initial_dir or os.getcwd()
        )
        if not selected_dir:
            root.destroy()
            return None, []
        current_folder = selected_dir

    result = {'folder': None, 'paths': []}

    def run_selection_window(folder):
        existing_paths = read_saved_l2_paths(folder)
        all_l2_files = find_l2_files(folder)

        # Combine existing and new files (preserving saved order first, matching DataEntry_L3)
        postselect = [f for f in all_l2_files if f not in existing_paths]
        full_files = existing_paths + postselect

        if not full_files:
            messagebox.showerror(
                "Error",
                f"No files ending with 'UnFormattedDataL2.csv' were found inside:\n{folder}\n\nPlease check folder contents and try again."
            )
            # Ask if user wants to select a different folder
            new_dir = filedialog.askdirectory(
                title="Select folder containing Level 2 test outputs",
                initialdir=folder
            )
            if new_dir:
                return run_selection_window(new_dir)
            else:
                return

        # Build window
        win = tk.Toplevel(root)
        win.title("Select Tests to Compare")
        win.geometry("900x550")
        win.minsize(600, 350)

        # Instructions / header frame
        header_frame = tk.Frame(win, padx=10, pady=10)
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text=f"Selected Folder: {folder}",
            font=("Helvetica", 11, "bold"),
            anchor="w",
            wraplength=850
        ).pack(fill=tk.X, pady=(0, 5))

        csv_file_path = os.path.join(folder, "UnformattedDataL2FilePaths.csv")
        info_text = (
            f"The following Level 2 outputs were found within this directory.\n"
            f"Any preselected paths were loaded from: {csv_file_path}\n"
            f"Please select which tests you would like to compare and press OK."
        )
        tk.Label(
            header_frame,
            text=info_text,
            justify=tk.LEFT,
            anchor="w",
            wraplength=850
        ).pack(fill=tk.X)

        # Listbox frame with scrollbars
        list_frame = tk.Frame(win, padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        hsb = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)

        listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            font=("Courier", 10)
        )
        vsb.config(command=listbox.yview)
        hsb.config(command=listbox.xview)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for item in full_files:
            listbox.insert(tk.END, item)

        # Preselect existing paths
        default_selection = len(existing_paths) if existing_paths else len(full_files)
        for i in range(default_selection):
            listbox.selection_set(i)

        # Helper buttons frame
        helper_frame = tk.Frame(win, padx=10, pady=5)
        helper_frame.pack(fill=tk.X)

        def select_all():
            listbox.selection_set(0, tk.END)

        def clear_all():
            listbox.selection_clear(0, tk.END)

        def change_folder():
            new_dir = filedialog.askdirectory(title="Select folder containing Level 2 test outputs", initialdir=folder)
            if new_dir:
                win.destroy()
                run_selection_window(new_dir)

        tk.Button(helper_frame, text="Select All", command=select_all).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(helper_frame, text="Clear All", command=clear_all).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(helper_frame, text="Change Folder...", command=change_folder).pack(side=tk.LEFT, padx=(0, 5))

        # Bottom action buttons
        btn_frame = tk.Frame(win, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        def on_ok():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select at least one test to compare.")
                return
            selected_paths = [listbox.get(i) for i in selected_indices]
            write_saved_l2_paths(folder, selected_paths)
            result['folder'] = folder
            result['paths'] = selected_paths
            win.destroy()

        def on_cancel():
            win.destroy()

        ok_btn = tk.Button(btn_frame, text="OK", width=12, command=on_ok)
        ok_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = tk.Button(btn_frame, text="Cancel", width=12, command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        win.protocol("WM_DELETE_WINDOW", on_cancel)
        win.transient(root)
        win.grab_set()
        root.wait_window(win)

    run_selection_window(current_folder)
    root.destroy()
    return result['folder'], result['paths']
