#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 11:26:58 2022

@author: daniel
"""

import serial
from datetime import datetime
from sensys_config import sensys_config
import time
import numpy as np

def sensys_connect(config):
    ser = serial.Serial()
    ser.port = config.load_value_from_config_str('rs232_settings','port')
    ser.baudrate = config.load_value_from_config_int('rs232_settings','baudrate')
    ser.timeout = config.load_value_from_config_int('rs232_settings','timeout')
    ser.open()
    return ser


def check_checksum(value, check_sum):
    value = value[1:]
    checksum = 0
    for el in value:
        checksum ^= ord(el)
    if(hex(checksum) == hex(int(check_sum,16))):
        return True
    return False

def open_file(config):
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
    if file is not None:
        file.close()
    file = None
    return file

def write_to_file(file, data):
    global a
    a = data
    file.write("".join(str(x) for x in data if x is not None))
    file.flush()

def convert(txt):
    values = None
    if(txt.find("$") != -1):
        try:
            txt, check_sum = txt.split('*')
            tab = txt.split(',')
            temp  = check_checksum(txt, check_sum)
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

def measurement(config):
    serial_conection = sensys_connect(config)
    flag_silent = config.load_value_from_config_bool('program','silent')
    timer = config.load_value_from_config_int('program','time_to_new_file')
    data_file = open_file(config)
    data_buffor = []
    now = datetime.now().timestamp()
    time_last = now
    beg = ''
    np_convert = np.vectorize(convert)
    while(True):
        data_from_sensys = serial_conection.read_all().decode('utf-8').rstrip().replace('\x00','')
        data_from_sensys = beg+data_from_sensys
        data_from_sensys = data_from_sensys.split('\r\n')
        if(len(data_from_sensys)>1):
            beg = data_from_sensys[-1]
            data_from_sensys = data_from_sensys[:-1]
        temp_data = np_convert(data_from_sensys)
        if(flag_silent is False): print(temp_data)
        data_buffor.extend(temp_data)
        if(len(data_buffor)>1000):
            write_to_file(data_file, data_buffor)
            data_buffor = []
        now = datetime.now()
        if(now.timestamp() - time_last > timer):
            write_to_file(data_file, data_buffor)
            data_buffor = []
            data_file = close_file(data_file)
            data_file = open_file(config)
            time_last = now.timestamp()
        time.sleep(1)
    data_file = close_file(data_file)
    
if __name__ == '__main__':
    config = sensys_config()
    measurement(config)