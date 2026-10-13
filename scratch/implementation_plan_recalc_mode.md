# Plan: GUI file picking in LEMSDataCruncher_L3 + merging pair shading into `main`

## Goal
1. In GUI mode, [LEMSDataCruncher_L3.py](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMSDataCruncher_L3.py) should pick files the same way [LEMS_DataEntry_L3.py](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_DataEntry_L3.py#L548-L609) does.
2. Get the shaded pair plotting (driven by `PairsUnformattedDataL2FilePaths.csv`) into `main` cleanly.

## What the code does now

| | LEMS_DataEntry_L3 (`on_browse`, L548–609) | Cruncher GUI branch (L747–790) |
|---|---|---|
| Asks for | One **folder** (`filedialog.askdirectory`) | A count of tests, then one `fileopenbox` per **data entry form** |
| Finds | Every `*UnFormattedDataL2.csv` under the folder (`os.walk`) | Only the files the user clicks |
| Selection | Multi-select listbox. Paths saved in `UnformattedDataL2FilePaths.csv` are preselected and listed first | None |
| Saves | Writes the selection back to `UnformattedDataL2FilePaths.csv` | Nothing |
| Builds | One L2 group per selected path | Only the per-test lists |

**There is also a bug in GUI mode today.** `list_input_L3`, `list_labels_L3` and `list_input_LP` are only defined in the CLI branch, so in GUI mode steps 20–30 fail with `NameError`. `folder_path` is also guessed from the parent of the first test folder. Doing the file picking the DataEntry_L3 way fixes both problems.

## Proposed changes

### 1. New shared module `LEMS/LEMS_L2FileSelector.py`
This pulls the logic out of `LEMS_DataEntry_L3.on_browse` so both tools use the same code:
- `find_L2_files(folder)`: walks the folder and returns every `*UnFormattedDataL2.csv`. The `_lp` and `_<phase>` files don't match that pattern, so they are skipped automatically.
- `read_saved_selection(folder)` / `write_saved_selection(folder, paths)`: read and write `UnformattedDataL2FilePaths.csv`.
- `order_candidates(saved, found)`: returns saved paths first, then any new ones, plus how many to preselect. This is the same ordering as L582–594.
- `select_L2_files_dialog(folder=None)`: a standalone Tk window with a folder Browse button, a `MULTIPLE` listbox and OK. It returns `(folder, selected_paths)`. The cruncher is a console program, so it needs its own window. It opens a `tk.Tk()`, waits on `mainloop`, then destroys the window.

`LEMS_DataEntry_L3.on_browse` / `on_okay` change to call `find_L2_files`, `read_saved_selection`, `order_candidates` and `write_saved_selection`. Its embedded listbox UI does not change.

### 2. Shared group builder inside the cruncher
Move the per-row body of the CLI loader (L677–720) into a new function, `_build_groups(l2_paths, labels)`. It returns `list_input`, `list_filename`, `list_directory`, `list_testname`, `list_logname`, `list_input_L3`, `list_labels_L3`, `list_input_LP` and `list_groups`.

For each `UnFormattedDataL2.csv` path, `group_dir = dirname(path)` gives:
- per-test inputs, read from `group_dir/DataEntrySheetFilePaths.csv` (used by steps 1–19)
- `list_input_L3`, which is the path itself (steps 20, 23–30)
- `list_input_LP`, which is `group_dir/UnFormattedDataL2_lp.csv` if that file exists (step 21)

The CLI branch calls it after reading `Name,Code,Path` (it converts `…/DataEntrySheetFilePaths.csv` to `…/UnFormattedDataL2.csv` first). The GUI branch calls it with the paths picked in the dialog.

### 3. New GUI branch (replaces L747–790)
```python
folder_path, selected = select_L2_files_dialog()
labels = _labels_from_pairs_or_folder(folder_path, selected)  # Name from Pairs CSV if present, else folder name
(... lists ...) = _build_groups(selected, labels)
write_saved_selection(folder_path, selected)
```
- `folder_path` is now the folder the user chose, so `L3_log.txt`, `PlotSelection.csv`, the Pairs CSV and all L3 outputs end up in the same place as in CLI mode.
- The "Run all LP tests? (y/n)" prompt is only in the CLI branch. GUI mode builds the LP list automatically.

### 4. How this fits with shaded pair plotting
- The Pairs loader (L807–818) runs **after** the mode split and reads `folder_path/PairsUnformattedDataL2FilePaths.csv`. Once `folder_path` is correct, GUI mode gets pair shading for steps 22–28 without any other changes.
- The Pairs CSV `path` column stays as **UnFormattedDataL2.csv**, which is what the GUI picker selects. Optionally, a `DataEntrySheetFilePaths.csv` path could also be accepted and converted to the same folder.
- If a Pairs CSV exists, the dialog preselects its paths in their listed order. That way the per-group steps and the paired plots use the same groups.
- Step 29 bug: it passes `list_input_L3` together with `list_pair_groups`, whose indices refer to the pairs list. Fix it the same way as steps 23–28.

> [!WARNING]
> This conflicts with [scratch/implementation_plan_pairs.md](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/scratch/implementation_plan_pairs.md), which proposed pointing the Pairs `path` at `DataEntrySheetFilePaths.csv`. Using UnFormattedDataL2.csv here keeps it consistent with how DataEntry_L3 and the GUI picker work.

### 5. Getting the feature into `main`
`LEMS-L3-additions` is 25 commits ahead of `main` across 52 files. Besides the plotting work, it also includes large `LEMS_EmissionCalcs.py` changes, scratch data and `.DS_Store` files. The branch's cruncher also depends on those EmissionCalcs changes: `recalculate_timeseries` does not exist on `main`.

The plotting files are safe to move on their own. Each plot function only gained optional `labels=None, pair_groups=None` arguments, and nothing outside the cruncher calls them. `LEMS_FormatData_L3Pairs` and `LEMS_CustomFormatted_L3Pairs` are already on `main`.

**Option A (recommended): a slim feature branch off `main`**
1. `git switch -c lems-l3-pair-shading origin/main`
2. Bring over these files from `LEMS-L3-additions`: `LEMS_PairsPlotHelper.py` and the seven plot modules (`boxplots`, `barcharts`, `scatterplots`, `multiboxplots`, `multibarcharts`, `multiscatterslopt`, `subplotscatterplot`).
3. Add `LEMS_L2FileSelector.py` and the `LEMS_DataEntry_L3` refactor.
4. Port only the cruncher wiring onto `main`'s cruncher: the Pairs loader, label/pair_groups arguments for steps 23–29, the GUI picker and `_build_groups`.
5. Open a PR into `main`. Rebase `LEMS-L3-additions` onto it afterwards, or merge it in later.

**Option B: merge all of `LEMS-L3-additions`**
Do the GUI work on this branch, remove `scratch/*` data and `.DS_Store` from the diff, and open one large PR. It is simpler, but it puts the EmissionCalcs changes in the same review.

## Verification
- **Dry load:** pick a folder that contains the sample groups. Print the per-test count, `list_input_L3`, `list_input_LP`, the labels and the pair groups, then compare them with a CLI run on the same groups.
- Run steps 20, 21, 22, 24 and 26 in GUI mode, with and without the Pairs CSV, and confirm that the shaded plots match the `scratch/L3Pairs*.png` references.
- Run `LEMS_DataEntry_L3`: browse, select, press OK. It should behave the same as before and produce the same `UnformattedDataL2FilePaths.csv`.
- On the `main`-based branch, run the existing (non-pair) plot steps to confirm nothing regressed.

## Open questions
1. **Merge route:** Option A (slim branch) or Option B (whole branch)?
2. **Pairs `path` column:** keep UnFormattedDataL2.csv, which this plan recommends, or switch to DataEntrySheetFilePaths.csv as the scratch plan proposed?
3. **Picker style:** a Tk listbox window (same as DataEntry_L3), or the easygui `diropenbox` + `multchoicebox` the cruncher already imports? Tk matches DataEntry_L3 exactly and keeps the preselection.
4. Should GUI mode keep asking for interactive vs. reprocessing mode on the console (current behaviour), or should that move into the dialog too?
