#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 08:22:15 2022

@author: Daniel
"""

import tkinter as tk
import serial
import multiprocessing as mp
from time import sleep
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QPushButton, QLabel, QTextEdit, QMessageBox
from threading import Thread
from datetime import datetime
from tkinter import filedialog
from ploter import Plotter
from sensys import sensys_fgm3d_uwd, get_tmi, draw_plots_from_csv, write_to_file

COLOR = {
    "green":"#00FF00",
    "red": "#FF0000",
    "back-red": "background-color:rgb(255,0,0)",
    "back-green": "background-color:rgb(0,255,0)"
}

MAX_BUFFOR_SIZE = 1000

class MainWidnow(QtWidgets.QMainWindow):
    def __init__(self, config):
        super().__init__()
        uic.loadUi('main_window.ui', self)
        self.show()
        #konfiguracja
        self.config = config
        self.log_directory = self.config.load_value_from_config_str('file_dir','Log')
        self.data_directory = self.config.load_value_from_config_str('file_dir','Data')
        # Wykres //TODO dodać sterowanie maksymalnym rozmiarem wykresu
        self.plot = Plotter(self)
        self.panel_chart.addWidget(self.plot)
        # Flagi
        self.serial_conection_create_flag = False
        self.plot_draw = {"X":False,"Y":True,"Z":False,"M":False}
        self.draw_plot_after_creating_csv = False
        # Urządzenie
        self.sensys = sensys_fgm3d_uwd()
        # Watki
        self.thread_gui = None
        self.thread_plot_update = None
        self.thread_plot_draw = None
        self.thread_sensys = None
        # Przyciski
        self.btn_connect.clicked.connect(self.btn_connect_clicked)
        self.btn_start_measurement.clicked.connect(self.btn_start_measurement_clicked)
        self.btn_stop_measurement.clicked.connect(self.btn_stop_measurement_clicked)
        self.btn_send_comand.clicked.connect(self.btn_send_comand_clicked)
        self.btn_record_start.clicked.connect(self.btn_record_start_clicked)
        self.btn_record_stop.clicked.connect(self.btn_record_stop_clicked)
        self.btn_select_dir.clicked.connect(self.btn_select_dir_clicked)
        self.btn_draw_chart_from_csv.clicked.connect(self.btn_draw_chart_from_csv_clicked)
        self.btn_draw_x_axis.clicked.connect(self.btn_axis_toggle_chart_clicked)
        self.btn_draw_y_axis.clicked.connect(self.btn_axis_toggle_chart_clicked)
        self.btn_draw_z_axis.clicked.connect(self.btn_axis_toggle_chart_clicked)
        self.btn_draw_m_axis.clicked.connect(self.btn_axis_toggle_chart_clicked)

        # Inne
        self.sensys.load_connection_data_from_config_file(self.config)
        now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        self.data_buffor = []
        self.log_file = open(f"{self.log_directory}/log_{now}.txt", "w+", encoding="utf-8")
        self.data_file = None


        self.btn_draw_chart_from_csv.setStyleSheet(COLOR["back-red"])
        self.txt_selected_dir.setPlainText(self.data_directory)

    def btn_connect_clicked(self):
        """
        Metoda uruchamiająca watki z obsługą gui oraz ustanawiająca połączenie z 
        urządzeniem.
        """
        if (self.serial_conection_create_flag is not True):
            try: 
                self.create_serial_conection()
                self.thread_sensys = Thread(target=self.update, daemon=True).start()
                self.thread_gui = Thread(target=self.update_gui, daemon=True).start()
                self.thread_plot_update = Thread(target=self.update_plot, daemon=True).start()
                self.btn_connect.setEnabled(False)
            except serial.serialutil.SerialException as ex:
                self.error_message_box(ex)
                print(ex)
    
    def btn_start_measurement_clicked(self):
        """
        Metoda wysyłająca polecenie Start do urządzenia.
        """
        self.sensys.send_message("START")
        self.btn_send_comand.setEnabled(False)
        self.txt_command.setEnabled(False)


    def btn_stop_measurement_clicked(self):
        """
        Metoda wysylająca polecenie do urzadzenia.
        """
        self.sensys.send_message("STOP")
        self.btn_send_comand.setEnabled(True)
        self.txt_command.setEnabled(True)
    
    def btn_send_comand_clicked(self):
        """
        Metoda wysylająca polecenie do urzadzenia.
        """
        self.sensys.send_message(self.txt_command.toPlainText())
    
    def btn_record_start_clicked(self):
        """
        Metoda otwerająca tworzaca plik, do którego zapisywane będą pomiary.
        """
        now = datetime.now()
        now = now.strftime("%d_%m_%Y_%H_%M_%S")
        name = 'data'
        if(self.txt_record_name.toPlainText() != ''):
            name = self.txt_record_name.toPlainText()
        self.data_file = open(f"{self.txt_selected_dir.toPlainText()}/{name}_{now}.csv", "w+", encoding="utf-8")
        self.data_file.write("Data,Czas,Time_Stamp,X,Y,Z,M1,M2,G\n")
        self.btn_record_start.setEnabled(False)
        self.btn_record_stop.setEnabled(True)

    def btn_record_stop_clicked(self):
        """
        Metoda kończąca zapis pomiarów do pliku.
        """
        temp = self.data_file
        self.data_file = None
        temp.close()
        if(self.draw_plot_after_creating_csv):
            Thread(target=draw_plots_from_csv, args=(temp.name,["X","Y","Z"])).start()
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)
    
    def btn_select_dir_clicked(self):
        """
        Metoda do obsługi okna dialogowego sluzacego do wybrania
        katalogu z zapisywanymi danymi

        """
        root = tk.Tk()
        root.withdraw()
        dir_path = filedialog.askdirectory()
        self.txt_selected_dir.setPlainText(dir_path)

    def btn_draw_chart_from_csv_clicked(self):
        """
        Metoda sterująca rysowaniem wykresów po skończonych pomiarach.
        """
        if(self.draw_plot_after_creating_csv):
            self.draw_plot_after_creating_csv = False
            self.btn_draw_chart_from_csv.setStyleSheet(COLOR["back-red"])
        else:
            self.draw_plot_after_creating_csv = True
            self.btn_draw_chart_from_csv.setStyleSheet(COLOR["back-green"])
    
    def btn_axis_toggle_chart_clicked(self):
        if self.sender().styleSheet() == "":
            self.sender().setStyleSheet(COLOR["back-green"])
        else:
            self.sender().setStyleSheet("")
    
    def update_plot(self):
        while True:
            if len(self.data_buffor) > 1:
                values = self.data_buffor[-1]
                value = {
                    "X": values[3],
                    "Y": values[4],
                    "Z": values[5],
                    "M": get_tmi(*values[3:6])
                }
                self.plot.update_values(value)
            sleep(0.1)
    
    def create_serial_conection(self):
        """
        Metoda otwierająca połączenie z urządzeniem
        """
        self.sensys.connect()
    
    def update(self):
        """
        Medtoda pobierająca informacje z urządzenia oraz zarządzająca buforem
        z danymi.
        """
        try:
            while(True):
                temp = self.sensys.get_data()
                tab = self.values_from_string_value(temp)
                write_to_file(self.log_file,temp)
                if self.data_file is not None:
                    write_to_file(self.data_file, temp)
                self.data_buffor.extend(tab)
                if len(self.data_buffor) > MAX_BUFFOR_SIZE:
                    self.data_buffor = self.data_buffor[-100:]
                sleep(0.025)
        except Exception as e:
            print(f"{e}")
    
    def values_from_string_value(self, string_values):
        """
        Metoda zmieniająca tablice z wartościami zapisanymi jako string, 
        na tablice z danymi na których można przprowadzać oblcizenia.

        Parameters
        ----------
        string_values : list
            Lista z danymi.

        Returns
        -------
        tab : list
            Lista z danymi.

        """
        tab = []
        for value in string_values:
            if value != "":
                val = value.split(",")[:-3]
                val[3] = float(val[3])
                val[4] = float(val[4])
                val[5] = float(val[5])
                tab.append(val)
        return tab
    
    def update_gui(self):
        while True:
            if len(self.data_buffor) > 1:
                values = self.data_buffor[-1]
                self.lbl_x_value.setText('{0:.2f}'.format(values[3]))
                self.lbl_y_value.setText('{0:.2f}'.format(values[4]))
                self.lbl_z_value.setText('{0:.2f}'.format(values[5]))
                self.lbl_m_value.setText('{0:.2f}'.format(get_tmi(*values[3:6])))
            sleep(0.1)
    
    def error_message_box(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"{message}")
        msg.setWindowTitle("Critical error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.show()
        msg.exec_()
        self.close_window()
    
    def close_window(self):
        """
        Metoda przerywajaca prace watkow, oraz zamykajaca okna.
        """
        if(self.sensys.is_open()):
            self.sensys.close_connection()
        self.close()