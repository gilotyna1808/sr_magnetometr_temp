#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 09:20:27 2022

@author: daniel
"""

import serial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def open_file(config):
    """
    Funkcja otwierająca strumień do pliku.

    Parameters
    ----------
    config : ConfigParser
        Zmienna z danymi konfiguracyjnymi.

    Returns
    -------
    file : TextIOWrapper
        Otwarty stream do pliku.

    """
    file = None
    now = datetime.now()
    now = now.strftime("%d_%m_%Y_%H_%M_%S")
    name = 'data'
    path = config.load_value_from_config_str('file_dir', 'data')
    file = open(f"{path}/{name}_{now}.csv", "w+", encoding="utf-8")
    file.write("Data,Czas,Time_Stamp,X,Y,Z,M1,M2,G\n")
    file.flush()
    return file

def close_file(file):
    """
    Funkcja zamykająca stream do pliku.

    Parameters
    ----------
    file : TextIOWrapper
        Otwarty stream do pliku.

    """
    if file is not None:
        file.close()
    file = None
    return file

def write_to_file(file, data):
    """
    Funkcja zapisująca informacje do pliku

    Parameters
    ----------
    file : TextIOWrapper
        Otwarty stream do pliku.
    data : list
        Lista wyników do zapisania.

    """
    file.write("".join(str(x) for x in data if x is not None))
    file.flush()

def convert(txt):
    """
    Funkcja przeksztalcajaca format odczytanej informacji na uzyteczny format.

    Parameters
    ----------
    txt : str
        Odczytana informacja.

    Returns
    -------
    str
        Informacja po przekształceniu.

    """
    values = None
    if(txt.find("$") != -1):
        try:
            txt, check_sum = txt.split('*')
            tab = txt.split(',')
            temp  = check_checksum8xor(txt[1:], check_sum)
            if temp is False:  
                values = None
            else:
                now = datetime.now()
                now_txt = now.strftime("%d/%m/%Y,%H:%M:%S.%f")[:-3]
                values = ""
                tab[4] = round(float(tab[4])*10e8,4)
                tab[5] = round(float(tab[5])*10e8,4)
                tab[6] = round(float(tab[6])*10e8,4)
                values = f"{now_txt},{tab[1]},{tab[4]},{tab[5]},{tab[6]},,,\n"
                return values
        except:
            values = None
    return ""

def check_checksum8xor(value, check_sum):
    """
    Funkcja zwracająca informacje czy suma kontolna 
    danej informacji zgadza sie z odczytaną

    Parameters
    ----------
    value : str
        Odczytana informacja.
    check_sum : str
        Odczytana suma kontrolna.

    Returns
    -------
    bool
        Informacja czy odczytana suma kontrolna odpowiada prawdziwej.

    """
    value = value
    checksum = 0
    for el in value:
        checksum ^= ord(el)
    if(hex(checksum) == hex(int(check_sum,16))):
        return True
    return False

def get_tmi(x:float,y:float,z:float):
    """
    Funkcja zwracająca moduł pierwiastka z sumy kwadratów składowych.

    Parameters
    ----------
    x : float
        Składowa x.
    y : float
        Składowa y.
    z : float
        Składowa z.

    Returns
    -------
    float
        Moduł pierwiastka z sumy kwadratów składowych.

    """
    return round((pow((pow(x,2)+pow(y,2)+pow(z,2)),1/2)),4)

def draw_plot_from_csv(file, axis):
    """
    Funkcja rysująca wykres z danych pobranych z pliku.

    Parameters
    ----------
    file : str
        Scieżka do pliku.
    axis : str
        Skladowa do narysowania.

    """
    df = pd.read_csv(file)
    plt.figure(figsize=(10,5), dpi=100)
    plt.plot(df[axis],'-', label=axis)
    plt.title(file)
    plt.legend().set_visible(True)
    plt.show()

def draw_plots_from_csv(file, axiss):
    """
    Funkcja rysująca wykres z danych pobranych z pliku.

    Parameters
    ----------
    file : str
        Scieżka do pliku.
    axis : str
        Skladowa do narysowania.

    """
    df = pd.read_csv(file)
    for axis in axiss:
        plt.figure(figsize=(10,5), dpi=100)
        plt.plot(df[axis],'-', label=axis)
        plt.title(file)
        plt.legend().set_visible(True)
        plt.show()

class sensys_fgm3d_uwd:
    """
    Klasa przechowująca dane do podłączenia oraz metody do zarządzania komunikacją.    

    Parameters
    ----------
    port : str, optional
        Port, na krórym znajudje sie urzadzenie. The default is None.
    boundrate : int, optional
        Boundrate. The default is None.
    timeout : int, optional
        Czas oczekiwania na odpowiedz [s]. The default is None.
    
    ----------
    
    Methods
    ----------
    load_connection_data_from_config_file(config):
        Załaduj dane z pliku konfiguracyjnego.
    connect():
        Podłącz sie do urządzenia.
    close_connection():
        Zamknij połączenie.
    get_data():
        Odbierz dane pomiarowe.
    is_open():
        Sprawdz czy połączanie jest otwarte
    check_conection():
        Sprawdz czy połączenie jest ustanowione
    send_message():
        Wyślij polecenie
    """

    def __init__(self, port:str=None, boundrate:int=None, timeout:int=None):
        # Conection variables
        self.port = port
        self.boundrate = boundrate
        self.timeout = timeout
        self.conection = None
        
        #functions
        self.np_convert = np.vectorize(convert)
        
        #
        self.last_message = ''
    
    def load_connection_data_from_config_file(self, config):
        """
        Metoda ładująca konfiguracje z pliku config.

        Parameters
        ----------
        config : ConfigParser
            Zmienna z danymi konfiguracyjnymi.


        """
        self.port = config.load_value_from_config_str('rs232_settings','port')
        self.boundrate = config.load_value_from_config_int('rs232_settings','baudrate')
        self.timeout = config.load_value_from_config_int('rs232_settings','timeout')
    
    def connect(self):
        """
        Metoda służąca do podłączenia sie do urządzenia.

        Raises
        ------
        ConnectionError
            Wyjątek gdy połączenie jest juz ustanowione.


        """
        if(self.conection is not None):
            raise ConnectionError("Connection already exist")
        ser = serial.Serial()
        ser.port = self.port
        ser.baudrate = self.boundrate
        ser.timeout = self.timeout
        ser.open()
        self.conection = ser
    
    def close_connection(self):
        """
        Metoda służąca do zamknięcia połączenia.

        Raises
        ------
        ConnectionError
            Wyjątek gdy połączenie nie było ustanowione.


        """
        if(self.conection is None):
            raise ConnectionError("Connection doesn't exist")
        else:
            temp = self.conection
            self.connect = None
            if(temp.isOpen()):
                temp.close()
            else:
                raise ConnectionError("Connection is not open")
    
    def get_data(self):
        """
        Metoda zwracająca listę z obrobionymi pomiarami.

        Returns
        -------
        temp_data : list
            Lista z odczytanymi pomiarami.

        """
        #Sprawdz czy polaczenie jest ustanowione
        self.check_conection()
        #Pobierz wszystkie dane z buforu
        data_from_sensys = self.conection.read_all().decode('utf-8', errors='ignore').rstrip().replace('\x00','')
        #Dodaj na poczatek wiadomosci poprzedni niekompletny pomiar
        data_from_sensys = self.last_message + data_from_sensys
        #Rozdiel pomiary na tablice
        data_from_sensys = data_from_sensys.split('\r\n')
        if(len(data_from_sensys)>1):
            self.last_message = data_from_sensys[-1]
            data_from_sensys = data_from_sensys[:-1]
        temp_data = self.np_convert(data_from_sensys)
        return temp_data
    
    def send_message(self, message:str):
        """
        Metoda wysłająca polecenie do urzadzenia

        Parameters
        ----------
        message : str
            Tresc polecenia.


        """
        self.check_conection()
        message = str.encode(message+'\r\n')
        self.conection.write(message)
    
    def is_open(self):
        """
        Metoda zwracająca informacje czy połączenie jest otwarte

        Returns
        -------
        bool
            Informacja czy połączenie jest ustanowione.

        """
        if self.conection is None:
            return False
        return self.conection.isOpen()
    
    def check_conection(self):
        """
        Metoda wyrzucająca wyjątek gdy połączenie nie jest ustanowione

        Raises
        ------
        ConnectionError
            Brak połączenia.

        """
        if self.conection is None:
            raise ConnectionError("Connection doesn't exist")
        if self.is_open() is not True:
            raise ConnectionError("Connection is not open")
