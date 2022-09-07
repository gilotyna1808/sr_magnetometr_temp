#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 11:26:58 2022

@author: daniel
"""

from datetime import datetime
from sensys_config import sensys_config
from sensys import sensys_fgm3d_uwd, open_file, close_file, write_to_file
import time

def measurement(config, sensys):
    print("")
    flag_silent = config.load_value_from_config_bool('program','silent')
    timer = config.load_value_from_config_int('program','time_to_new_file')
    data_file = open_file(config)
    data_buffor = []
    now = datetime.now().timestamp()
    time_last = now
    while(True):
        temp_data = sensys.get_data()
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
    config = sensys_config(2)
    sensys = sensys_fgm3d_uwd()
    sensys.load_connection_data_from_config_file(config)
    sensys.connect()
    measurement(config, sensys)