# Plan: `PairsUnformattedDataL2FilePaths.csv` replaces the two older config CSVs

## Goal
In [LEMSDataCruncher_L3.py](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMSDataCruncher_L3.py), `PairsUnformattedDataL2FilePaths.csv` becomes the **one config file** for the whole run. It replaces:
- `UnformattedDataL2FilePaths_DataEntrySheetFilePaths.csv`: group list, used for steps 1–20, 23–30
- `UnformattedDataL2FilePaths_lp.csv`: LP list, used for step 21 (and step 31 through `FormattedDataL3_lp.csv`)

If the file has no `d…/…` pair rows, the run works the same way it does now with the DataEntrySheet CSV (plain L3, no pair shading).

## Confirmed decisions
- `path` points to the group's **DataEntrySheetFilePaths.csv**. `UnFormattedDataL2.csv` and `UnFormattedDataL2_lp.csv` are found in the same folder.
- The LP file is called **`UnFormattedDataL2_lp.csv`** (written by step 18).
- Support for the old CSVs is **removed completely**. If the Pairs CSV is missing, print a warning and leave the lists empty.
- Labels use **Name**, then test_code, then the folder name.

## What the code does now
| Item | Today |
|---|---|
| Group loader (L657–725) | Reads `Name,Code,Path`. `Path` points to a group's `DataEntrySheetFilePaths.csv`. Builds per-test lists, `list_input_L3` (`<dir>/UnFormattedDataL2.csv`), `list_labels_L3` and `list_groups` |
| LP loader (L727–745) | Reads a single column of LP paths and asks "Run all LP tests? (y/n)" |
| Pairs loader (L807–818, [load_pairs_csv](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_PairsPlotHelper.py#L9-L84)) | Reads `Name,test_code,data_key,path`. `path` points to `UnFormattedDataL2.csv` |
| [LEMS_FormatData_L3Pairs](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_FormatData_L3Pairs.py#L20) | Re-reads the pairs CSV and loads `path` directly as the UnFormattedDataL2 file |

## Proposed design

### 1. CSV format (proposed)
```
Name,test_code,data_key,path
Stove A baseline,1B,1B,C:\...\GroupA\DataEntrySheetFilePaths.csv
Stove A retrofit,1R2,1R2,C:\...\GroupB\DataEntrySheetFilePaths.csv
Stove A pair,,d1B/1R2,
```
For each row that has a `path`, the folder `group_dir = dirname(path)` gives:
- per-test inputs → read from `path` (the DataEntrySheetFilePaths.csv), used by steps 1–19
- `group_dir/UnFormattedDataL2.csv`, added to `list_input_L3`, used by steps 20, 23–30
- `group_dir/UnFormattedDataL2_lp.csv`, added to `list_input_LP`, used by step 21

Rows without a `path` that have a `d…/…` key become `list_pair_groups`, which steps 22–28 and 32 use.

### 2. New single loader
Add `load_pairs_config(csv_path)` to `LEMS_PairsPlotHelper.py`. It returns one structure containing `groups`, `list_input`/per-test lists, `list_input_L3`, `list_labels_L3`, `list_input_LP`, and `pair_groups`. This replaces the three loader blocks in the CLI branch.

### 3. Changes to downstream steps
- **Step 21:** uses `list_input_LP`, which is now derived from the pairs CSV.
- **Step 22 / `LEMS_FormatData_L3Pairs`:** accepts a `path` that is either a DataEntrySheet CSV or an UnFormattedDataL2.csv, and resolves it to UnFormattedDataL2.
- **Steps 23–28:** keep the existing "pairs if present, otherwise plain L3" switch. Since there is only one list now, the inputs/labels are the same either way; only `pair_groups` changes.
- **Step 29:** fix an existing bug. It passes `list_input_L3` together with `list_pair_groups`, but those indices refer to a different list.
- **Old CSVs:** delete the loader blocks for the DataEntrySheet CSV and the LP CSV (L657–745), the "Run all LP tests? (y/n)" prompt, and the separate pairs block (L807–818). Rename step 21 to "LP - compare all outputs".

### 4. Edge cases
- The same group listed in several rows (e.g. used in two pairs): dedupe per-test reprocessing by path so steps 1–19 don't run twice.
- `UnFormattedDataL2_lp.csv` missing: warn and skip that group in step 21.
- `data_key.startswith('d')` currently treats any key starting with `d` as a pair. Tighten this to require a `/`.

## Open questions
These are not decided yet. None of them are implemented unless you approve them.
1. **Step 29 bug:** should it use the pairs inputs/labels with `pair_groups`, the way steps 23–28 do? (Recommended, since there is only one list now.)
2. **Pairs LP output:** should step 22 also write `PairsFormattedDataL3_lp.csv` from the `_lp` files?
3. **Pair detection:** should a `data_key` only count as a pair when it contains `/`? Today `startswith('d')` is enough, both here and in `LEMS_FormatData_L3Pairs`.
4. **Duplicate groups:** if one group appears in several rows, should steps 1–19 skip the repeats? Should steps 20/21 and the plots still show the group once per row?

## Verification
- Dry-load a sample pairs CSV with and without `d` rows. Print the per-test count, the L3/LP lists and the pair groups.
- Run steps 20, 21, 22 and 24 on an existing dataset and diff the outputs against the current files.
