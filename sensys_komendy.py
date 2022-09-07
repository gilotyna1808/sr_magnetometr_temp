#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 11:31:44 2022

@author: daniel
"""

import serial
from sensys_config import sensys_config
import time

def _help():
    """
    Funkcja wysyłająca polecenie HELP
    """
    send_message(serial_conection,"HELP")

def sensys_connect(config):
    """
    Funkcja ustanawiająca połączenie z urządzeniem.

    Parameters
    ----------
    config : configparser
        Konfiguracja połączenia.

    Returns
    -------
    ser : serial
        Zmienna z połczeniem do urządzenia.

    """
    ser = serial.Serial()
    ser.port = config.load_value_from_config_str('rs232_settings','port')
    ser.baudrate = config.load_value_from_config_int('rs232_settings','baudrate')
    ser.timeout = config.load_value_from_config_int('rs232_settings','timeout')
    ser.open()
    return ser

def send_message(serial_conection, message):
    """
    Funkcja wysyłająca polecenie do urządzenia

    Parameters
    ----------
    serial_conection : serial
        Zmienna z ustanowionym połczeniem do urządzenia.
    message : str
        Polecenie do urządzenia.
    """
    message = str.encode(message+'\r\n')
    serial_conection.write(message)

def read_serial(serial):
    """
    Funkcja odczytująca informacje z urządzenia

    Parameters
    ----------
    serial : serial
        Zmienna z ustanowionym połczeniem do urządzenia.
    """
    time.sleep(0.5)
    data_from_sensys = serial_conection.read_all().decode('utf-8').rstrip().replace('\x00','')
    print(data_from_sensys)

if __name__ == '__main__':
    config = sensys_config(3)
    serial_conection = sensys_connect(config)
    send_message(serial_conection,"STOP")
    read_serial(serial_conection, config)
    while(True):
        com = input()
        if(com == '/?' or com == 'help' or com =="HELP"):
            _help()
        elif(com == 'quit' or com == 'q'):
            break
        else:
            send_message(serial_conection, com)
        read_serial(serial_conection, config)