#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 08:22:15 2022

@author: Daniel
"""

import wx
# from main_window import MainWindow
from sensys_config import sensys_config
from PyQt5 import QtWidgets
from main_window2 import MainWidnow
import sys

if __name__ == '__main__':
    config = sensys_config(1)
    # app = wx.App()
    # main_window = MainWindow(config)
    # app.MainLoop()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWidnow(config)
    app.exec_()