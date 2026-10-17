# LEMS_BlackCarbon Documentation

> **Branch:** `black-carbon-second-window`  
> **Source Module:** `LEMS/LEMS_BlackCarbon.py`  
> **HTML Version:** [`LEMS_BlackCarbon_Documentation.html`](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/Documentation/LEMS_BlackCarbon_Documentation.html)

---

## 1. Executive Summary & Purpose

In this branch, the **Black Carbon (BC)** data entry and calculation pipeline is fully decoupled from the **Gravimetric (Grav)** pipeline.

### Why Decouple BC from Gravimetric?
- **Three-Line LEMS (3 LPM without Flow Sensor)**: In physical sampling configurations where a dedicated 3 L/min line lacks a digital inline sensor, users can manually specify a 3.0 L/min flow rate independently of the gravimetric digital sensor reading.
- **High-Flow Lines (16.7 LPM)**: Cyclone or high-flow stack lines require flow rates and filter identification distinct from the primary gravimetric filter.
- **Different Physical Filters**: The gravimetric filter (e.g. filter `1`) and the black carbon filter (e.g. filter `201`) can be distinct physical filters during the same phase.

---

## 2. Key User Capabilities

1. **Specify Different Flow Rate (`Qsample_<phase>`)**:
   - The user can enter a custom flow rate (e.g. `3.0` L/min or `16.7` L/min) in the dialog.
   - This overrides the digital flow rate recorded in `GravOutputs.csv`.
2. **Specify Different Filter Number (`filterID_<phase>`)**:
   - The user can specify any filter ID in the dialog.
   - This overrides the gravimetric filter specified in `GravInputs.csv`.
   - The image detection engine looks for `<testname>_<filterID>.jpeg` (or `.jpg`/`.png`) using this filter ID.
3. **Dedicated Authoritative File**:
   - All settings are saved to `<testname>_BCInputs.csv`. On subsequent runs, this file is loaded directly, preserving user inputs.

---

## 3. Workflow Diagram

```
+--------------------------------------------------------------+
|               Launch Black Carbon Data Entry                 |
|      (via GUI 'Black Carbon' button or standalone call)      |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|            Step 1 & 2: Early Fallback Loading                |
|  - Load GravInputs.csv (filterID_* fallback)                 |
|  - Load GravOutputs.csv (Qsample_* & phase_time_* fallback)  |
|  - Load existing BCInputs.csv (takes priority if present)    |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|            Step 3 & 4: Phase Discovery & Prepopulation       |
|  - Detect active phases from filterID_* keys                 |
|  - Skip any blank phases                                     |
|  - Pre-populate: BCInputs -> GravInputs/GravOutputs fallback |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|           Step 6 & 7: Interactive 'Filter Inputs' Modal      |
|  - easygui.multenterbox grouped by active phase:             |
|      filterID_<phase>     <- User can enter custom filter    |
|      phase_time_<phase>   <- User can enter phase time       |
|      Qsample_<phase>      <- User can enter custom flow rate |
|      filterRadius_<filter><- User can adjust deposit radius  |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|           Step 8 & 9: Save Authoritative BCInputs.csv        |
|  - Re-derive active filters from edited filterID_<phase>     |
|  - Assign default 1.95 mm radius for new filters             |
|  - Save complete set to <testname>_BCInputs.csv              |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|           Step 10: Image Analysis & Decoupled Calcs          |
|  - Find <testname>_<filterID>.jpeg image                     |
|  - Detect 4 QR codes & 10 gray calibration gradient bars     |
|  - Sample filter deposit circle                              |
|  - Rate filter against BC_TOT calibration curve              |
|  - Calculate BC metrics using bcval Qsample & phase_time:    |
|      * BCloading_<filter>_<phase>       [ug/cm^2]            |
|      * BCconcentration_<filter>_<phase> [cm^3/ug]            |
|      * BCmass_<filter>_<phase>          [ug]                 |
|      * BCemissionrate_<filter>_<phase>  [ug/min]             |
|  - Write outputs to <testname>_BCOutputs.csv                 |
|  - Save debug overlay <testname>_<filterID>_Debug.jpg        |
+--------------------------------------------------------------+
```

---

## 4. Precedence & Fallback Rules

| Parameter | 1st Priority (Authoritative) | 2nd Priority (Fallback) | Default | Unit |
| :--- | :--- | :--- | :--- | :--- |
| `filterID_<phase>` | `BCInputs.csv` | `GravInputs.csv` (`filterID_<phase>`) | `""` | `text` |
| `phase_time_<phase>` | `BCInputs.csv` | `GravOutputs.csv` (`phase_time_<phase>`) | `""` | `min` |
| `Qsample_<phase>` | `BCInputs.csv` | `GravOutputs.csv` (`Qsample_<phase>`) | `""` | `l/min` |
| `filterRadius_<filter>` | `BCInputs.csv` | — | `1.95` | `mm` |

---

## 5. Mathematical Calculation Engine

In Step 10, calculations are decoupled from `gravovals`:

```python
exposedTime = bcval['phase_time_' + phases[filter]]
airFlowRate = bcval['Qsample_' + phases[filter]]
bccCalcs = computeBCC(filterRadius, bcLoading, exposedTime, airFlowRate)
```

The resulting metrics are saved to `<testname>_BCOutputs.csv`:
- `BCloading_<filter>_<phase>`: Deposit loading density ($\mu\text{g/cm}^2$).
- `BCconcentration_<filter>_<phase>`: Volumetric exhaust concentration ($\mu\text{g/m}^3$).
- `BCmass_<filter>_<phase>`: Total mass emitted ($\mu\text{g}$).
- `BCemissionrate_<filter>_<phase>`: Rate of emission ($\mu\text{g/min}$).

---

## 6. File Reference

- **Implementation**: [`Data-Processing-Software/LEMS/LEMS_BlackCarbon.py`](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_BlackCarbon.py)
- **GUI Trigger (L1)**: [`Data-Processing-Software/LEMS/LEMS_DataEntry_L1.py`](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_DataEntry_L1.py#L2464)
- **GUI Trigger (L2)**: [`Data-Processing-Software/LEMS/LEMS_DataEntry_L2.py`](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/LEMS_DataEntry_L2.py#L830)
- **Interactive HTML Documentation**: [`Data-Processing-Software/LEMS/Documentation/LEMS_BlackCarbon_Documentation.html`](file:///Users/user/Documents/UCET%20software/Data-Processing-Software/LEMS/Documentation/LEMS_BlackCarbon_Documentation.html)
