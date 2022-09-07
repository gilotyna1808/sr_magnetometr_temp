#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 08:35:40 2022

@author: daniel
"""

import configparser
from os.path import exists

class sensys_config():
    """
    Klasa przechowująca konfiguracje urządzenia.
    
    Parameters
    ----------
    config_type : int
        typ ładowanej konfiguracji.
        1 - Wersja Graficzna
        2 - Wersja Konsolowa
        3 - Wersja tylko do podlaczenia
        Inne - nieznane Sprawdz wszystko
    """
    def __init__(self, config_type:int = 0):
        self.config_file_path = 'config.ini'
        self.config = None
        self.config_type = config_type
        if(exists(self.config_file_path)):
            # self.create_config()
            self.load_config()
            self.check_config_file()
        else:
            raise Exception("Not implemented")
    
    def load_config(self):
        """
        Metoda wczytujaca plik konfiguracyjny
        """
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)
        self.config.sections()
        
    def load_value_from_config_str(self, section, attr):
        """
        Metoda pobierająca informacje z danej sekcji i atrybutu w postaci str.

        Parameters
        ----------
        section : str
            Sekcja, w której znajduje się atrybut.
        attr : str
            Wyszukiwany atrybut.

        Raises
        ------
        Exception
            Wyjatek gdy brakuje rządanej sekcji lub atrybutu.

        Returns
        -------
        str
            Wartosc dla wybranego atrybutu.

        """
        if(section in self.config):
            if(attr in self.config[section]):
                return self.config.get(section, attr)
        raise Exception(f"Nie ma attrybutu {section} {attr}")

    def load_value_from_config_int(self, section:str, attr:str):
        """
        Metoda pobierająca informacje z danej sekcji i atrybutu w postaci int.

        Parameters
        ----------
        section : str
            Sekcja, w której znajduje się atrybut.
        attr : str
            Wyszukiwany atrybut.

        Raises
        ------
        Exception
            Wyjatek gdy brakuje rządanej sekcji lub atrybutu.

        Returns
        -------
        int
            Wartosc dla wybranego atrybutu.

        """
        if(section in self.config):
            if(attr in self.config[section]):
                return self.config.getint(section, attr)
        raise Exception(f"Nie ma attrybutu {section} {attr}")
    
    def load_value_from_config_bool(self, section:str, attr:str):
        """
        Metoda pobierająca informacje z danej sekcji i atrybutu w postaci bool.

        Parameters
        ----------
        section : str
            Sekcja, w której znajduje się atrybut.
        attr : str
            Wyszukiwany atrybut.

        Raises
        ------
        Exception
            Wyjatek gdy brakuje rządanej sekcji lub atrybutu.

        Returns
        -------
        bool
            Wartosc dla wybranego atrybutu.

        """
        if(section in self.config):
            if(attr in self.config[section]):
                return self.config.getboolean(section, attr)
        raise Exception(f"Nie ma attrybutu {section} {attr}")
    
    def create_config(self):
        """
        Metoda tworząca domyślny plik konfiguracyjny.
        """
        config = configparser.ConfigParser()
        config['file_dir'] = {}
        config['file_dir']['Log'] = 'Log'
        config['file_dir']['Data'] = 'Data'
        config['program'] = {}
        config['program']['silent'] = 'False'
        config['program']['time_to_new_file'] = '600'
        config['rs232_settings'] = {}
        config['rs232_settings']['port'] = '/dev/ttyUSB0'
        config['rs232_settings']['baudrate'] = str(115200)
        config['rs232_settings']['timeout'] = str(1)
        with open(self.config_file_path, 'w') as configfile:
          config.write(configfile)
    
    def check_config_file(self):
        """
        Metoda sprawddzająca czy wczytany plik ma wszystkie wymagane pola.
        
        Raises
        ------
        Exception
            Wyjątek gdy jakiegos pola brakuje.
        """
        section_list = self.load_section_list()
        for section in section_list:
            if(self.check_if_section_exist(section) is False):
                raise Exception(f'Brak sekcji {section}')
            for attr in section_list[section]:
                if(self.check_if_attr_exist(section, attr) is False):
                    raise Exception(f'Brak atrybutu {attr} w sekcji {attr}')
    
    def load_section_list(self):
        section_list = {}
        section_list['rs232_settings'] = ['port','baudrate','timeout']
        if(self.config_type == 1):
            section_list['file_dir'] = ['Log','Data']
        elif(self.config_type == 2):
            section_list['file_dir'] = ['Data']
            section_list['program'] = ['silent','time_to_new_file']
        elif(self.config_type == 3):
            pass
        else:
            section_list['file_dir'] = ['Log','Data']
            section_list['program'] = ['silent','time_to_new_file']
        return section_list
    
    def save_config(self):
        """
        Metoda zapisująca obecną konfiguracje.
        """
        config = configparser.ConfigParser()
        for section in self.config:
            if section != 'DEFAULT':
              config[section] = {}
              for attr in self.config[section]:
                  config[section][attr] = self.config[section][attr]
        
        with open(self.config_file_path, 'w') as configfile:
          config.write(configfile)

    def check_if_section_exist(self, section:str):
        """
        Metoda sprawdzająca czy sekcja istnieje.

        Parameters
        ----------
        section : str
            Nazwa sprawdzanej sekcji.

        Returns
        -------
        bool
            Informacja czy sekcja istnieje.

        """
        return section in self.config
    
    def check_if_attr_exist(self, section:str, attr:str):
        """
        Metoda sprawdzająca czy atrybut w danej sekcji istnieje.

        Parameters
        ----------
        section : str
            Nazwa sekcji, w której szukamy atrybutu.
        attr : str
            Nazwa sprawdzanego atrybutu.

        Returns
        -------
        bool
            Informacja o tym czy atrybut istnieje.

        """
        return attr in self.config[section]