import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from PEMS_SubtractBkg import PEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_Plotter1 import PEMS_Plotter
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PIL import Image, ImageTk
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import pandas as pd
import threading
import traceback
import csv

#For pyinstaller:
#C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS>pyinstaller --onefile -p C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS --icon=C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS\ARC-Logo.ico LEMS_DataEntry_L1.py

class LEMSDataInput(tk.Frame):
    def __init__(self, root): #Configurar ventana
        tk.Frame.__init__(self, root)

        #barra de desplazamiento vertical
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")

        # barra de desplazamiento horizontal
        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.pack(side="bottom", fill="x")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((8, 8), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)


        #crear sección de información de prueba
        self.test_info = TestInfoFrame(self.frame, "Información de la Prueba")
        self.test_info.grid(row=1, column=0, columnspan=2, padx=(0, 270), pady=(100, 0))

        #agregar instrucciones
        instructions = f"*Por favor seleccione una carpeta para almacenar sus entradas.\n" \
                       f"*La carpeta debe estar nombrada con el nombre de la prueba y contener datos brutos de LEMS (carpeta etiquetada como nombrecarpeta_RawData.csv) si se usa.\n" \
                       f"*Para ingresar valores para el carbón creado por estufas de leña, ingrese la información como un segundo o tercer combustible en Combustible\n" \
                       f"*con un cfrac db mayor que 0.75. Luego ingrese los pesos de carbón como masa de combustible con la masa inicial siendo 0 si la estufa no tenía carbón al inicio.\n" \
                       f"*Los valores predeterminados para el carbón creado en una estufa de leña son:\n" \
                       f"   mc (contenido de humedad): 0%\n" \
                       f"   valor calorífico superior: 32500 kJ/kg\n" \
                       f"   cfrac db (fracción de carbono en base seca): 0.9\n" \
                       f"*Para la temperatura máxima del agua, ingrese la temperatura máxima del agua.\n" \
                       f"*Para la temperatura final del agua, ingrese la temperatura del agua al final de la fase (al finalizar el apagado para pruebas ISO).\n" \
                       f"*Por favor ingrese todos los tiempos como yyyymmdd HH:MM:SS o HH:MM:SS y ingrese todos los tiempos en el mismo formato."

        self.instructions_frame = tk.Text(self.frame, wrap="word", height=16, width=100)
        self.instructions_frame.insert(tk.END, instructions)
        self.instructions_frame.grid(row=1, column=1, columnspan=4, padx=(10, 0), pady=(10, 0))
        self.instructions_frame.config(state="disabled")

        #crear sección de información del entorno
        self.enviro_info = EnvironmentInfoFrame(self.frame, "Condiciones de la Prueba")
        self.enviro_info.grid(row=2, column=2, columnspan=2, pady=(10, 140), padx=(0, 40))

        #crear sección de comentarios
        self.comments = CommentsFrame(self.frame, "Comentarios")
        self.comments.grid(row=2, column=3, columnspan=3, pady=(10, 0), padx=(0, 70))

        # crear sección de información del combustible
        self.fuel_info = FuelInfoFrame(self.frame, "Información del Combustible")
        self.fuel_info.grid(row=2, column=0, columnspan=2, padx=(10, 0))

        # crear sección de inicio de alta potencia
        self.hpstart_info = HPstartInfoFrame(self.frame, "Inicio de Alta Potencia")
        self.hpstart_info.grid(row=3, column=0, columnspan=2)
        self.hpend_info = HPendInfoFrame(self.frame, "Fin de Alta Potencia")
        self.hpend_info.grid(row=3, column=2, columnspan=2)

        # crear sección de inicio de potencia media
        self.mpstart_info = MPstartInfoFrame(self.frame, "Inicio de Media Potencia")
        self.mpstart_info.grid(row=3, column=4, columnspan=2)
        self.mpend_info = MPendInfoFrame(self.frame, "Fin de Media Potencia")
        self.mpend_info.grid(row=3, column=6, columnspan=2)

        # crear sección de inicio de baja potencia
        self.lpstart_info = LPstartInfoFrame(self.frame, "Inicio de Baja Potencia")
        self.lpstart_info.grid(row=3, column=8, columnspan=2)
        self.lpend_info = LPendInfoFrame(self.frame, "Fin de Baja Potencia")
        self.lpend_info.grid(row=3, column=10, columnspan=2)

        # crear niveles de ponderación de rendimiento
        self.weight_info = WeightPerformanceFrame(self.frame, "Ponderación para Niveles de Rendimiento Voluntarios")
        self.weight_info.grid(row=4, column=0, columnspan=2, pady=(10, 0), padx=(0, 170))

        # Entrada de ruta de archivo
        tk.Label(self.frame, text="   Seleccionar Carpeta:   ").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var, width=55)
        self.folder_path.grid(row=0, column=1, padx=(10, 50))

        #crear un botón para navegar por las carpetas en la computadora
        browse_button = tk.Button(self.frame, text="  Buscar  ", command=self.on_browse)
        browse_button.grid(row=0, column=2, padx=(0, 300))

        # botón interactivo
        ok_button = tk.Button(self.frame, text="   Ejecutar por primera vez   ", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=6, column=0, padx=(60, 0), pady=10)

        # botón no interactivo
        nonint_button = tk.Button(self.frame, text="   Ejecutar con entradas anteriores   ", command=self.on_nonint)
        nonint_button.anchor()
        nonint_button.grid(row=6, column=1, padx=(0, 60))

        # Vincular el evento MouseWheel a la función onCanvasMouseWheel
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

    def onCanvasMouseWheel(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_nonint(self):  # Cuando se presiona el botón "Ejecutar con entradas anteriores"
        self.inputmethod = '2'
        # para cada marco, verificar entradas
        float_errors = []
        blank_errors = []
        range_errors = []
        value_errors = []
        format_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.comments.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors, range_errors = self.enviro_info.check_input_validity(float_errors, blank_errors,
                                                                                         range_errors)
        float_errors, blank_errors, range_errors = self.fuel_info.check_input_validity(float_errors, blank_errors,
                                                                                       range_errors)
        float_errors, blank_errors, value_errors, format_errors = self.hpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.hpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.mpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.mpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.lpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.lpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors = self.weight_info.check_input_validity(float_errors, blank_errors)

        message = ''
        if len(float_errors) != 0:
            floatmessage = 'Las siguientes variables requieren una entrada numérica:'
            for name in float_errors:
                floatmessage = floatmessage + ' ' + name

            message = message + floatmessage + '\n'

        if len(blank_errors) != 0:
            blankmessage = 'Las siguientes variables se dejaron en blanco pero requieren una entrada:'
            for name in blank_errors:
                blankmessage = blankmessage + ' ' + name

            message = message + blankmessage + '\n'

        if len(range_errors) != 0:
            rangemessage = 'Las siguientes variables están fuera del rango de valores esperado:'
            for name in range_errors:
                rangemessage = rangemessage + ' ' + name

            message = message + rangemessage + '\n'

        if len(value_errors) != 0:
            valuemessage = 'Las siguientes variables tienen una masa inicial que es menor que la masa final:'
            for name in value_errors:
                valuemessage = valuemessage + ' ' + name

            message = message + valuemessage + '\n'

        if len(format_errors) != 0:
            formatmessage = 'Las siguientes tienen un formato incorrecto para la hora o no coinciden ' \
                            'con el formato de hora ingresado en otras áreas \n Los formatos de hora aceptados son yyyymmdd HH:MM:SS o HH:MM:SS:'
            for name in format_errors:
                formatmessage = formatmessage + ' ' + name

            message = message + formatmessage + '\n'

        if message != '':
            # Error
            messagebox.showerror("Error", message)
        else:
            self.names = []
            self.units = {}
            self.data = {}
            self.unc = {}
            self.uval = {}

            name = 'nombre_variable'
            self.names.append(name)
            self.units[name] = 'unidades'
            self.data[name] = 'valor'
            self.unc[name] = 'incertidumbre'
            self.uval[name] = ''

            self.testdata = self.test_info.get_data()
            for name in self.testdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.testdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.commentsdata = self.comments.get_data()
            for n, name in enumerate(self.commentsdata):
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.commentsdata[name].get("1.0", "end").strip()
                self.unc[name] = ''
                self.uval[name] = ''

            self.envirodata = self.enviro_info.get_data()
            self.envirounits = self.enviro_info.get_units()
            for name in self.envirodata:
                self.names.append(name)
                self.units[name] = self.envirounits[name].get()
                self.data[name] = self.envirodata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.fueldata = self.fuel_info.get_data()
            self.fuelunits = self.fuel_info.get_units()
            for name in self.fueldata:
                self.names.append(name)
                self.units[name] = self.fuelunits[name].get()
                self.data[name] = self.fueldata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpstartdata = self.hpstart_info.get_data()
            self.hpstartunits = self.hpstart_info.get_units()
            for name in self.hpstartdata:
                self.names.append(name)
                self.units[name] = self.hpstartunits[name].get()
                self.data[name] = self.hpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpenddata = self.hpend_info.get_data()
            self.hpendunits = self.hpend_info.get_units()
            for name in self.hpenddata:
                self.names.append(name)
                self.units[name] = self.hpendunits[name].get()
                self.data[name] = self.hpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpstartdata = self.mpstart_info.get_data()
            self.mpstartunits = self.mpstart_info.get_units()
            for name in self.mpstartdata:
                self.names.append(name)
                self.units[name] = self.mpstartunits[name].get()
                self.data[name] = self.mpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpenddata = self.mpend_info.get_data()
            self.mpendunits = self.mpend_info.get_units()
            for name in self.mpenddata:
                self.names.append(name)
                self.units[name] = self.mpendunits[name].get()
                self.data[name] = self.mpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpstartdata = self.lpstart_info.get_data()
            self.lpstartunits = self.lpstart_info.get_units()
            for name in self.lpstartdata:
                self.names.append(name)
                self.units[name] = self.lpstartunits[name].get()
                self.data[name] = self.lpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpenddata = self.lpend_info.get_data()
            self.lpendunits = self.lpend_info.get_units()
            for name in self.lpenddata:
                self.names.append(name)
                self.units[name] = self.lpendunits[name].get()
                self.data[name] = self.lpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            try:
                self.extradata = self.extra_test_inputs.get_data()
                self.extraunits = self.extra_test_inputs.get_units()
                for name in self.extradata:
                    self.names.append(name)
                    self.units[name] = self.extraunits[name].get()
                    self.data[name] = self.extradata[name].get()
                    self.unc[name] = ''
                    self.uval[name] = ''
            except:
                pass

            self.weightdata = self.weight_info.get_data()
            for name in self.weightdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.weightdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            success = 0

            # Guardar en CSV
            try:
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except PermissionError:
                message = self.file_path + ' está abierto en otro programa, ciérrelo y vuelva a intentarlo.'
                # Error
                messagebox.showerror("Error", message)

            if success == 1:
                success = 0
                self.output_path = os.path.join(self.folder_path,
                                                f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
                self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
                try:
                    [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
                    success = 1
                except PermissionError:
                    message = self.output_path + ' está abierto en otro programa, ciérrelo y vuelva a intentarlo.'
                    # Error
                    messagebox.showerror("Error", message)
                if success == 1:
                    self.frame.destroy()
                    # Crear un cuaderno para contener las pestañas
                    self.notebook = ttk.Notebook(height=30000)
                    self.notebook.grid(row=0, column=0)

                    # Crear un nuevo marco
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Agregar la pestaña al cuaderno con el nombre de la carpeta como etiqueta de la pestaña
                    self.notebook.add(self.tab_frame, text="Menú")

                    # Configurar el marco como lo hiciste para el marco original
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff", height=self.winfo_height(),
                                          width=self.winfo_width() * 20)
                    self.frame.grid(row=1, column=0)

                    self.energy_button = tk.Button(self.frame, text="Paso 1: Cálculos de Energía",
                                                   command=self.on_energy)
                    self.energy_button.grid(row=1, column=0, padx=(0, 125))

                    blank = tk.Frame(self.frame, width=self.winfo_width() - 1040)
                    blank.grid(row=0, column=2, rowspan=2)

                    self.cali_button = tk.Button(self.frame, text="Paso 2: Ajustar Calibraciones de Sensores",
                                                 command=self.on_cali)
                    self.cali_button.grid(row=2, column=0, padx=(0, 50))

                    self.bkg_button = tk.Button(self.frame, text="Paso 3: Restar Fondo", command=self.on_bkg)
                    self.bkg_button.grid(row=3, column=0, padx=(0, 155))

                    self.grav_button = tk.Button(self.frame, text="Paso 4: Calcular Datos Gravimétricos (opcional)",
                                                 command=self.on_grav)
                    self.grav_button.grid(row=4, column=0, padx=(0, 15))

                    self.emission_button = tk.Button(self.frame, text="Paso 5: Calcular Emisiones", command=self.on_em)
                    self.emission_button.grid(row=5, column=0, padx=(0, 125))

                    self.all_button = tk.Button(self.frame, text="Ver Todos los Resultados", command=self.on_all)
                    self.all_button.grid(row=6, column=0, padx=(0, 135))

                    self.plot_button = tk.Button(self.frame, text="Graficar Datos", command=self.on_plot)
                    self.plot_button.grid(row=7, column=0, padx=(0, 195))

                    # Botón de salida
                    exit_button = tk.Button(self.frame, text="SALIR", command=root.quit, bg="red", fg="white")
                    exit_button.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")

                    # Instrucciones
                    message = f'* Utilice los siguientes botones para procesar sus datos.\n' \
                              f'* Los botones se volverán verdes cuando tengan éxito.\n' \
                              f'* Los botones se volverán rojos si fallan.\n' \
                              f'* Aparecerán pestañas que contendrán salidas de cada paso.\n' \
                              f'* Si se cambian datos de un paso anterior, todos los pasos posteriores deben repetirse.\n' \
                              f'* Los archivos con salidas de datos aparecerán en la carpeta que seleccionó. Modificar estos archivos cambiará el resultado calculado si se repiten los pasos.\n\n' \
                              f'NO proceda al siguiente paso hasta que el paso anterior tenga éxito.\n' \
                              f'Si un paso no tiene éxito y se han seguido todas las instrucciones del mensaje de error ' \
                              f'o no aparece un mensaje de error, envíe una captura de pantalla de la impresión en su intérprete de Python ' \
                              f'o la segunda pantalla (negra con escritura blanca si usa la versión de la aplicación) junto con sus datos a jaden@aprovecho.org.'
                    instructions = tk.Text(self.frame, width=85, wrap="word", height=13)
                    instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                    instructions.insert(tk.END, message)
                    instructions.configure(state="disabled")

                    self.toggle = tk.Button(self.frame, text="      Haga clic para ingresar nuevos valores       ",
                                            bg='lightblue',
                                            command=self.update_input)
                    self.toggle.grid(row=0, column=0)

                    # Recentrar la vista en la esquina superior izquierda
                    self.canvas.yview_moveto(0)
                    self.canvas.xview_moveto(0)

                    self.on_energy()
                    self.on_cali()
                    self.on_bkg()
                    self.on_grav()
                    self.on_em()
                    self.on_all()

    def on_okay(self):  # Cuando se presiona el botón "Ejecutar con entradas anteriores"
        self.inputmethod = '1'
        # para cada marco, verificar entradas
        float_errors = []
        blank_errors = []
        range_errors = []
        value_errors = []
        format_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.comments.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors, range_errors = self.enviro_info.check_input_validity(float_errors, blank_errors,
                                                                                         range_errors)
        float_errors, blank_errors, range_errors = self.fuel_info.check_input_validity(float_errors, blank_errors,
                                                                                       range_errors)
        float_errors, blank_errors, value_errors, format_errors = self.hpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.hpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.mpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.mpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.lpstart_info.check_input_validity(float_errors,
                                                                                                         blank_errors,
                                                                                                         value_errors,
                                                                                                         format_errors)
        float_errors, blank_errors, format_errors = self.lpend_info.check_input_validity(float_errors, blank_errors,
                                                                                         format_errors)
        float_errors, blank_errors = self.weight_info.check_input_validity(float_errors, blank_errors)

        message = ''
        if len(float_errors) != 0:
            floatmessage = 'Las siguientes variables requieren una entrada numérica:'
            for name in float_errors:
                floatmessage = floatmessage + ' ' + name

            message = message + floatmessage + '\n'

        if len(blank_errors) != 0:
            blankmessage = 'Las siguientes variables se dejaron en blanco pero requieren una entrada:'
            for name in blank_errors:
                blankmessage = blankmessage + ' ' + name

            message = message + blankmessage + '\n'

        if len(range_errors) != 0:
            rangemessage = 'Las siguientes variables están fuera del rango de valores esperado:'
            for name in range_errors:
                rangemessage = rangemessage + ' ' + name

            message = message + rangemessage + '\n'

        if len(value_errors) != 0:
            valuemessage = 'Las siguientes variables tienen una masa inicial que es menor que la masa final:'
            for name in value_errors:
                valuemessage = valuemessage + ' ' + name

            message = message + valuemessage + '\n'

        if len(format_errors) != 0:
            formatmessage = 'Las siguientes tienen un formato incorrecto para la hora o no coinciden ' \
                            'con el formato de hora ingresado en otras áreas \n Los formatos de hora aceptados son yyyymmdd HH:MM:SS o HH:MM:SS:'
            for name in format_errors:
                formatmessage = formatmessage + ' ' + name

            message = message + formatmessage + '\n'

        if message != '':
            # Error
            messagebox.showerror("Error", message)
        else:
            self.names = []
            self.units = {}
            self.data = {}
            self.unc = {}
            self.uval = {}

            name = 'nombre_variable'
            self.names.append(name)
            self.units[name] = 'unidades'
            self.data[name] = 'valor'
            self.unc[name] = 'incertidumbre'
            self.uval[name] = ''

            self.testdata = self.test_info.get_data()
            for name in self.testdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.testdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.commentsdata = self.comments.get_data()
            for n, name in enumerate(self.commentsdata):
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.commentsdata[name].get("1.0", "end").strip()
                self.unc[name] = ''
                self.uval[name] = ''

            self.envirodata = self.enviro_info.get_data()
            self.envirounits = self.enviro_info.get_units()
            for name in self.envirodata:
                self.names.append(name)
                self.units[name] = self.envirounits[name].get()
                self.data[name] = self.envirodata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.fueldata = self.fuel_info.get_data()
            self.fuelunits = self.fuel_info.get_units()
            for name in self.fueldata:
                self.names.append(name)
                self.units[name] = self.fuelunits[name].get()
                self.data[name] = self.fueldata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpstartdata = self.hpstart_info.get_data()
            self.hpstartunits = self.hpstart_info.get_units()
            for name in self.hpstartdata:
                self.names.append(name)
                self.units[name] = self.hpstartunits[name].get()
                self.data[name] = self.hpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpenddata = self.hpend_info.get_data()
            self.hpendunits = self.hpend_info.get_units()
            for name in self.hpenddata:
                self.names.append(name)
                self.units[name] = self.hpendunits[name].get()
                self.data[name] = self.hpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpstartdata = self.mpstart_info.get_data()
            self.mpstartunits = self.mpstart_info.get_units()
            for name in self.mpstartdata:
                self.names.append(name)
                self.units[name] = self.mpstartunits[name].get()
                self.data[name] = self.mpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpenddata = self.mpend_info.get_data()
            self.mpendunits = self.mpend_info.get_units()
            for name in self.mpenddata:
                self.names.append(name)
                self.units[name] = self.mpendunits[name].get()
                self.data[name] = self.mpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpstartdata = self.lpstart_info.get_data()
            self.lpstartunits = self.lpstart_info.get_units()
            for name in self.lpstartdata:
                self.names.append(name)
                self.units[name] = self.lpstartunits[name].get()
                self.data[name] = self.lpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpenddata = self.lpend_info.get_data()
            self.lpendunits = self.lpend_info.get_units()
            for name in self.lpenddata:
                self.names.append(name)
                self.units[name] = self.lpendunits[name].get()
                self.data[name] = self.lpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            try:
                self.extradata = self.extra_test_inputs.get_data()
                self.extraunits = self.extra_test_inputs.get_units()
                for name in self.extradata:
                    self.names.append(name)
                    self.units[name] = self.extraunits[name].get()
                    self.data[name] = self.extradata[name].get()
                    self.unc[name] = ''
                    self.uval[name] = ''
            except:
                pass

            self.weightdata = self.weight_info.get_data()
            for name in self.weightdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.weightdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            success = 0

            # Guardar en CSV
            try:
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except PermissionError:
                message = self.file_path + ' está abierto en otro programa, ciérrelo y vuelva a intentarlo.'
                # Error
                messagebox.showerror("Error", message)

            if success == 1:
                success = 0
                self.output_path = os.path.join(self.folder_path,
                                                f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
                self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
                try:
                    [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
                    success = 1
                except PermissionError:
                    message = self.output_path + ' está abierto en otro programa, ciérrelo y vuelva a intentarlo.'
                    # Error
                    messagebox.showerror("Error", message)
                if success == 1:
                    self.frame.destroy()
                    # Crear un cuaderno para contener las pestañas
                    self.notebook = ttk.Notebook(height=30000)
                    self.notebook.grid(row=0, column=0)

                    # Crear un nuevo marco
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Agregar la pestaña al cuaderno con el nombre de la carpeta como etiqueta de la pestaña
                    self.notebook.add(self.tab_frame, text="Menú")

                    # Configurar el marco como lo hiciste para el marco original
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff", height=self.winfo_height(),
                                          width=self.winfo_width() * 20)
                    self.frame.grid(row=1, column=0)

                    self.energy_button = tk.Button(self.frame, text="Paso 1: Cálculos de Energía",
                                                   command=self.on_energy)
                    self.energy_button.grid(row=1, column=0, padx=(0, 125))

                    blank = tk.Frame(self.frame, width=self.winfo_width() - 1040)
                    blank.grid(row=0, column=2, rowspan=2)

                    self.cali_button = tk.Button(self.frame, text="Paso 2: Ajustar Calibraciones de Sensores",
                                                 command=self.on_cali)
                    self.cali_button.grid(row=2, column=0, padx=(0, 50))

                    self.bkg_button = tk.Button(self.frame, text="Paso 3: Restar Fondo", command=self.on_bkg)
                    self.bkg_button.grid(row=3, column=0, padx=(0, 155))

                    self.grav_button = tk.Button(self.frame, text="Paso 4: Calcular Datos Gravimétricos (opcional)",
                                                 command=self.on_grav)
                    self.grav_button.grid(row=4, column=0, padx=(0, 15))

                    self.emission_button = tk.Button(self.frame, text="Paso 5: Calcular Emisiones", command=self.on_em)
                    self.emission_button.grid(row=5, column=0, padx=(0, 125))

                    self.all_button = tk.Button(self.frame, text="Ver Todos los Resultados", command=self.on_all)
                    self.all_button.grid(row=6, column=0, padx=(0, 135))

                    self.plot_button = tk.Button(self.frame, text="Graficar Datos", command=self.on_plot)
                    self.plot_button.grid(row=7, column=0, padx=(0, 195))

                    # Botón de salida
                    exit_button = tk.Button(self.frame, text="SALIR", command=root.quit, bg="red", fg="white")
                    exit_button.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")

                    # Instrucciones
                    message = f'* Utilice los siguientes botones para procesar sus datos.\n' \
                              f'* Los botones se volverán verdes cuando tengan éxito.\n' \
                              f'* Los botones se volverán rojos si fallan.\n' \
                              f'* Aparecerán pestañas que contendrán salidas de cada paso.\n' \
                              f'* Si se cambian datos de un paso anterior, todos los pasos posteriores deben repetirse.\n' \
                              f'* Los archivos con salidas de datos aparecerán en la carpeta que seleccionó. Modificar estos archivos cambiará el resultado calculado si se repiten los pasos.\n\n' \
                              f'NO proceda al siguiente paso hasta que el paso anterior tenga éxito.\n' \
                              f'Si un paso no tiene éxito y se han seguido todas las instrucciones del mensaje de error ' \
                              f'o no aparece un mensaje de error, envíe una captura de pantalla de la impresión en su intérprete de Python ' \
                              f'o la segunda pantalla (negra con escritura blanca si usa la versión de la aplicación) junto con sus datos a jaden@aprovecho.org.'
                    instructions = tk.Text(self.frame, width=85, wrap="word", height=13)
                    instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                    instructions.insert(tk.END, message)
                    instructions.configure(state="disabled")

                    self.toggle = tk.Button(self.frame, text=" Haga clic para ejecutar con los valores actuales ",
                                            bg='violet',
                                            command=self.update_input)
                    self.toggle.grid(row=0, column=0)

                    # Recentrar la vista en la esquina superior izquierda
                    self.canvas.yview_moveto(0)
                    self.canvas.xview_moveto(0)

    def update_input(self):
        if self.inputmethod == '2':
            self.inputmethod = '1'
            self.toggle.config(text=" Haga clic para ejecutar con los valores actuales ", bg='violet')
        elif self.inputmethod == '1':
            self.inputmethod = '2'
            self.toggle.config(text="      Haga clic para ingresar nuevos valores       ", bg='lightblue')

    def on_plot(self):
        phases = ['hp', 'mp', 'lp']

        # Create the popup
        popup = tk.Toplevel(self)
        popup.title("Seleccionar Fases")

        selected_phases = []

        # Function to handle OK button click
        def ok():
            nonlocal selected_phases
            selected_phases = [phases[i] for i in listbox.curselection()]
            popup.destroy()

        # Function to handle Cancel button click
        def cancel():
            popup.destroy()

        # Instructions
        message = tk.Label(popup, text="Seleccione las fases para el gráfico")
        message.grid(row=0, column=0, columnspan=2, padx=20)

        # Listbox to display phases
        listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE, height=5)
        for phase in phases:
            listbox.insert(tk.END, phase)
        listbox.grid(row=1, column=0, columnspan=2, padx=20)

        # OK button
        ok_button = tk.Button(popup, text="Aceptar", command=ok)
        ok_button.grid(row=2, column=0, padx=5, pady=5)

        # Cancel button
        cancel_button = tk.Button(popup, text="Cancelar", command=cancel)
        cancel_button.grid(row=2, column=1, padx=5, pady=5)

        # Wait for popup to be destroyed
        popup.wait_window()

        print(selected_phases)
        self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")

        for phase in selected_phases:
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeriesMetrics_"
                                           + phase + ".csv")
            if os.path.isfile(self.input_path):  # check that the data exists
                try:
                    self.plots_path = os.path.join(self.folder_path,
                                                   f"{os.path.basename(self.folder_path)}_plots_"
                                                   + phase + ".csv")
                    self.fig_path = os.path.join(self.folder_path,
                                                   f"{os.path.basename(self.folder_path)}_plot_"
                                                   + phase + ".png")

                    names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                        PEMS_Plotter(self.input_path, self.fuel_path, self.fuelmetric_path, self.exact_path, self.scale_path,
                                     self.nano_path, self.teom_path, self.senserion_path, self.ops_path, self.pico_path, self.plots_path,
                                     self.fig_path, self.log_path)
                    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames,
                                        pnames, self.plots_path, self.fig_path)
                except PermissionError:
                    message = f"El archivo: {self.plots_path} está abierto en otro programa, cierre y vuelva a intentarlo."
                    messagebox.showerror("Error", message)
                except ValueError as e:
                    print(e)
                    if 'could not convert' in str(e):
                        message = f'La entrada de la escala requiere un número válido. Las letras y los espacios en blanco no son números válidos. Corrija el problema y vuelva a intentarlo.'
                        messagebox.showerror("Error", message)
                    if 'invalid literal' in str(e):
                        message = f'La entrada graficada requiere una entrada válida de un número entero ya sea 0 para no graficar o cualquier entero para graficar. Corrija el problema y vuelva a intentarlo.'
                        messagebox.showerror("Error", message)
                    if 'valid value for color' in str(e):
                        message = f'Uno de los colores es inválido. Se puede encontrar una lista válida de colores en: '
                        error_win = tk.Toplevel(root)
                        error_win.title("Error")
                        error_win.geometry("400x100")

                        error_label = tk.Label(error_win, text=message)
                        error_label.pack(pady=10)

                        hyperlink = tk.Button(error_win,
                                              text="https://matplotlib.org/stable/gallery/color/named_colors.html",
                                              command=open_website)
                        hyperlink.pack()

                # Check if the grav Calculations tab exists
                tab_index = None
                for i in range(self.notebook.index("end")):
                    if self.notebook.tab(i, "text") == (phase + " Plot"):
                        tab_index = i
                if tab_index is None:
                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Add the tab to the notebook with the folder name as the tab label
                    self.notebook.add(self.tab_frame, text=phase + " Plot")

                    # Set up the frame as you did for the original frame
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)
                else:
                    # Overwrite existing tab
                    # Destroy existing tab frame
                    self.notebook.forget(tab_index)
                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Add the tab to the notebook with the folder name as the tab label
                    self.notebook.add(self.tab_frame, text=phase + " Plot")

                    # Set up the frame as you did for the original frame
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)

                self.create_plot_frame(self.plots_path, self.fig_path, self.folder_path)

    def create_plot_frame(self, plot_path, fig_path, folder_path):
        plot_frame = Plot(self.frame, plot_path, fig_path, folder_path)
        plot_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_all(self):
        try:
            self.all_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_AllOutputs.csv")
            names, units, data, unc, uval = io.load_constant_inputs(self.all_path)
            self.all_button.config(bg="lightgreen")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.all_button.config(bg="red")

        # Check if the grav Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Todos los Resultados":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Todos los Resultados")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Todos los Resultados")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        self.create_all_frame(data, units)

    def create_all_frame(self, data, units):
        all_frame = All_Outputs(self.frame, data, units)
        all_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_em(self):
        try:
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeries.csv")
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.grav_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravOutputs.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.output_path = os.path.join(self.folder_path,
                                            f"{os.path.basename(self.folder_path)}_EmissionOutputs.csv")
            self.all_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_AllOutputs.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            logs, data, units = LEMS_EmissionCalcs(self.input_path, self.energy_path, self.grav_path, self.average_path,
                                                   self.output_path, self.all_path, self.log_path, self.phase_path,
                                                   self.fuel_path, self.fuelmetric_path, self.exact_path,
                                                   self.scale_path, self.nano_path, self.teom_path, self.senserion_path,
                                                   self.ops_path, self.pico_path)
            self.emission_button.config(bg="lightgreen")
        except PermissionError:
            message = f"Uno de los siguientes archivos: {self.output_path}, {self.all_path} está abierto en otro programa. Por favor, cierre y vuelva a intentarlo."
            messagebox.showerror("Error", message)
            self.emission_button.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.emission_button.config(bg="red")

        # Check if the grav Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Cálculos de Emisión":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos de Emisión")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos de Emisión")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        self.create_em_frame(logs, data, units)

    def create_em_frame(self, logs, data, units):
        em_frame = Emission_Calcs(self.frame, logs, data, units)
        em_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_grav(self):
        try:
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravInputs.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravOutputs.csv")
            logs, gravval, outval, gravunits, outunits = LEMS_GravCalcs(self.input_path, self.average_path,
                                                                        self.phase_path, self.energy_path,
                                                                        self.output_path, self.log_path,
                                                                        self.inputmethod)
            self.grav_button.config(bg="lightgreen")
        except PermissionError:
            message = f"El archivo: {self.output_path} está abierto en otro programa. Por favor, cierre y vuelva a intentarlo."
            messagebox.showerror("Error", message)
            self.grav_path.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.grav_button.config(bg="red")

        # Check if the grav Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Cálculos Gravimétricos":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos Gravimétricos")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos Gravimétricos")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        self.create_grav_frame(logs, gravval, outval, gravunits, outunits)

    def create_grav_frame(self, logs, gravval, outval, gravunits, outunits):
        grav_frame = Grav_Calcs(self.frame, logs, gravval, outval, gravunits, outunits)
        grav_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_bkg(self):
        try:
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.input_path = os.path.join(self.folder_path,
                                           f"{os.path.basename(self.folder_path)}_RawData_Recalibrated.csv")
            self.UC_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_UCInputs.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeries.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.method_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_BkgMethods.csv")
            self.fig1 = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}__subtractbkg1.png")
            self.fig2 = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}__subtractbkg2.png")
            logs, methods, phases = PEMS_SubtractBkg(self.input_path, self.energy_path, self.UC_path, self.output_path,
                                                     self.average_path, self.phase_path, self.method_path,
                                                     self.log_path,
                                                     self.fig1, self.fig2, self.inputmethod)
            self.bkg_button.config(bg="lightgreen")
        except PermissionError:
            message = f"Uno de los siguientes archivos: {self.output_path}, {self.phase_path}, {self.method_path} está abierto en otro programa. Por favor, cierre y vuelva a intentarlo."
            messagebox.showerror("Error", message)
            self.bkg_button.config(bg="red")
        except KeyError as e:
            print(e)
            if 'time' in str(e):
                error = str(e)
                wrong = error.split(':')
                message = f"La entrada de tiempo para: {wrong} está ingresada en un formato incorrecto o es un tiempo que ocurrió antes o después de que se recopilaron los datos.\n" \
                          f"    * Verifique que el formato de tiempo se haya ingresado como hh:mm:ss o yyyymmdd hh:mm:ss\n" \
                          f"    * Verifique que no se incluyan letras, símbolos o espacios en la entrada de tiempo\n" \
                          f"    * Verifique que el tiempo ingresado exista dentro de los datos\n" \
                          f"    * Verifique que el tiempo no se haya dejado en blanco cuando debería haber una entrada.\n" \
                          f"El archivo {self.phase_path} puede necesitar abrirse y cambiarse o eliminarse."
            self.bkg_button.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.bkg_button.config(bg="red")

        # Check if the Energy Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Restar Fondo":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Restar Fondo")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Restar Fondo")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        self.create_bkg_frame(logs, self.fig1, self.fig2, methods, phases)

    def create_bkg_frame(self, logs, fig1, fig2, methods, phases):
        bkg_frame = Subtract_Bkg(self.frame, logs, fig1, fig2, methods, phases)
        bkg_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_cali(self):
        try:
            self.sensor_path = os.path.join(self.folder_path,
                                            f"{os.path.basename(self.folder_path)}_SensorboxVersion.csv")
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData.csv")
            self.output_path = os.path.join(self.folder_path,
                                            f"{os.path.basename(self.folder_path)}_RawData_Recalibrated.csv")
            self.header_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Header.csv")
            logs, firmware = LEMS_Adjust_Calibrations(self.input_path, self.sensor_path, self.output_path,
                                                      self.header_path, self.log_path, self.inputmethod)
            self.cali_button.config(bg="lightgreen")

        except UnboundLocalError:
            message = f'Algo salió mal en los cálculos del Firmware. \n' \
                      f'Por favor, verifique que la versión del firmware ingresada corresponda al número de la caja del sensor.\n' \
                      f'Versiones de firmware aceptadas:\n' \
                      f'    *SB4003.16\n' \
                      f'    *SB3001\n' \
                      f'    *SB3002\n' \
                      f'Si el firmware de su caja de sensor no es uno de los que se enumeran, se puede ingresar pero no se recalibrará nada.\n' \
                      f'Esto puede causar problemas más adelante.'
            messagebox.showerror("Error", message)
            self.cali_button.config(bg="red")

        except PermissionError:
            message = f"El archivo: {self.output_path} está abierto en otro programa. Por favor, cierre y vuelva a intentarlo."
            messagebox.showerror("Error", message)
            self.cali_button.config(bg="red")
        except IndexError:
            message = f'El programa no pudo leer correctamente el archivo de datos crudos. Por favor, revise lo siguiente:\n' \
                      f'    * No hay líneas o celdas en blanco dentro del conjunto de datos\n' \
                      f'    * La caja del sensor no se restableció en algún momento, lo que causó que se insertara un encabezado en medio del conjunto de datos.\n' \
                      f'    * No hay líneas en blanco adicionales o líneas de valor no en el archivo.\n' \
                      f'Abrir el archivo en un programa de edición de texto como el bloc de notas puede ser útil.' \
                      f'Elimine los problemas e inténtelo de nuevo.'
            messagebox.showerror("Error", message)
            self.cali_button.config(bg="red")

        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.cali_button.config(bg="red")

        # Check if the Energy Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Recalibración":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Recalibración")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Recalibración")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        self.create_adjust_frame(logs, firmware)

    def create_adjust_frame(self, logs, firmware):
        adjust_frame = Adjust_Frame(self.frame, logs, firmware)
        adjust_frame.grid(row=3, column=0, padx=0, pady=0)
        #adjust_frame.pack(side="left")

    def on_energy(self):
        try:
            [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
            self.energy_button.config(bg="lightgreen")
        except:
            self.energy_button.config(bg="red")

        # round to 3 decimals
        round_data = {}
        for name in data:
            try:
                rounded = round(data[name].n, 3)
            except:
                rounded = data[name]
            round_data[name] = rounded
        data = round_data

        # Check if the Energy Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Cálculos de Energía":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos de Energía")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Cálculos de Energía")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        # Output table
        self.create_output_table(data, units, logs, num_columns=self.winfo_width(),
                                 num_rows=self.winfo_height(),
                                 folder_path=self.folder_path)  # Adjust num_columns and num_rows as needed

    def create_output_table(self, data, units, logs, num_columns, num_rows, folder_path):
        output_table = OutputTable(self.frame, data, units, logs, num_columns, num_rows, folder_path)
        output_table.grid(row=3, column=0, columnspan=num_columns, padx=0, pady=0)

    def on_browse(self):  # cuando se presiona el botón de explorar, abrir el buscador de archivos.
        self.destroy_widgets()

        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Comprobar si el archivo _EnergyInputs.csv existe
        self.file_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
        try:
            [names, units, data, unc, uval] = io.load_constant_inputs(self.file_path)
            try:
                data.pop("variable_name")
            except:
                data.pop('nombre_variable')
            data = self.test_info.check_imported_data(data)
            data = self.comments.check_imported_data(data)
            data = self.enviro_info.check_imported_data(data)
            data = self.fuel_info.check_imported_data(data)
            data = self.hpstart_info.check_imported_data(data)
            data = self.hpend_info.check_imported_data(data)
            data = self.mpstart_info.check_imported_data(data)
            data = self.mpend_info.check_imported_data(data)
            data = self.lpstart_info.check_imported_data(data)
            data = self.lpend_info.check_imported_data(data)
            data = self.weight_info.check_imported_data(data)
            # si existe y tiene entradas no especificadas en la hoja de entrada, agréguelas
            if data:
                self.extra_test_inputs = ExtraTestInputsFrame(self.frame, "Entradas de prueba adicionales", data, units)
                self.extra_test_inputs.grid(row=5, column=0, columnspan=2)
        except FileNotFoundError:
            pass
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

    def destroy_widgets(self):
        """
        Destroy previously created widgets.
        """
        if hasattr(self, 'message'):
            self.message.destroy()
        if hasattr(self, 'file_selection_listbox'):
            self.file_selection_listbox.destroy()
        if hasattr(self, 'ok_button'):
            self.ok_button.destroy()

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class Plot(tk.Frame):
    def __init__(self, root, plotpath, figpath, folderpath):
        tk.Frame.__init__(self, root)
        self.folder_path = folderpath
        self.plotpath = plotpath
        self.variable_data = self.read_csv(plotpath)

        self.canvas = tk.Canvas(self, borderwidth=0, height=self.winfo_height() * 530, width=500)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.bind("<Configure>",
                                   lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        self.create_widgets()

        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Mostrar imagen
        image1 = Image.open(figpath)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # para evitar la recolección de basura
        label1.grid(row=1, column=2, padx=10, pady=5, columnspan=3)

    def read_csv(self, filepath):
        variable_data = []
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                variable_data.append(row)
        return variable_data

    def save_to_csv(self):
        with open(self.plotpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in self.updated_variable_data:
                writer.writerow(row)

    def create_widgets(self):
        for i, variable_row in enumerate(self.variable_data):
            variable_name = variable_row[0]
            tk.Label(self.scrollable_frame, text=variable_name).grid(row=i + 1, column=0)

            plotted_entry = tk.Entry(self.scrollable_frame)
            plotted_entry.insert(0, variable_row[1])
            plotted_entry.grid(row=i + 1, column=1)

            scale_entry = tk.Entry(self.scrollable_frame)
            scale_entry.insert(0, variable_row[2])
            scale_entry.grid(row=i + 1, column=2)

            color_entry = tk.Entry(self.scrollable_frame)
            color_entry.insert(0, variable_row[3])
            color_entry.grid(row=i + 1, column=3)

            self.variable_data[i] = [variable_name, plotted_entry, scale_entry, color_entry]

        ok_button = tk.Button(self.scrollable_frame, text="OK", command=self.save)
        ok_button.grid(row=len(self.variable_data) + 1, column=4, pady=10)

        # Establecer la altura del marco desplazable
        self.scrollable_frame.config(height=self.winfo_height() * 32)
        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    @staticmethod
    def show_error_with_link(message):
        result = messagebox.showerror("Error", message)
        if result == 'ok':
            webbrowser.open_new("https://matplotlib.org/stable/gallery/color/named_colors.html")

    def save(self):
        self.updated_variable_data = []
        for i, row in enumerate(self.variable_data):
            plotted_value = self.variable_data[i][1].get()
            scale_value = self.variable_data[i][2].get()
            color_value = self.variable_data[i][3].get()

            self.updated_variable_data.append([row[0], plotted_value, scale_value, color_value])

        self.save_to_csv()

        parts = self.plotpath.split('_')

        phase = parts[-1]
        parts = phase.split('.')
        phase = parts[0]

        self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")

        self.input_path = os.path.join(self.folder_path,
                                       f"{os.path.basename(self.folder_path)}_TimeSeriesMetrics_" + phase + ".csv")
        self.plots_path = os.path.join(self.folder_path,
                                       f"{os.path.basename(self.folder_path)}_plots_" + phase + ".csv")
        self.fig_path = os.path.join(self.folder_path,
                                     f"{os.path.basename(self.folder_path)}_plot_" + phase + ".png")

        try:
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                PEMS_Plotter(self.input_path, self.fuel_path, self.fuelmetric_path, self.exact_path,
                             self.scale_path,
                             self.nano_path, self.teom_path, self.senserion_path, self.ops_path, self.pico_path,
                             self.plots_path, self.fig_path, self.log_path)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames,
                                opsnames, pnames, self.plots_path, self.fig_path)
        except PermissionError:
            message = f"File: {self.plots_path} is open in another program, close and try again."
            messagebox.showerror("Error", message)
        except ValueError as e:
            print(e)
            if 'could not convert' in str(e):
                message = f'The scale input requires a valid number. Letters and blanks are not valid numbers. Please correct the issue and try again.'
                messagebox.showerror("Error", message)
            if 'invalid literal' in str(e):
                message = f'The plotted input requires a valid input of an integer either 0 to not plot or any integer to plot. Please correct the issue and try again.'
                messagebox.showerror("Error", message)
            if 'valid value for color' in str(e):
                message = f'One of the colors is invalid. A valid list of colors can be found at: '
                error_win = tk.Toplevel(root)
                error_win.title("Error")
                error_win.geometry("400x100")

                error_label = tk.Label(error_win, text=message)
                error_label.pack(pady=10)

                hyperlink = tk.Button(error_win,
                                      text="https://matplotlib.org/stable/gallery/color/named_colors.html",
                                      command=lambda: self.show_error_with_link(message))
                hyperlink.pack()

        # Mostrar imagen
        image1 = Image.open(self.fig_path)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # para evitar la recolección de basura
        label1.grid(row=1, column=2, padx=10, pady=5, columnspan=3)

def open_website():
    webbrowser.open_new("https://matplotlib.org/stable/gallery/color/named_colors.html")

class All_Outputs(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)

        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Buscar", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Tabla de salida
        self.text_widget = tk.Text(self, wrap="none", height=1, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<114}|".format("TODAS LAS SALIDAS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<32} | {:<13} |".format("Variable", "Valor", "Unidades")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in data.items():
            if key.endswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")
        self.text_widget.config(height=self.winfo_height()*33)
        self.text_widget.configure(state="disabled")

        # Tabla corta
        self.cut_table = tk.Text(self, wrap="none", height=1, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=3, column=4, padx=0, pady=0, columnspan=3)
        cut_header = "{:<110}|".format("MÉTRICAS PESADAS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<28} | {:<12} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = round(float(value.n))
            except:
                try:
                    val = round(float(value))
                except:
                    val = value
            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.endswith('weighted'):
                row = "{:<35} | {:<15} | {:<10} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")

        cut_header = "{:<70}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<128}|".format("NIVELES ISO")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<60} |".format("Variable", "Nivel")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value

            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.startswith('tier'):
                row = "{:<35} | {:<30} |".format(key, val)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        cut_header = "{:<69}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")

        cut_header = "{:<102}|".format("VARIABLES IMPORTANTES")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<28} | {:<12} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_parameters = ['eff_w_char', 'eff_wo_char', 'char_mass_productivity', 'char_energy_productivity',
                          'cooking_power', 'burn_rate', 'phase_time', 'CO_useful_eng_deliver', 'PM_useful_eng_deliver',
                          'PM_mass_time', 'PM_heat_mass_time', 'CO_mass_time']
        for key, value in data.items():
            if any(key.startswith(param) for param in cut_parameters):
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<15} | {:<10} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        self.cut_table.config(height=self.winfo_height()*33)
        self.cut_table.configure(state="disabled")

    def find_text(self):
        search_text = self.find_entry.get()

        if search_text:
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("highlight", background="yellow")

        if search_text:
            self.cut_table.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.cut_table.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.cut_table.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.cut_table.tag_configure("highlight", background="yellow")

class Emission_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units):
        tk.Frame.__init__(self, root)
        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Buscar", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Sección 'Avanzado' plegable para registros
        self.advanced_section = CollapsibleFrame(self, text="Avanzado", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para los registros y agregar una barra de desplazamiento vertical
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Tabla de salida
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<124}|".format("SALIDAS DE EMISIÓN")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")
        header = "{:<54} | {:<32} | {:<33} |".format("Variable", "Valor", "Unidades")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")

        rownum = 0
        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value
                if not val:
                    val = " "
                row = "{:<30} | {:<17} | {:<20} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 75 + "\n")

        self.text_widget.config(height=self.winfo_height() * 32)
        self.text_widget.configure(state="disabled")

        # Tabla corta
        self.cut_table = tk.Text(self, wrap="none", height=1, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=2, column=4, padx=0, pady=0, columnspan=3)
        cut_header = "{:<108}|".format("MÉTRICAS PESADAS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<25} | {:<14} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = round(float(value.n))
            except:
                try:
                    val = round(float(value))
                except:
                    val = value
            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.endswith('weighted'):
                row = "{:<35} | {:<13} | {:<11} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")

        cut_header = "{:<70}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<128}|".format("NIVELES ISO")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<60} |".format("Variable", "Nivel")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value

            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.startswith('tier'):
                row = "{:<35} | {:<30} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        cut_header = "{:<69}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")

        cut_header = "{:<110}|".format("VARIABLES IMPORTANTES")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 68 + "\n", "bold")
        cut_header = "{:<64} | {:<24} | {:<15} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 68 + "\n", "bold")
        cut_parameters = ['CO_useful_eng_deliver', 'PM_useful_eng_deliver',
                          'PM_mass_time', 'PM_heat_mass_time', 'CO_mass_time']
        for key, value in data.items():
            if any(key.startswith(param) for param in cut_parameters):
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<13} | {:<11} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 75 + "\n")
        self.cut_table.config(height=self.winfo_height() * 32)
        self.cut_table.configure(state="disabled")

    def find_text(self):
        search_text = self.find_entry.get()

        if search_text:
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("highlight", background="yellow")

class Grav_Calcs(tk.Frame):
    def __init__(self, root, logs, gravval, outval, gravunits, outunits):
        tk.Frame.__init__(self, root)
        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Buscar", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Sección 'Avanzado' plegable para registros
        self.advanced_section = CollapsibleFrame(self, text="Avanzado", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para los registros y agregar una barra de desplazamiento vertical
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Tabla de salida para gravval
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<117}|".format("ENTRADAS GRAV")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<44} | {:<32} | {:<33} |".format("Variable", "Valor", "Unidades")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        rownum = 0
        for key, value in gravval.items():
            if 'variable' not in key:
                unit = gravunits.get(key, "")
                try:
                    val = value.n
                except:
                    val = value
                if not val:
                    val = " "
                row = "{:<25} | {:<17} | {:<20} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")
                rownum += 2

        self.text_widget.config(height=self.winfo_height() * 32)
        self.text_widget.configure(state="disabled")

        # Tabla de salida para outval
        self.out_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.out_widget.grid(row=2, column=4, columnspan=3, padx=0, pady=0)

        self.out_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<116}|".format("SALIDAS GRAV")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<44} | {:<32} | {:<28} |".format("Variable", "Valor", "Unidades")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in outval.items():
            if 'variable' not in key:
                unit = outunits.get(key, "")
                try:
                    val = value.n
                except:
                    val = value
                if not val:
                    val = " "
                row = "{:<25} | {:<17} | {:<18} |".format(key, val, unit)
                self.out_widget.insert(tk.END, row + "\n")
                self.out_widget.insert(tk.END, "_" * 70 + "\n")

        self.out_widget.config(height=self.winfo_height() * 32)
        self.out_widget.configure(state="disabled")

    def find_text(self):
        search_text = self.find_entry.get()

        if search_text:
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("highlight", background="yellow")

        if search_text:
            self.out_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.out_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.out_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.out_widget.tag_configure("highlight", background="yellow")

class Subtract_Bkg(tk.Frame):
    def __init__(self, root, logs, fig1, fig2, methods, phases):
        tk.Frame.__init__(self, root)
        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Sección 'Avanzado' plegable para registros
        self.advanced_section = CollapsibleFrame(self, text="Avanzado", collapsed=True)
        self.advanced_section.grid(row=3, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para los registros y agregar una barra de desplazamiento vertical
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=65)
        self.logs_text.grid(row=3, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=3, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Sección plegable 'Fases' para registros
        self.phase_section = CollapsibleFrame(self, text="Tiempos de Fase", collapsed=True)
        self.phase_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para las fases y agregar una barra de desplazamiento vertical
        self.phase_text = tk.Text(self.phase_section.content_frame, wrap="word", height=10, width=65)
        self.phase_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        phase_scrollbar = tk.Scrollbar(self.phase_section.content_frame, command=self.phase_text.yview)
        phase_scrollbar.grid(row=1, column=3, sticky="ns")

        self.phase_text.config(yscrollcommand=phase_scrollbar.set)

        for key, value in phases.items():
            if 'variable' not in key:
                self.phase_text.insert(tk.END, key + ': ' + value + "\n")

        self.phase_text.configure(state="disabled")

        # Sección plegable 'Método' para registros
        self.method_section = CollapsibleFrame(self, text="Métodos de Resta", collapsed=True)
        self.method_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para los métodos y agregar una barra de desplazamiento vertical
        self.method_text = tk.Text(self.method_section.content_frame, wrap="word", height=10, width=65)
        self.method_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        method_scrollbar = tk.Scrollbar(self.method_section.content_frame, command=self.method_text.yview)
        method_scrollbar.grid(row=2, column=3, sticky="ns")

        self.method_text.config(yscrollcommand=method_scrollbar.set)

        for key, value in methods.items():
            if 'chan' not in key:
                self.method_text.insert(tk.END, key + ': ' + value + "\n")

        self.method_text.configure(state="disabled")

        # Mostrar imágenes debajo de la sección Avanzado
        image1 = Image.open(fig1)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # para evitar la recolección de basura
        label1.grid(row=4, column=0, padx=10, pady=5, columnspan=3)

        image2 = Image.open(fig2)
        image2 = image2.resize((550, 450), Image.LANCZOS)
        photo2 = ImageTk.PhotoImage(image2)
        label2 = tk.Label(self, image=photo2, width=575)
        label2.image = photo2  # para evitar la recolección de basura
        label2.grid(row=4, column=4, padx=10, pady=5, columnspan=3)

class Adjust_Frame(tk.Frame):
    def __init__(self, root, logs, firmware):
        tk.Frame.__init__(self, root)
        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Versión del firmware
        firm_message = tk.Text(self, wrap="word", height=1, width=80)
        firm_message.grid(row=0, column=0, columnspan=3)
        firm_message.insert(tk.END, f"Versión del Firmware Utilizado: {firmware}")
        firm_message.configure(state="disabled")

        # Sección 'Avanzado' plegable para registros
        self.advanced_section = CollapsibleFrame(self, text="Avanzado", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Usar un widget Text para los registros y agregar una barra de desplazamiento vertical
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=75)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

class CollapsibleFrame(ttk.Frame):
    def __init__(self, master, text, collapsed=True, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.is_collapsed = tk.BooleanVar(value=collapsed)

        # Header
        self.header = ttk.Label(self, text=f"▼ {text}", style="CollapsibleFrame.TLabel")
        self.header.grid(row=0, column=0, sticky="w", pady=5)
        self.header.bind("<Button-1>", self.toggle)

        # Content Frame
        self.content_frame = tk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="w")

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Call toggle to set initial state
        self.toggle()

    def toggle(self, event=None):
        if self.is_collapsed.get():
            self.content_frame.grid_remove()
            self.header["text"] = f"▼ {self.header['text'][2:]}"
        else:
            self.content_frame.grid()
            self.header["text"] = f"▲ {self.header['text'][2:]}"

        self.is_collapsed.set(not self.is_collapsed.get())

class OutputTable(tk.Frame):
    def __init__(self, root, data, units, logs, num_columns, num_rows, folder_path):
        tk.Frame.__init__(self, root)

        # Botón de salida
        exit_button = tk.Button(self, text="SALIR", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Buscar", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Sección 'Avanzado' plegable para registros
        self.advanced_section = CollapsibleFrame(self, text="Avanzado", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Utilice un widget Text para los registros y agregue una barra de desplazamiento vertical
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Sección de Advertencia plegable
        self.warning_section = CollapsibleFrame(self, text="Advertencias", collapsed=False)  # iniciar abierta
        self.warning_section.grid(row=2, column=0, pady=0, padx=0, sticky='w')

        self.warning_frame = tk.Text(self.warning_section.content_frame, wrap="word", width=70, height=10)
        self.warning_frame.grid(row=2, column=0, columnspan=6)

        warn_scrollbar = tk.Scrollbar(self.warning_section.content_frame, command=self.warning_frame.yview)
        warn_scrollbar.grid(row=2, column=6, sticky='ns')
        self.warning_frame.config(yscrollcommand=warn_scrollbar.set)

        # Configurar una etiqueta para texto en negrita

        # Tabla de salida
        self.text_widget = tk.Text(self, wrap="none", height=num_rows, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<100}|".format("TODAS LAS SALIDAS DE ENERGÍA")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<32} | {:<13} |".format("Variable", "Valor", "Unidades")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        # Tabla corta
        self.cut_table = tk.Text(self, wrap="none", height=num_rows, width=72)
        # Configurar una etiqueta para texto en negrita
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=3, column=3, padx=0, pady=0, columnspan=3)
        cut_header = "{:<106}|".format("MÉTRICAS PONDERADAS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<34} | {:<9} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value
            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.endswith('weighted'):
                row = "{:<35} | {:<18} | {:<8} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")

        cut_header = "{:<70}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<124}|".format("TIPOS DE ISO")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<59} |".format("Variable", "Tipo")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value

            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.startswith('tier'):
                row = "{:<35} | {:<30} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        cut_header = "{:<69}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<106}|".format("VARIABLES IMPORTANTES")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<32} | {:<13} |".format("Variable", "Valor", "Unidades")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_parameters = ['eff_w_char', 'eff_wo_char', 'char_mass_productivity', 'char_energy_productivity',
                          'cooking_power', 'burn_rate', 'phase_time']

        tot_rows = 1
        for key, value in data.items():
            if key.endswith('variable') or key.endswith("comments"):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = value.n
                except:
                    val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")

                if any(key.startswith(param) for param in cut_parameters):
                    unit = units.get(key, "")
                    try:
                        val = value.n
                    except:
                        val = value

                    if not val:
                        val = " "
                    if not unit:
                        unit = " "
                    row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                    self.cut_table.insert(tk.END, row + "\n")
                    self.cut_table.insert(tk.END, "_" * 70 + "\n")

            # Comprueba la condición y resalta en rojo con mensaje de advertencia
            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) > 55 and float(val) < 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es más alto que lo típico. Esto no significa que sea incorrecto, pero los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado bajo.\n"
                        warning_message_3 = f"      Verifique que la masa de carbón (carbón creado) sea un peso realista y no demasiado bajo.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia grande (más de 1000 g (1 L)).\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado alta.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es más de 100. Esto es incorrecto, los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado bajo.\n"
                        warning_message_3 = f"      Verifique que la masa de carbón (carbón creado) sea un peso realista y no demasiado bajo.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia grande (más de 1000 g (1 L)).\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado alta.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es más bajo que lo típico. Esto no significa que sea incorrecto, pero los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado alto.\n"
                        warning_message_3 = f"      Verifique que la masa de carbón (carbón creado) sea un peso realista y no demasiado alto.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia pequeña.\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado baja.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es negativo. Esto es incorrecto, los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado alto.\n"
                        warning_message_3 = f"      Verifique que la masa de carbón (carbón creado) sea un peso realista y no demasiado alto.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia pequeña.\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado baja.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            ########################################################################3
            #TE sin carbón
            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 55 and float(val) < 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es mayor que lo típico. Esto no significa que sea incorrecto, pero se deben verificar los resultados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado alto.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia grande (más de 1000g (1L)).\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado alta.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es más de 100. Esto es incorrecto y los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado bajo.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia grande (más de 1000g (1L)).\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado alta.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="yellow")
                        self.warning_frame.tag_add("yellow", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es menor que lo típico. Esto no significa que sea incorrecto, pero se deben verificar los resultados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado alto.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia pequeña.\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado baja.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es negativo. Esto es incorrecto y los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de combustible (combustible consumido) sea un peso realista y no demasiado alto.\n"
                        warning_message_4 = f"      Verifique que la masa de agua final - masa de agua inicial no resulte en una diferencia pequeña.\n"
                        warning_message_5 = f"      Verifique que la temperatura máxima del agua - temperatura inicial del agua no sea demasiado baja.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")

                except:
                    pass

            ##########################################################################################
            # Productividad de carbón
            if key.startswith('char_energy_productivity') or key.startswith('char_mass_productivity'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es negativo. Esto es incorrecto y los resultados deben ser verificados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_2 = f"      Verifique que la masa de carbón (carbón creado) no sea negativa.\n"
                        warning_message_4 = f"      Verifique que el valor calorífico bruto para el carbón vegetal sea correcto.\n"
                        warning_message_5 = f"      Verifique que no se hayan ingresado combustibles que no sean carbón con una fracción de carbono superior a 0.75.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #############################################################
            # Masa de carbón
            if key.startswith('char_mass_hp') or key.startswith('char_mass_mp') or key.startswith('char_mass_lp'):
                try:
                    if val and float(val) > 0.050:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} es una masa grande. Esto no significa que sea incorrecto, pero se deben verificar los resultados.\n" \
                                            f"  Esto puede ser un problema de entrada. Por favor, verifique los valores de lo siguiente:\n"
                        warning_message_5 = f"      Verifique que no se hayan ingresado combustibles que no sean carbón con una fracción de carbono superior a 0.75.\n"
                        warning_message = warning_message_1 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            #############################################################
            # Temperatura del agua
            if key.startswith('initial_water_temp'):
                try:
                    delta = abs(float(val) - float(data['initial_air_temp'].n))
                    if val and delta > 10:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA:\n')
                        warning_message_1 = f"  {key} está más de 10 grados de la temperatura ambiente.\n"
                        warning_message = warning_message_1

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #######################################################33
            # Verificaciones ISO
            if key.startswith('phase_time'):
                try:
                    if val and float(val) < 30:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA ISO:\n')
                        warning_message_1 = f"  {key} es inferior a 30 minutos. Las pruebas ISO requieren periodos de fase de 30 minutos.\n"
                        warning_message_2 = f"      Esta advertencia puede ser ignorada si no se está ejecutando una prueba ISO.\n"
                        warning_message = warning_message_1 + warning_message_2

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            if key.startswith('phase_time'):
                try:
                    if val and float(val) > 35:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA ISO:\n')
                        warning_message_1 = f"  {key} es más de 35. Las pruebas ISO requieren periodos de fase de máximo 35 minutos (incluyendo apagado).\n"
                        warning_message_2 = f"      Las fases de prueba pueden durar 60 minutos si se está ejecutando una sola fase.\n"
                        warning_message_3 = f"      Esta advertencia puede ser ignorada si no se está ejecutando una prueba ISO.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            if key.startswith('end_water_temp'):
                try:
                    phase = key[-3:]
                    max_temp = data['max_water_temp_pot1' + phase]
                    delta = float(max_temp.n) - float(val)
                    print(delta)
                    if val and (delta > 5 or delta < 5) and float(data['phase_time' + phase]) < 35:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA ISO:\n')
                        warning_message_1 = f"  max_water_temp_pot1' {phase} - {key} no está a 5 grados. " \
                                            f"\n    Las pruebas ISO requieren un periodo de apagado de 5 minutos o cuando la temperatura máxima del agua cae a 5 grados por debajo de la temperatura de ebullición..\n"
                        warning_message_2 = f"      Esta advertencia puede ser ignorada si se realizó el procedimiento de apagado de 5 minutos.\n"
                        warning_message_3 = f"      Esta advertencia puede ser ignorada si no se está ejecutando una prueba ISO.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('firepower_w_char_mp'):
                try:
                    hp = float(data['firepower_w_char_hp'])
                    mp = float(val)
                    lp = float(data['firepower_w_char_lp'])
                    result = lp <= mp <= hp and lp + 1 <= mp <= hp - 1
                    if result:
                        pass
                    else:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ADVERTENCIA ISO:\n')
                        warning_message_1 = f"  {key} no está entre potencia alta y potencia baja. Las pruebas ISO requieren que la media potencia de fuego esté entre alta y baja.\n"
                        warning_message = warning_message_1

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = num_lines + warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            tot_rows += 2

        self.text_widget.config(height=self.winfo_height() * (30))
        self.cut_table.config(height=self.winfo_height() * (30))
        self.warning_frame.config(height=8)

        self.text_widget.configure(state="disabled")
        self.warning_frame.configure(state="disabled")
        self.cut_table.configure(state="disabled")

    def find_text(self):
        search_text = self.find_entry.get()

        if search_text:
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("highlight", background="yellow")

        if search_text:
            self.cut_table.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.cut_table.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.cut_table.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.cut_table.tag_configure("highlight", background="yellow")
class TestInfoFrame(tk.LabelFrame): # Área de entrada de información de prueba
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.testinfo = {'test_name': 'Nombre de la prueba', 'test_number': 'Número de prueba',
                         'date': 'Fecha', 'name_of_tester': 'Nombre del probador',
                         'location': 'Ubicación', 'stove_type/model': 'Tipo/Modelo de estufa'}
        self.entered_test_info = {}
        for i, (key, value) in enumerate(self.testinfo.items()):
            tk.Label(self, text=f"{value.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[key] = tk.Entry(self)
            self.entered_test_info[key].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field, label in self.testinfo.items():
            if field in data:
                self.entered_test_info[field].delete(0, tk.END)  # Borrar el contenido existente
                self.entered_test_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_test_info

class CommentsFrame(tk.LabelFrame): # Área de entrada de comentarios
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.comments = {'general_comments': 'Comentarios generales', 'high_power_comments': 'Comentarios alta potencia',
                         'medium_power_comments': 'Comentarios media potencia', 'low_power_comments': 'Comentarios baja potencia'}
        self.entered_comments = {}
        for i, (key, value) in enumerate(self.comments.items()):
            tk.Label(self, text=f"{value.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_comments[key] = tk.Text(self, height=6, width=25, wrap="word")
            self.entered_comments[key].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field, label in self.comments.items():
            if field in data:
                self.entered_comments[field].delete("1.0", tk.END)  # Borrar el contenido existente
                self.entered_comments[field].insert(tk.END, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_comments

class EnvironmentInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.enviroinfo = {'initial_air_temp': 'Temperatura del aire inicial' , 'initial_RH' : 'Humedad relativa inicial', 'initial_pressure' : 'Presión inicial', 'initial_wind_velocity' : 'Velocidad del viento inicial',
                           'final_air_temp' : 'Temperatura del aire final', 'final_RH' : 'Humedad relativa final', 'final_pressure' : 'Presión final', 'final_wind_velocity' : 'Velocidad del viento final',
                           'pot1_dry_mass' : 'Masa seca de la olla 1', 'pot2_dry_mass' : 'Masa seca de la olla 2', 'pot3_dry_mass' : 'Masa seca de la olla 3', 'pot4_dry_mass' : 'Masa seca de la olla 4'}
        self.envirounits = ['C', '%', 'in Hg', 'm/s', 'C', '%', 'in Hg', 'm/s', 'kg', 'kg', 'kg', 'kg']
        self.entered_enviro_info = {}
        self.entered_enviro_units = {}
        for i, (key, name) in enumerate(self.enviroinfo.items()):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_enviro_info[key] = tk.Entry(self)
            self.entered_enviro_info[key].grid(row=i, column=2)
            self.entered_enviro_units[key] = tk.Entry(self)
            self.entered_enviro_units[key].insert(0, self.envirounits[i])
            self.entered_enviro_units[key].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, range_errors: list):
        for name in self.enviroinfo:
            try:
                test = float(self.entered_enviro_info[name].get())
            except ValueError:
                if self.entered_enviro_info[name].get() != '': #If not blank, string was entered instead of number
                    float_errors.append(name)
                if (name == 'initial_air_temp' or name == 'initial_pressure') and 'final' not in name and \
                        'pot' not in name and self.entered_enviro_info[name].get() == '': #Inital temp and pressure require inputs
                    blank_errors.append(name)
                if 'pot' in name and '1' in name and self.entered_enviro_info[name].get() == '': #dry weight of pot 1 required
                    blank_errors.append(name)
        #RH should not be above 100
        try:
            test = float(self.entered_enviro_info['initial_RH'].get())
            if float(self.entered_enviro_info['initial_RH'].get()) > 100:
                range_errors.append('initial_RH')
        except:
            pass
        try:
            float(self.entered_enviro_info['final_RH'].get())
            if float(self.entered_enviro_info['final_RH'].get()) > 100:
                range_errors.append('final_RH')
        except:
            pass

        return float_errors, blank_errors, range_errors

    def check_imported_data(self, data: dict):
        for field in self.enviroinfo:
            if field in data:
                self.entered_enviro_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_enviro_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_enviro_info

    def get_units(self):
        return self.entered_enviro_units

class FuelInfoFrame(tk.LabelFrame): #Fuel info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.singlefuelinfo = {'fuel_type': 'Tipo de combustible','fuel_source': 'Fuente de combustible',
                               'fuel_dimensions': 'Dimensiones del combustible',
                               'fuel_mc': 'Contenido de humedad del combustible',
                               'fuel_higher_heating_value': 'Valor de calor superior del combustible',
                               'fuel_Cfrac_db': 'Fracción de carbono en base seca del combustible'}
        self.fuelunits = ['', '', 'cmxcmxcm', '%', 'kJ/kg', 'g/g']
        self.fuelinfo = {}
        self.number_of_fuels = 3
        start = 1
        self.entered_fuel_units = {}
        while start <= self.number_of_fuels:
            for i, (name, val) in enumerate(self.singlefuelinfo.items()):
                new_name = name + '_' + str(start)
                new_val = val + '_' + str(start)
                self.fuelinfo[new_name] = new_val
                self.entered_fuel_units[new_name] = tk.Entry(self)
                self.entered_fuel_units[new_name].insert(0, self.fuelunits[i])

            start += 1
        self.entered_fuel_info = {}
        for i, (name, val) in enumerate(self.fuelinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_fuel_info[name] = tk.Entry(self)
            self.entered_fuel_info[name].grid(row=i, column=2)
            self.entered_fuel_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, range_errors: list):
        self.fuel_2_values_entered = any(self.entered_fuel_info[name].get() != '' for name in self.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(self.entered_fuel_info[name].get() != '' for name in self.fuelinfo if '3' in name)

        for name in self.fuelinfo:
            try:
                test = float(self.entered_fuel_info[name].get())
            except ValueError:
                if ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name) and \
                        self.entered_fuel_info[name].get() != '':
                    float_errors.append(name)
                if ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '1' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)
                if self.fuel_2_values_entered and ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '2' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)
                if self.fuel_3_values_entered and ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '3' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)

        start = 1
        while start <= self.number_of_fuels:
            try:
                HV = float(self.entered_fuel_info['fuel_higher_heating_value_' + str(start)].get())
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if (HV < 11000 or HV > 25000) and cfrac < 0.75:
                    range_errors.append('fuel_higher_heating_value_' + str(start))
            except:
                pass

            try:
                HV = float(self.entered_fuel_info['fuel_higher_heating_value_' + str(start)].get())
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if (HV < 25000 or HV > 33500) and cfrac > 0.75:
                    range_errors.append('fuel_higher_heating_value_' + str(start))
            except:
                pass

            try:
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if cfrac > 1:
                    range_errors.append('fuel_Cfrac_db_' + str(start))
            except:
                pass

            start += 1

        return float_errors, blank_errors, range_errors

    def check_imported_data(self, data: dict):
        for field in self.fuelinfo:
            if field in data:
                self.entered_fuel_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_fuel_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_fuel_info

    def get_units(self):
        return self.entered_fuel_units

class HPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.hpstartinfo = {'start_time_hp': 'Hora de inicio (ap)',
                            'initial_fuel_mass_1_hp': 'Masa inicial de combustible 1 ap',
                            'initial_fuel_mass_2_hp': 'Masa inicial de combustible 2 ap',
                            'initial_fuel_mass_3_hp': 'Masa inicial de combustible 3 ap',
                            'initial_water_temp_pot1_hp': 'Temperatura inicial del agua ap',
                            'initial_water_temp_pot2_hp': 'Temperatura inicial del agua ap',
                            'initial_water_temp_pot3_hp': 'Temperatura inicial del agua (olla 3, ap)',
                            'initial_water_temp_pot4_hp': 'Temperatura inicial del agua (olla 4, ap)',
                            'initial_pot1_mass_hp': 'Masa inicial de la olla 1 (ap)',
                            'initial_pot2_mass_hp': 'Masa inicial de la olla 2 (ap)',
                            'initial_pot3_mass_hp': 'Masa inicial de la olla 3 (ap)',
                            'initial_pot4_mass_hp': 'Masa inicial de la olla 4 (ap)',
                            'fire_start_material_hp': 'Material de inicio del fuego (ap)',
                            'boil_time_hp': 'Tiempo de ebullición (ap)'}
        self.hpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', '', 'hh:mm:ss']
        self.entered_hpstart_info = {}
        self.entered_hpstart_units = {}
        for i, (name, val) in enumerate(self.hpstartinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_hpstart_info[name] = tk.Entry(self)
            self.entered_hpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_hp' or name == 'initial_fuel_mass_3_hp':
                self.entered_hpstart_info[name].insert(0, 0) #default of 0
            self.entered_hpstart_units[name] = tk.Entry(self)
            self.entered_hpstart_units[name].insert(0, self.hpstartunits[i])
            self.entered_hpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.hpend_info_frame = HPendInfoFrame(self, "HP End")
        self.entered_hpend_info = self.hpend_info_frame.get_data()
        hpstart_values_entered = any(self.entered_hpstart_info[name].get() != '' for name in self.hpstartinfo)
        #timeformat = 0
        if hpstart_values_entered:
            for name in self.hpstartinfo:
                try:
                    float(self.entered_hpstart_info[name].get())
                except ValueError:
                    if self.entered_hpstart_info[name].get() != '' and 'time' not in name and name != 'fire_start_material_hp':
                        float_errors.append(name)
                    if'time' not in name and name != 'fire_start_material_hp' and '1' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and name != 'fire_start_material_hp' and '2' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and name != 'fire_start_material_hp' and '3' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_hp'
                final_mass_name = f'final_pot{i}_mass_hp'
                try:
                    initial_mass = float(self.entered_hpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_hpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_hp')
                except ValueError:
                    pass

            if len(self.entered_hpstart_info['start_time_hp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_hp')
            #else:
                #timeformat = len(self.entered_hpstart_info['start_time_hp'].get())

            if len(self.entered_hpstart_info['boil_time_hp'].get()) not in (8, 17, 0):
                print(len(self.entered_hpstart_info['boil_time_hp'].get()))
                format_errors.append('boil_time_hp')

            return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.hpstartinfo:
            if field in data:
                self.entered_hpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_hpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_hpstart_info

    def get_units(self):
        return self.entered_hpstart_units

class HPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.hpendinfo = {'end_time_hp': 'Hora de finalización (ap)',
                          'final_fuel_mass_1_hp': 'Masa final de combustible 1 (ap)',
                          'final_fuel_mass_2_hp': 'Masa final de combustible 2 (ap)',
                          'final_fuel_mass_3_hp': 'Masa final de combustible 3 (ap)',
                          'max_water_temp_pot1_hp': 'Temperatura máxima del agua (olla 1, ap)',
                          'max_water_temp_pot2_hp': 'Temperatura máxima del agua (olla 2, ap)',
                          'max_water_temp_pot3_hp': 'Temperatura máxima del agua (olla 3, ap)',
                          'max_water_temp_pot4_hp': 'Temperatura máxima del agua (olla 4, ap)',
                          'end_water_temp_pot1_hp': 'Temperatura final del agua (olla 1, ap)',
                          'final_pot1_mass_hp': 'Masa final de la olla 1 (ap)',
                          'final_pot2_mass_hp': 'Masa final de la olla 2 (ap)',
                          'final_pot3_mass_hp': 'Masa final de la olla 3 (ap)',
                          'final_pot4_mass_hp': 'Masa final de la olla 4 (ap)'}
        self.hpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_hpend_info = {}
        self.entered_hpend_units = {}
        for i, (name, val) in enumerate(self.hpendinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_hpend_info[name] = tk.Entry(self)
            self.entered_hpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_hp' or name == 'final_fuel_mass_3_hp':
                self.entered_hpend_info[name].insert(0, 0) #default of 0
            self.entered_hpend_units[name] = tk.Entry(self)
            self.entered_hpend_units[name].insert(0, self.hpendunits[i])
            self.entered_hpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        hpend_values_entered = any(self.entered_hpend_info[name].get() != '' for name in self.hpendinfo)
        if hpend_values_entered:
            for name in self.hpendinfo:
                try:
                    float(self.entered_hpend_info[name].get())
                except ValueError:
                    if self.entered_hpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)

            #if timeformat == 0:
            if len(self.entered_hpend_info['end_time_hp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_hp')
            #else:
                #timeformat = len(self.entered_hpend_info['end_time_hp'].get())
            #else:
            #if len(self.entered_hpend_info['end_time_hp'].get()) != (8 or 17 or 0):
                #format_errors.append('end_time_hp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.hpendinfo:
            if field in data:
                self.entered_hpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_hpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_hpend_info

    def get_units(self):
        return self.entered_hpend_units

class MPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.mpstartinfo = {'start_time_mp': 'Hora de inicio (mp)',
                            'initial_fuel_mass_1_mp': 'Masa inicial de combustible 1 mp',
                            'initial_fuel_mass_2_mp': 'Masa inicial de combustible 2 mp',
                            'initial_fuel_mass_3_mp': 'Masa inicial de combustible 3 mp',
                            'initial_water_temp_pot1_mp': 'Temperatura inicial del agua mp',
                            'initial_water_temp_pot2_mp': 'Temperatura inicial del agua mp',
                            'initial_water_temp_pot3_mp': 'Temperatura inicial del agua (olla 3, mp)',
                            'initial_water_temp_pot4_mp': 'Temperatura inicial del agua (olla 4, mp)',
                            'initial_pot1_mass_mp': 'Masa inicial de la olla 1 (mp)',
                            'initial_pot2_mass_mp': 'Masa inicial de la olla 2 (mp)',
                            'initial_pot3_mass_mp': 'Masa inicial de la olla 3 (mp)',
                            'initial_pot4_mass_mp': 'Masa inicial de la olla 4 (mp)',
                            'fire_start_material_mp': 'Material de inicio del fuego (mp)',
                            'boil_time_mp': 'Tiempo de ebullición (mp)'}
        self.mpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', '', 'hh:mm:ss']
        self.entered_mpstart_info = {}
        self.entered_mpstart_units = {}
        for i, (name, val) in enumerate(self.mpstartinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_mpstart_info[name] = tk.Entry(self)
            self.entered_mpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_mp' or name == 'initial_fuel_mass_3_mp':
                self.entered_mpstart_info[name].insert(0, 0) #default of 0
            self.entered_mpstart_units[name] = tk.Entry(self)
            self.entered_mpstart_units[name].insert(0, self.mpstartunits[i])
            self.entered_mpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.mpend_info_frame = MPendInfoFrame(self, "MP End")
        self.entered_mpend_info = self.mpend_info_frame.get_data()
        mpstart_values_entered = any(self.entered_mpstart_info[name].get() != '' for name in self.mpstartinfo)
        if mpstart_values_entered:
            for name in self.mpstartinfo:
                try:
                    float(self.entered_mpstart_info[name].get())
                except ValueError:
                    if self.entered_mpstart_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_mp'
                final_mass_name = f'final_pot{i}_mass_mp'
                try:
                    initial_mass = float(self.entered_mpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_mpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_mp')
                except ValueError:
                    pass

            #if self.timeformat == 0:
            if len(self.entered_mpstart_info['start_time_mp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_mp')
            #else:
                #self.timeformat = len(self.entered_mpstart_info['start_time_mp'].get())
            #else:
                #if len(self.entered_mpstart_info['start_time_mp'].get()) != (self.timeformat or 0):
                    #format_errors.append('start_time_mp')

            if (len(self.entered_mpstart_info['boil_time_mp'].get()) not in (8, 17, 0)) :
                format_errors.append('boil_time_mp')

        return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.mpstartinfo:
            if field in data:
                self.entered_mpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_mpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_mpstart_info

    def get_units(self):
        return self.entered_mpstart_units

class MPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.mpendinfo = {'end_time_mp': 'Hora de finalización (mp)',
                          'final_fuel_mass_1_mp': 'Masa final de combustible 1 (mp)',
                          'final_fuel_mass_2_mp': 'Masa final de combustible 2 (mp)',
                          'final_fuel_mass_3_mp': 'Masa final de combustible 3 (mp)',
                          'max_water_temp_pot1_mp': 'Temperatura máxima del agua (olla 1, mp)',
                          'max_water_temp_pot2_mp': 'Temperatura máxima del agua (olla 2, mp)',
                          'max_water_temp_pot3_mp': 'Temperatura máxima del agua (olla 3, mp)',
                          'max_water_temp_pot4_mp': 'Temperatura máxima del agua (olla 4, mp)',
                          'end_water_temp_pot1_mp': 'Temperatura final del agua (olla 1, mp)',
                          'final_pot1_mass_mp': 'Masa final de la olla 1 (mp)',
                          'final_pot2_mass_mp': 'Masa final de la olla 2 (mp)',
                          'final_pot3_mass_mp': 'Masa final de la olla 3 (mp)',
                          'final_pot4_mass_mp': 'Masa final de la olla 4 (mp)'}
        self.mpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_mpend_info = {}
        self.entered_mpend_units = {}
        for i, (name, val) in enumerate(self.mpendinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_mpend_info[name] = tk.Entry(self)
            self.entered_mpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_mp' or name == 'final_fuel_mass_3_mp':
                self.entered_mpend_info[name].insert(0, 0) #default of 0
            self.entered_mpend_units[name] = tk.Entry(self)
            self.entered_mpend_units[name].insert(0, self.mpendunits[i])
            self.entered_mpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        mpend_values_entered = any(self.entered_mpend_info[name].get() != '' for name in self.mpendinfo)
        if mpend_values_entered:
            for name in self.mpendinfo:
                try:
                    float(self.entered_mpend_info[name].get())
                except ValueError:
                    if self.entered_mpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and \
                            self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and \
                            self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)

            #if self.timeformat == 0:
            if len(self.entered_mpend_info['end_time_mp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_mp')
            #else:
                #self.timeformat = len(self.entered_mpend_info['end_time_mp'].get())
            #else:
                #if len(self.entered_mpend_info['end_time_mp'].get()) != (self.timeformat or 0):
                    #format_errors.append('end_time_mp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.mpendinfo:
            if field in data:
                self.entered_mpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_mpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_mpend_info

    def get_units(self):
        return self.entered_mpend_units

class LPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.lpstartinfo = {'start_time_lp': 'Hora de inicio (bp)',
                            'initial_fuel_mass_1_lp': 'Masa inicial de combustible 1 bp',
                            'initial_fuel_mass_2_lp': 'Masa inicial de combustible 2 bp',
                            'initial_fuel_mass_3_lp': 'Masa inicial de combustible 3 bp',
                            'initial_water_temp_pot1_lp': 'Temperatura inicial del agua bp',
                            'initial_water_temp_pot2_lp': 'Temperatura inicial del agua bp',
                            'initial_water_temp_pot3_lp': 'Temperatura inicial del agua (olla 3, bp)',
                            'initial_water_temp_pot4_lp': 'Temperatura inicial del agua (olla 4, bp)',
                            'initial_pot1_mass_lp': 'Masa inicial de la olla 1 (bp)',
                            'initial_pot2_mass_lp': 'Masa inicial de la olla 2 (bp)',
                            'initial_pot3_mass_lp': 'Masa inicial de la olla 3 (bp)',
                            'initial_pot4_mass_lp': 'Masa inicial de la olla 4 (bp)',
                            'fire_start_material_lp': 'Material de inicio del fuego (bp)',
                            'boil_time_lp': 'Tiempo de ebullición (bp)'}
        self.lpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', '', 'hh:mm:ss']
        self.entered_lpstart_info = {}
        self.entered_lpstart_units = {}
        for i, (name, val) in enumerate(self.lpstartinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_lpstart_info[name] = tk.Entry(self)
            self.entered_lpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_lp' or name == 'initial_fuel_mass_3_lp':
                self.entered_lpstart_info[name].insert(0, 0) #default of 0
            self.entered_lpstart_units[name] = tk.Entry(self)
            self.entered_lpstart_units[name].insert(0, self.lpstartunits[i])
            self.entered_lpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.lpend_info_frame = LPendInfoFrame(self, "LP End")
        self.entered_lpend_info = self.lpend_info_frame.get_data()
        lpstart_values_entered = any(self.entered_lpstart_info[name].get() != '' for name in self.lpstartinfo)
        if lpstart_values_entered:
            for name in self.lpstartinfo:
                try:
                    float(self.entered_lpstart_info[name].get())
                except ValueError:
                    if self.entered_lpstart_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_lp'
                final_mass_name = f'final_pot{i}_mass_lp'
                try:
                    initial_mass = float(self.entered_lpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_lpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_mp')
                except ValueError:
                    pass

            #if self.timeformat == 0:
            if len(self.entered_lpstart_info['start_time_lp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_lp')
            #else:
                #self.timeformat = len(self.entered_lpstart_info['start_time_lp'].get())
            #else:
                #if len(self.entered_lpstart_info['start_time_lp'].get()) != (self.timeformat or 0):
                    #format_errors.append('start_time_lp')

            if (len(self.entered_lpstart_info['boil_time_lp'].get()) not in (8, 17, 0)):
                format_errors.append('boil_time_lp')

        return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.lpstartinfo:
            if field in data:
                self.entered_lpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_lpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_lpstart_info

    def get_units(self):
        return self.entered_lpstart_units

class LPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.lpendinfo = {'end_time_lp': 'Hora de finalización (bp)',
                          'final_fuel_mass_1_lp': 'Masa final de combustible 1 (bp)',
                          'final_fuel_mass_2_lp': 'Masa final de combustible 2 (bp)',
                          'final_fuel_mass_3_lp': 'Masa final de combustible 3 (bp)',
                          'max_water_temp_pot1_lp': 'Temperatura máxima del agua (olla 1, bp)',
                          'max_water_temp_pot2_lp': 'Temperatura máxima del agua (olla 2, bp)',
                          'max_water_temp_pot3_lp': 'Temperatura máxima del agua (olla 3, bp)',
                          'max_water_temp_pot4_lp': 'Temperatura máxima del agua (olla 4, bp)',
                          'end_water_temp_pot1_lp': 'Temperatura final del agua (olla 1, bp)',
                          'final_pot1_mass_lp': 'Masa final de la olla 1 (bp)',
                          'final_pot2_mass_lp': 'Masa final de la olla 2 (bp)',
                          'final_pot3_mass_lp': 'Masa final de la olla 3 (bp)',
                          'final_pot4_mass_lp': 'Masa final de la olla 4 (bp)'}
        self.lpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_lpend_info = {}
        self.entered_lpend_units = {}
        for i, (name, val) in enumerate(self.lpendinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_lpend_info[name] = tk.Entry(self)
            self.entered_lpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_lp' or name == 'final_fuel_mass_3_lp':
                self.entered_lpend_info[name].insert(0, 0) #default of 0
            self.entered_lpend_units[name] = tk.Entry(self)
            self.entered_lpend_units[name].insert(0, self.lpendunits[i])
            self.entered_lpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        lpend_values_entered = any(self.entered_lpend_info[name].get() != '' for name in self.lpendinfo)
        if lpend_values_entered:
            for name in self.lpendinfo:
                try:
                    test = float(self.entered_lpend_info[name].get())
                except ValueError:
                    if self.entered_lpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and \
                            self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and \
                            self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)

            #if self.timeformat == 0:
            if len(self.entered_lpend_info['end_time_lp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_lp')
            #else:
                #self.timeformat = len(self.entered_lpend_info['end_time_lp'].get())
            #else:
                #if len(self.entered_lpend_info['end_time_lp'].get()) != (self.timeformat or 0):
                    #format_errors.append('end_time_lp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.lpendinfo:
            if field in data:
                self.entered_lpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_lpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_lpend_info

    def get_units(self):
        return self.entered_lpend_units

class WeightPerformanceFrame(tk.LabelFrame): #Test info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.testinfo = {'weight_hp' : 'Peso ap', 'weight_mp' : 'Peso mp', 'weight_lp' : 'Peso bp',
                         'weight_total' : 'Peso total'}
        self.entered_test_info = {}
        for i, (name, val) in enumerate(self.testinfo.items()):
            tk.Label(self, text=f"{val.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self)
            self.entered_test_info[name].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field in self.testinfo:
            if field in data:
                self.entered_test_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_test_info[field].insert(0, data.pop(field, ""))

        return data
    def get_data(self):
        return self.entered_test_info

class ExtraTestInputsFrame(tk.LabelFrame):
    def __init__(self, root, text, new_vars: dict, units: dict):
        super().__init__(root, text=text, padx=10, pady=10)
        self.entered_test_info = {}
        self.entered_test_units = {}
        for i, name in enumerate(new_vars):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self)
            self.entered_test_info[name].insert(0, new_vars[name])
            self.entered_test_info[name].grid(row=i, column=2)
            self.entered_test_units[name] = tk.Entry(self)
            self.entered_test_units[name].insert(0, units[name])
            self.entered_test_units[name].grid(row=i, column=3)

    def get_data(self):
        return self.entered_test_info

    def get_units(self):
        return self.entered_test_units


if __name__ == "__main__":
    root = tk.Tk()
    version = '0.0'
    root.title("App L1. Version: " + version)
    root.iconbitmap("ARC-Logo.ico")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataInput(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()

