#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 08:22:15 2022

@author: Daniel
"""

import wx
from threading import Thread
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from sensys import sensys_fgm3d_uwd, get_tmi, draw_plot_from_csv, write_to_file

class MainWindow(wx.Frame):
    """
    Metoda zmieniająca timestamp na czas działania urzadzenia.

    Parameters
    ----------
    config : ConfigParser
        Zmienna z danymi konfiguracyjnymi.
    
    ----------
    
    Controls
    ----------
    Pansels:
        panel:
            Panel głównego okna
        plot_panel:
            Panel, w którym rysowany będzie wykres
    Buttons:
        btn_connect:
            Przycisk inicjujący podłączenie do urządzenia.
        btn_start:
            Przycisk wysyłający polecenie rozpoczęcia pomiarów do urządzenia.
        btn_stop:
            Przycisk wysyłający polecenie zatrzymania pomiarów do urządzenia.
        btn_start_data:
            Przycisk rozpoczynający zapisywanie pomiarów do wybranego pliku.
        btn_stop_data
            Przycisk zatrzymujący zapisywanie pomiarów do wybranego pliku.
        btn_plot_x:
            Przycisk sterujący rysowaniem wykresu dla składowej X.
        btn_plot_y:
            Przycisk sterujący rysowaniem wykresu dla składowej Y.
        btn_plot_z:
            Przycisk sterujący rysowaniem wykresu dla składowej Z.
        btn_plot_m:
            Przycisk sterujący rysowaniem wykresu dla składowej M.
        btn_draw_from_csv:
            Przycisk sterujący rysowaniem wykresu dla wszystkich składowych
            po zakończeniu zapisywania pomiarów do pliku.
        btn_select_folder:
            Przycisk uruchamiający okno dialogowe z opcją
            wyboru katalogu do zapisywania danych.
        btn_send_comand:
            Przycisk wysyłający polecenie z pola tekstowego 'txt_write_comand'
            do urządzenia.
    TextBoxs:
        txt_data_file_name:
            Pole tekstowe przechowujące nazwę pliku z danymi.
        txt_data_folder_name:
            Pole tekstowe przechowujące scieżkę do katalogu z zapisywanymi danymi.
        txt_write_comand:
            Pole tekstowe przechowujące polecenie do urządzenia.
    ----------
    """
    def __init__(self, config):
        # Konstruktor
        super().__init__(parent=None, title='Sensys Program',size=(900,400))
        self.panel = wx.Panel(self)
        self.SetSize(wx.Size(900, 600))
        #Konfiguracja
        self.config = config
        self.log_directory = self.config.load_value_from_config_str('file_dir','Log')
        # Flagi
        self.serial_conection_create_flag = False
        self.plot_draw = {"X":False,"Y":True,"Z":False,"M":False}
        self.draw_plot_after_creating_csv = False
        # Zmienne
        self.sensys = sensys_fgm3d_uwd()
        # Wykres
        self.plot_x_axis = list(range(0,1000))
        self.plot_axis_values = {"X":[],"Y":[],"Z":[],"M":[]}
        self.sampling_num = 0
        # Przyciski
        self.btn_connect = wx.Button(self.panel, label='Polacz', pos=(5, 55))
        self.btn_start = wx.Button(self.panel, label='Start', pos=(100, 55))
        self.btn_stop = wx.Button(self.panel, label='Stop', pos=(195, 55))
        self.btn_start_data = wx.Button(self.panel, label='Zapis start', pos=(5, 0))
        self.btn_stop_data = wx.Button(self.panel, label='Zapis stop', pos=(100, 0))
        self.btn_plot_x = wx.Button(self.panel, label='X', pos=(350, 500))
        self.btn_plot_y = wx.Button(self.panel, label='Y', pos=(450, 500))
        self.btn_plot_z = wx.Button(self.panel, label='Z', pos=(550, 500))
        self.btn_plot_m = wx.Button(self.panel, label='TMI', pos=(650, 500))
        self.btn_draw_from_csv = wx.Button(self.panel, label='Rysuj wykres z csv', pos=(750, 500))
        self.btn_select_folder = wx.Button(self.panel, label='Select Folder', pos=(80, 450))
        self.btn_send_comand = wx.Button(self.panel, label='Wyślij Komende', pos=(110, 250))
        # Etykiety
        self.lbl_x1 = wx.StaticText(self.panel, label='X', pos=(5, 100))
        self.lbl_y1 = wx.StaticText(self.panel, label='Y', pos=(5, 120))
        self.lbl_z1 = wx.StaticText(self.panel, label='Z', pos=(5, 140))
        self.lbl_m1 = wx.StaticText(self.panel, label='M', pos=(5, 160))
        self.lbl_time = wx.StaticText(self.panel, label='Czas dzialania: ', pos=(5, 180))
        self.lbl_folder = wx.StaticText(self.panel, label='Folder:', pos=(5, 450))
        # Panele
        self.plot_panel = wx.Panel(self.panel,pos=(300, 0), size=(700,500))
        # Pola tekstowe
        self.txt_data_file_name = wx.TextCtrl(self.panel, pos=(195,0))
        self.txt_data_folder_name = wx.TextCtrl(self.panel, pos=(5,500), size=(300,20))
        self.txt_write_comand = wx.TextCtrl(self.panel, pos=(5,250), size=(100,20))
        # Watki
        self.thread_gui = None
        self.thread_plot_update = None
        self.thread_plot_draw = None
        self.thread_sensys = None
        # Bindy
        self.btn_connect.Bind(wx.EVT_BUTTON, self.btn_connect_on_click)
        self.btn_start.Bind(wx.EVT_BUTTON, self.btn_start_on_click)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.btn_stop_on_click) 
        self.btn_start_data.Bind(wx.EVT_BUTTON, self.btn_start_data_on_click)
        self.btn_stop_data.Bind(wx.EVT_BUTTON, self.btn_stop_data_on_click) 
        self.btn_plot_x.Bind(wx.EVT_BUTTON, self.toggle_plot("X"))
        self.btn_plot_y.Bind(wx.EVT_BUTTON, self.toggle_plot("Y"))
        self.btn_plot_z.Bind(wx.EVT_BUTTON, self.toggle_plot("Z"))
        self.btn_plot_m.Bind(wx.EVT_BUTTON, self.toggle_plot("M"))
        self.btn_draw_from_csv.Bind(wx.EVT_BUTTON, self.toggle_drawing_csv)
        self.btn_select_folder.Bind(wx.EVT_BUTTON, self.select_folder)
        self.btn_send_comand.Bind(wx.EVT_BUTTON, self.btn_send_comand_on_click)
        self.Bind(wx.EVT_CLOSE, self.close_window)
        
        self.Show()
        # Podlaczenie serial
        self.sensys.load_connection_data_from_config_file(self.config)
        # Inne
        self.button_color = [(255, 0, 0, 255),(0, 255, 0, 255)]
        self.btn_draw_from_csv.SetBackgroundColour(self.button_color[0])
        self.last_time = 0
        self.data_buffor = []
        now = datetime.now()
        now = now.strftime("%d_%m_%Y_%H_%M_%S")
        self.log_file = open(f"{self.log_directory}/log_{now}.txt", "w+", encoding="utf-8")
        self.data_file = None
        self.btn_stop_data.Disable()
        self.btn_send_comand.Disable()
        self.txt_data_folder_name.SetValue(f"{self.config.load_value_from_config_str('file_dir','Data')}")
        self.a = 0
    
    def btn_connect_on_click(self, event):
        """
        Metoda uruchamiająca watki z obsługą gui oraz ustanawiająca połączenie z 
        urządzeniem.
        """
        if (self.serial_conection_create_flag is not True):
            self.create_serial_conection()
            self.thread_gui = Thread(target=self.update_gui).start()
            self.thread_sensys = Thread(target=self.update).start()
            self.thread_plot_update = Thread(target=self.update_plot).start()
            self.thread_plot_draw = Thread(target=self.draw_plot).start()
        self.btn_connect.Disable()
        
        
    def update_gui(self):
        """
        Metoda odświeżająca zawartość gui.
        """
        try:
            while(True):
                try:
                    if(len(self.data_buffor)>1):
                        tab = self.data_buffor[-1]
                        m = get_tmi(tab[3],tab[4],tab[5])
                        time_stamp = self.time_stamp_to_time(tab[2])
                        wx.CallAfter(self.lbl_x1.SetLabel, f"X: {tab[3]}")
                        wx.CallAfter(self.lbl_y1.SetLabel, f"Y: {tab[4]}")
                        wx.CallAfter(self.lbl_z1.SetLabel, f"Z: {tab[5]}")
                        wx.CallAfter(self.lbl_m1.SetLabel, f"M: {m}")
                        wx.CallAfter(self.lbl_time.SetLabel, f" Czas dzialania: {time_stamp}")
                        time.sleep(0.1)
                except TypeError as e:
                    self.exception_handler(e,2,188,False)
        except Exception as e:
            self.exception_handler(e,3,190)
    
    def update_plot(self):
        """
        Metoda pobierająca dane z bufora danych i 
        tworząca bufor dla kazdej z skladowej pola magnetycznego.
        """
        try:
            while(True):
                try:
                    if(len(self.data_buffor)>2):
                        val = self.data_buffor[-1]
                        if(type(val) is float):
                            raise TypeError
                        values = {"X":val[3],"Y":val[4],"Z":val[5],
                                  "M":get_tmi(val[3], val[4], val[5])}
                        for axis in self.plot_axis_values:
                            self.plot_axis_values[axis].append(values[axis])
                        if(len(self.plot_axis_values["X"])>3000):
                            for axis in self.plot_axis_values:
                                self.plot_axis_values[axis] = self.plot_axis_values[axis][-1000:].copy()
                except TypeError as e:
                    self.exception_handler(e,2,207,True)
                time.sleep(0.02)
        except Exception as e:
            self.exception_handler(e,3,210)
    
    def draw_plot(self):
        """
        Metoda inicjalizujaca rysowanie wykresu w gui.
        """
        i = 0
        try:
            while(True):
                try:
                    if(len(self.plot_axis_values["X"])>10 and sum(self.plot_draw.values())>0):
                        dpi = 96
                        if(i==0):figure = Figure(figsize=(600/dpi,400/dpi), dpi=dpi)
                        else: figure.clear()
                        axes = figure.add_subplot(111)
                        i=1
                        for axis in self.plot_draw:
                            if(self.plot_draw[axis]):
                                values = self.plot_axis_values[axis]
                                if(len(values)<1000):
                                    axes.plot(self.plot_x_axis[:len(values)],values,label = f'os{axis}')
                                else:
                                    axes.plot(self.plot_x_axis,values[-1000:],label = f'os{axis}')
                        figure.legend().set_visible(True)
                        FigureCanvas(self.plot_panel, -1, figure)
                    time.sleep(0.5)
                except TypeError as e:
                    self.exception_handler(e,2,242,True)
        except Exception as e:
            self.exception_handler(e,3,244)
    
    def update(self):
        """
        Medtoda pobierająca informacje z urządzenia oraz zarządzająca buforem
        z danymi.
        """
        try:
            while(True):
                temp_data = self.sensys.get_data()
                tab = self.values_from_string_value(temp_data)
                # print(tab)
                write_to_file(self.log_file,temp_data)
                if(self.data_file != None):
                    write_to_file(self.data_file, temp_data)
                self.data_buffor.extend(tab)
                if(len(self.data_buffor)>1000):
                    self.data_buffor = self.data_buffor[-100:]
                time.sleep(0.025)
        except TypeError as e:
            self.exception_handler(e,1,264)
        except Exception as e:
            self.exception_handler(e,0,266)

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
    
    def time_stamp_to_time(self,time_stamp):
        """
        Metoda zmieniająca timestamp na czas działania urzadzenia.

        Parameters
        ----------
        time_stamp : str
            Timestamp liczony od czasu uruchomienia urządzenia.

        Returns
        -------
        str
            String w formacie Godziny:minuty:sekundy.milisekundy.

        """
        ms = int(time_stamp[:-3])
        s = int(int(ms/1000))
        m = int(int(s)/60)
        h = int(m/60)
        ms = ms%1000
        return f"{h}:{m%60}:{s%60}.{ms}"
    
    def create_serial_conection(self):
        """
        Metoda otwierająca połączenie z urządzeniem
        """
        self.sensys.connect()    
    
    def btn_stop_on_click(self, event):
        """
        Metoda wysyłająca polecenie Stop do urządzenia.
        """
        self.sensys.send_message("STOP")
        self.btn_send_comand.Enable()
    
    def btn_start_on_click(self, event):
        """
        Metoda wysyłająca polecenie Start do urządzenia.
        """
        self.sensys.send_message("START")
        self.btn_send_comand.Disable()
        
    def btn_send_comand_on_click(self, event):
        """
        Metoda wysylająca polecenie do urzadzenia.
        """
        self.sensys.send_message(self.txt_write_comand.Value)

    def btn_stop_data_on_click(self, event):
        """
        Metoda kończąca zapis pomiarów do pliku.
        """
        temp = self.data_file
        self.data_file = None
        temp.close()
        if(self.draw_plot_after_creating_csv):
            draw_plot_from_csv(temp.name,"X")
            draw_plot_from_csv(temp.name,"Y")
            draw_plot_from_csv(temp.name,"Z")
        self.btn_start_data.Enable()
        self.btn_stop_data.Disable()
    
    def btn_start_data_on_click(self, event):
        """
        Metoda otwerająca tworzaca plik, do którego zapisywane będą pomiary.
        """
        now = datetime.now()
        now = now.strftime("%d_%m_%Y_%H_%M_%S")
        name = 'data'
        if(self.txt_data_file_name.Value != ''):
            name = self.txt_data_file_name.Value
        self.data_file = open(f"{self.txt_data_folder_name.Value}/{name}_{now}.csv", "w+", encoding="utf-8")
        self.data_file.write("Data,Czas,Time_Stamp,X,Y,Z,M1,M2,G\n")
        self.btn_start_data.Disable()
        self.btn_stop_data.Enable()

    def close_window(self, event):
        """
        Metoda przerywajaca prace watkow, oraz zamykajaca okna.
        """
        if(self.sensys.is_open()):
            self.sensys.close_connection()
        if(self.thread_sensys != None):
            self.thread.kill()
        if(self.thread_plot_draw !=None):
            self.thread_plot_draw.kill()
        if(self.thread_plot_update != None):
            self.thread_plot_update.kill()
        if(self.thread_gui != None):
            self.thread.kill()
        self.Destroy()
    
    def toggle_plot(self,axis):
        """
        Metoda do wybierania skladowej do wyswietlania na osi.
        """
        def goingToHandler(event):
            self.plot_draw[axis] = not self.plot_draw[axis]
        return goingToHandler
        
    def toggle_drawing_csv(self,event):
        """
        Metoda sterująca rysowaniem wykresów po skończonych pomiarach.
        """
        if(self.draw_plot_after_creating_csv):
            self.draw_plot_after_creating_csv = False
            self.btn_draw_from_csv.SetBackgroundColour(self.button_color[0])
        else:
            self.draw_plot_after_creating_csv = True
            self.btn_draw_from_csv.SetBackgroundColour(self.button_color[1])

    def select_folder(self,event):
        """
        Metoda do obsługi okna dialogowego sluzacego do wybrania
        katalogu z zapisywanymi danymi

        """
        root = tk.Tk()
        root.withdraw()
        dir_path = filedialog.askdirectory()
        print(dir_path)
        wx.CallAfter(self.txt_data_folder_name.SetValue, dir_path) 

    def exception_handler(self, ex, tryb=0,line = 0, print_error=True):
        """
        Metoda służąca do obsługi wyjątków.
        
        Tryb:
            1:
                Wyjątek poza pętlą while, 
            2:
                Wyjątek w pętli while.
            3:
                Wyjątek poza pętlą while, zalecane wyłączenie programu.
            Inny:
                Nie znany wyjątek skutkuje wyłączeniem programu.
        
        Parameters
        ----------
        ex : Exceptionlike
            Przechwycony wyjątek.
        tryb : int, optional
            Zmienna sterujaca sposobem obsługi wyjątku. The default is 0.
        line : int, optional
            Linia, w której wystąpił wyjątek. The default is 0.
        print_error : bool, optional
            Flaga sterująca wypisywaniem wiadomosci wyjątku. The default is True.
        """
        if(print_error):print(f"[Error {tryb}]: {type(ex).__name__} {ex}\n[Line]: {line}")
        if(tryb == 1):
            pass
        elif(tryb == 2):
            pass
        elif(tryb == 3):
            pass
        else:    
            if(self.data_file is not None):
                self.data_file.close()
                self.data_file = None
            self.close_window("")