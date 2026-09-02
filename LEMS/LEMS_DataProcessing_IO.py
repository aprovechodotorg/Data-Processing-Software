# v0.3  Python3

#    Copyright (C) 2022-2026 Aprovecho Research Center
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Contact: sam@aprovecho.org

import csv
import io
import math
import os
import re
import time
import tkinter as tk
from datetime import datetime as dt

import chardet
import numpy as np
import pandas as pd
import xlrd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from openpyxl import load_workbook
from PIL import Image, ImageTk
from uncertainties import ufloat, unumpy

# =====================================================================
# GUI, POPUP, AND NAVIGATION UTILITIES
# =====================================================================


class InfoToolTip:
    """Handles hover-triggered informational popups with optional LaTeX formula rendering."""

    def __init__(self):
        self.hover_popup = None
        self.latex_image = None

    def show_info_popup(
        self, message, anchor_widget, formula=None, align="left"
    ):
        self.hide_info_popup()

        self.hover_popup = tk.Toplevel(anchor_widget)
        self.hover_popup.wm_overrideredirect(True)
        self.hover_popup.attributes("-topmost", True)

        popup_width = 270
        y = anchor_widget.winfo_rooty() + 20

        if align == "right":
            x = anchor_widget.winfo_rootx() + 20
        else:
            x = anchor_widget.winfo_rootx() - popup_width

        self.hover_popup.geometry(f"+{x}+{y}")

        frame = tk.Frame(
            self.hover_popup,
            bg="lightyellow",
            padx=5,
            pady=5,
            bd=1,
            relief="solid",
        )
        frame.pack()

        label = tk.Label(
            frame,
            text=message,
            bg="lightyellow",
            justify="left",
            wraplength=250,
        )
        label.pack()

        if formula:
            image = self.create_latex_image(formula)
            self.latex_image = ImageTk.PhotoImage(image)
            img_label = tk.Label(
                frame, image=self.latex_image, bg="lightyellow"
            )
            img_label.pack()

    def hide_info_popup(self):
        if hasattr(self, "hover_popup") and self.hover_popup is not None:
            self.hover_popup.destroy()
            self.hover_popup = None

    def create_latex_image(self, formula):
        fig = Figure(figsize=(0.01, 0.01))
        FigureCanvasAgg(fig)

        ax = fig.add_subplot(111)
        fig.patch.set_visible(False)
        ax.axis("off")

        ax.text(0, 0, f"${formula}$", fontsize=14)

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            bbox_inches="tight",
            pad_inches=0.2,
            transparent=True,
        )
        buf.seek(0)
        return Image.open(buf)


def highlight_search_text(
    search_text, text_widgets, tag_name="highlight", bg_color="yellow"
):
    """Highlights matches for search_text across a single or collection of Tkinter Text widgets."""
    if not isinstance(text_widgets, (list, tuple)):
        text_widgets = [text_widgets]

    for widget in text_widgets:
        widget.tag_remove(tag_name, "1.0", tk.END)

    if not search_text:
        return

    for widget in text_widgets:
        start_pos = "1.0"
        while True:
            start_pos = widget.search(search_text, start_pos, tk.END)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(search_text)}c"
            widget.tag_add(tag_name, start_pos, end_pos)
            start_pos = end_pos

        widget.tag_configure(tag_name, background=bg_color)


def read_simple_csv(filepath):
    """Reads a CSV file into a list of rows."""
    data = []
    with open(filepath, "r", newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data


def move_next_entry(entries_list, event):
    """Focuses the next entry widget in the given list."""
    current_entry = event.widget
    try:
        current_index = entries_list.index(current_entry)
        if current_index + 1 < len(entries_list):
            entries_list[current_index + 1].focus_set()
    except (ValueError, IndexError):
        pass


def move_prev_entry(entries_list, event):
    """Focuses the previous entry widget in the given list."""
    current_entry = event.widget
    try:
        current_index = entries_list.index(current_entry)
        if current_index > 0:
            entries_list[current_index - 1].focus_set()
    except (ValueError, IndexError):
        pass


# =====================================================================
# TIME SERIES, FILE LOADING & PARSING FUNCTIONS
# =====================================================================


def fill_controller_reboot_data(Inputpath, Outputpath):
    metadata_lines = []
    with open(Inputpath, "r") as f:
        for line in f:
            if not line.startswith("time"):
                metadata_lines.append(line.strip())
            else:
                break

    data = pd.read_csv(Inputpath, skiprows=len(metadata_lines))
    data["time"] = pd.to_datetime(
        data["time"], format="%Y%m%d %H:%M:%S", errors="coerce"
    )
    data = data.dropna(subset=["time"]).reset_index(drop=True)
    data = data.drop_duplicates(subset="time")
    data = data.set_index("time")
    data_continuous = data.resample("s").asfreq()
    data_continuous = data_continuous.bfill().reset_index()
    data_continuous["time"] = data_continuous["time"].dt.strftime(
        "%Y%m%d %H:%M:%S"
    )

    with open(Outputpath, "w") as f:
        for meta in metadata_lines:
            f.write(f"{meta}\n")
        data_continuous.to_csv(f, index=False, header=True)

    print("Continuous timestamp data created successfully.")


def load_inputs_from_spreadsheet(Inputpath):
    names = []
    units = {}
    val = {}
    unc = {}

    name = "variable_name"
    names.append(name)
    units[name] = "units"
    val[name] = "value"
    unc[name] = "uncertainty"

    wb = load_workbook(filename=Inputpath, data_only=True)
    sheet = wb.active

    grabvals = 0
    colnum = 0
    units_colnum = 1

    for col in sheet.iter_cols():
        colnum = colnum + 1
        rownum = 0
        for cell in col:
            rownum = rownum + 1
            if grabvals == 1:
                if cell.value is None:
                    grabvals = 0
                else:
                    name = cell.value
                    names.append(name)
                    units[name] = sheet.cell(
                        row=rownum, column=units_colnum
                    ).value
                    val[name] = sheet.cell(row=rownum, column=colnum - 1).value
            if cell.value == "label":
                grabvals = 1
                for n in range(colnum, 0, -1):
                    nextcell = sheet.cell(row=rownum, column=n).value
                    if nextcell in ["Units", "units"]:
                        units_colnum = n
                        break

    return names, units, val, unc


def detect_encoding(Inputpath):
    with open(Inputpath, "rb") as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result["encoding"]


def load_constant_inputs(Inputpath):
    names = []
    units = {}
    val = {}
    unc = {}
    uval = {}

    encoding = detect_encoding(Inputpath)
    print(f"Detected encoding: {encoding}")

    stuff = []
    with open(Inputpath, "r", encoding=encoding) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    for row in stuff:
        # Skipping empty rows

        if len(row) < 2:
            continue





        name = row[0]
        units[name] = row[1]
        val[name] = row[2]
        try:
            unc[name] = row[3]
        except IndexError:
            unc[name] = ""
        try:
            float(val[name])
            try:
                float(unc[name])
                uval[name] = ufloat(float(val[name]), float(unc[name]))
            except ValueError:
                uval[name] = ufloat(float(val[name]), 0)
        except ValueError:
            uval[name] = row[2]
        names.append(name)

    return names, units, val, unc, uval


def load_timeseries_with_header(Inputpath, logpath):
    units = {}
    A = {}
    B = {}
    C = {}
    D = {}
    const = {}
    data = {}
    logs = []

    header_peek = []
    with open(Inputpath, "r") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            header_peek.append(row)
            if i > 100:
                break

    version = ""
    namesrow = unitsrow = Arow = Brow = Crow = Drow = None

    for n, row in enumerate(header_peek):
        if not row:
            continue
        if row[0] in ["#A:", "# 0"]:
            Arow = n
        if row[0] == "#B:":
            Brow = n
        if row[0] == "#C:":
            Crow = n
        if row[0] == "#D:":
            Drow = n
        if row[0] == "#units:":
            unitsrow = n
        if row[0] in ["time", "seconds"]:
            namesrow = n
        if "#version" in row[0]:
            version = row[0]

    names = header_peek[namesrow]
    num_columns = len(names)

    for name in names:
        data[name] = []

    for n, name in enumerate(names):
        if unitsrow is not None and n < len(header_peek[unitsrow]):
            units[name] = header_peek[unitsrow][n]
        else:
            units[name] = "N/A"

        for mapping, row_idx in [(A, Arow), (B, Brow), (C, Crow), (D, Drow)]:
            if row_idx is not None and n < len(header_peek[row_idx]):
                v = header_peek[row_idx][n]
                try:
                    mapping[name] = float(v)
                except (ValueError, TypeError):
                    mapping[name] = v
            else:
                mapping[name] = None

        if name in C and isinstance(C[name], str):
            const[C[name]] = D.get(name)

    with open(Inputpath, "r") as f:
        reader = csv.reader(f)
        for _ in range(namesrow + 1):
            next(reader)

        line_count = namesrow + 1
        for row in reader:
            line_count += 1
            if len(row) != num_columns or not row[0].strip() or row.count("") > 0:
                timestamp = row[0] if row else "Unknown"
                logs.append(
                    f"Line {line_count}: Skipped garbled data at {timestamp}"
                )
                continue

            for n, name in enumerate(names):
                v = row[n]
                try:
                    data[name].append(float(v))
                except ValueError:
                    data[name].append(v)

    if version != "":
        try:
            head, ver = version.split(" ")
            version = ver
        except ValueError:
            pass

    write_logfile(logpath, logs)
    return names, units, data, A, B, C, D, const, version


def load_header(Inputpath):
    names = []
    units = {}
    A = {}
    B = {}
    C = {}
    D = {}
    const = {}

    stuff = []
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    Arow = Brow = Crow = Drow = unitsrow = namesrow = None
    for n, row in enumerate(stuff[:100]):
        if row[0] == "#A:":
            Arow = n
        if row[0] == "#B:":
            Brow = n
        if row[0] == "#C:":
            Crow = n
        if row[0] == "#D:":
            Drow = n
        if row[0] == "#units:":
            unitsrow = n
        if row[0] == "time":
            namesrow = n

    names = stuff[namesrow]
    for n, name in enumerate(names):
        units[name] = stuff[unitsrow][n]
        try:
            A[name] = float(stuff[Arow][n])
        except (ValueError, TypeError):
            A[name] = stuff[Arow][n]
        try:
            B[name] = float(stuff[Brow][n])
        except (ValueError, TypeError):
            B[name] = stuff[Brow][n]
        try:
            C[name] = float(stuff[Crow][n])
        except (ValueError, TypeError):
            C[name] = stuff[Crow][n]
        try:
            D[name] = float(stuff[Drow][n])
        except (ValueError, TypeError):
            D[name] = stuff[Drow][n]

        if isinstance(C[name], str):
            const[C[name]] = D[name]

    return names, units, A, B, C, D, const


def load_timeseries(Inputpath):
    data = {}
    encoding = detect_encoding(Inputpath)
    print(f"Detected encoding: {encoding}")

    stuff = []
    with open(Inputpath, "r", encoding=encoding) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    names = stuff[0]
    units = {}
    for n, name in enumerate(names):
        units[name] = stuff[1][n]
        data[name] = [x[n] for x in stuff[2:]]
        for m, val in enumerate(data[name]):
            try:
                data[name][m] = float(data[name][m])
            except ValueError:
                pass

    return names, units, data


def load_L2_constant_inputs(Inputpath):
    names = []
    units = {}
    val = {}
    data = {}
    average = {}
    N = {}
    stdev = {}
    Interval = {}
    High = {}
    Low = {}
    COV = {}
    CI = {}

    encoding = detect_encoding(Inputpath)
    print(f"Detected encoding: {encoding}")

    stuff = []
    with open(Inputpath, "r", encoding=encoding) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    averagerow = Nrow = stdevrow = intervalrow = highrow = lowrow = COVrow = (
        CIrow
    ) = None
    for i, value in enumerate(stuff[0]):
        if stuff[0][i] == "average":
            averagerow = i
        elif stuff[0][i] == "N":
            Nrow = i
        elif stuff[0][i] == "stdev":
            stdevrow = i
        elif stuff[0][i] in ["Interval", "interval"]:
            intervalrow = i
        elif stuff[0][i] in ["High Tier Estimate", "high_tier"]:
            highrow = i
        elif stuff[0][i] in ["Low Tier Estimate", "low_tier"]:
            lowrow = i
        elif stuff[0][i] == "COV":
            COVrow = i
        elif stuff[0][i] == "CI":
            CIrow = i

    for row in stuff:
        names.append(row[0])

    for n, name in enumerate(names):
        units[name] = stuff[n][1] if len(stuff[n]) > 1 else ""
        average[name] = (
            stuff[n][averagerow] if averagerow and len(stuff[n]) > averagerow else ""
        )
        N[name] = stuff[n][Nrow] if Nrow and len(stuff[n]) > Nrow else ""
        stdev[name] = (
            stuff[n][stdevrow] if stdevrow and len(stuff[n]) > stdevrow else ""
        )
        Interval[name] = (
            stuff[n][intervalrow]
            if intervalrow and len(stuff[n]) > intervalrow
            else ""
        )
        High[name] = (
            stuff[n][highrow] if highrow and len(stuff[n]) > highrow else ""
        )
        Low[name] = stuff[n][lowrow] if lowrow and len(stuff[n]) > lowrow else ""
        COV[name] = stuff[n][COVrow] if COVrow and len(stuff[n]) > COVrow else ""
        CI[name] = stuff[n][CIrow] if CIrow and len(stuff[n]) > CIrow else ""
        val[name] = (
            stuff[n][2:averagerow]
            if averagerow and len(stuff[n]) >= averagerow
            else [""]
        )

    data["average"] = average
    data["N"] = N
    data["stdev"] = stdev
    data["Interval"] = Interval
    data["High Tier"] = High
    data["Low Tier"] = Low
    data["COV"] = COV
    data["CI"] = CI

    return names, units, val, data


# =====================================================================
# FILE WRITING & OUTPUT FUNCTIONS
# =====================================================================


def write_constant_outputs(Outputpath, Names, Units, Val, Unc, Uval):
    for name in Names:
        try:
            Val[name]
        except KeyError:
            try:
                Val[name] = Uval[name].n
            except AttributeError:
                Val[name] = Uval[name]
        try:
            Unc[name]
        except KeyError:
            try:
                if name in Unc and name in Uval:
                    Unc[name] = Uval[name].s
            except AttributeError:
                Unc[name] = ""

    output = []
    for name in Names:
        row = [name, Units.get(name, ""), Val.get(name, ""), Unc.get(name, "")]
        output.append(row)

    with open(Outputpath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)


def write_timeseries_with_header(Outputpath, Names, Units, Data, A, B, C, D):
    Arow = []
    Brow = []
    Crow = []
    Drow = []
    Unitsrow = []
    for name in Names:
        Arow.append(A[name])
        Brow.append(B[name])
        Crow.append(C[name])
        Drow.append(D[name])
        Unitsrow.append(Units[name])

    output = [Arow, Brow, Crow, Drow, Unitsrow, Names]
    for n, val in enumerate(Data["time"]):
        row = [Data[name][n] for name in Names]
        output.append(row)

    with open(Outputpath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)


def write_header(Outputpath, Names, Units, A, B, C, D):
    Arow = []
    Brow = []
    Crow = []
    Drow = []
    Unitsrow = []
    for name in Names:
        Arow.append(A[name])
        Brow.append(B[name])
        Crow.append(C[name])
        Drow.append(D[name])
        Unitsrow.append(Units[name])

    output = [Arow, Brow, Crow, Drow, Unitsrow, Names]
    with open(Outputpath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)


def write_timeseries(Outputpath, Names, Units, Data):
    Unitsrow = [Units[name] for name in Names]
    output = [Names, Unitsrow]
    for n, val in enumerate(Data["time"]):
        row = [Data[name][n] for name in Names]
        output.append(row)

    with open(Outputpath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)


def write_timeseries_with_uncertainty(Outputpath, Names, Units, Data):
    timestampstring = dt.now().strftime("%H:%M:%S")
    print("start write_timeseries_with_uncertainty " + timestampstring)
    newnames = []
    regex1 = re.compile("_smooth")
    regex2 = re.compile("_Ave")

    for name in Names:
        if re.search(regex1, name) or re.search(regex2, name):
            newnames.extend([name, name + "_uc"])
            Units[name + "_uc"] = Units[name]
            try:
                Data[name + "_uc"] = [""] * len(Data[name])
                Data[name] = unumpy.nominal_values(Data[name])
            except Exception:
                Data[name + "_uc"] = [""] * len(Data[name])
        else:
            newnames.extend([name, name + "_uc"])
            Units[name + "_uc"] = Units[name]
            try:
                Data[name + "_uc"] = unumpy.std_devs(Data[name])
                Data[name] = unumpy.nominal_values(Data[name])
            except Exception:
                Data[name + "_uc"] = [""] * len(Data[name])

    write_timeseries(Outputpath, newnames, Units, Data)


def write_timeseries_without_uncertainty(Outputpath, Names, Units, Data):
    timestampstring = dt.now().strftime("%H:%M:%S")
    print("start write_timeseries_without_uncertainty " + timestampstring)

    if os.path.isfile(Outputpath):
        os.remove(Outputpath)

    Namesrow = [name for name in Names]
    Unitsrow = [Units[name] for name in Names]
    output = [Namesrow, Unitsrow]

    for n in range(len(Data["time"])):
        row = []
        for name in Names:
            try:
                row.append(Data[name][n].n)
            except AttributeError:
                row.append(Data[name][n])
        output.append(row)
        if n % 1000 == 0 or n == len(Data["time"]) - 1:
            with open(Outputpath, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                for outrow in output:
                    writer.writerow(outrow)
            output = []


def write_logfile(Logpath, Logs):
    with open(Logpath, "a") as logfile:
        for log in Logs:
            logfile.write("\n" + log)