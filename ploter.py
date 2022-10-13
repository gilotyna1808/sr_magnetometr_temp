#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 08:22:15 2022

@author: Daniel
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QApplication)
import pyqtgraph as pg
PLOT_RANGE = 1000


class Plotter(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.btn_bar = {
            "X": parent.btn_draw_x_axis,
            "Y": parent.btn_draw_y_axis,
            "Z": parent.btn_draw_z_axis,
            "M": parent.btn_draw_m_axis
        }

        self.setAutoFillBackground(True)
        layout = QVBoxLayout()
        self.graph = pg.PlotWidget()
        layout.addWidget(self.graph)
        self.graph.setTitle("Odczyty")
        self.graph.setLabel('left', 'Tesla [μT]')
        self.graph.setBackground('w')
        self.graph.showGrid(x=True, y=True)
        self.graph.addLegend()
        self.setLayout(layout)

        self.plot_values = {
                "index": list(range(PLOT_RANGE)),
                "X": (self.graph.plot([],[], pen = pg.mkPen(color=(255, 0, 0), width=5)),[]),
                "Y": (self.graph.plot([],[], pen = pg.mkPen(color=(0, 255, 0), width=5)),[]),
                "Z": (self.graph.plot([],[], pen = pg.mkPen(color=(0, 0, 255), width=5)),[]),
                "M": (self.graph.plot([],[], pen = pg.mkPen(color=(255, 255, 0), width=5)),[])
            }
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.plot)
        self.timer.start()
    
    def btn_is_pressed(self, button):
        if button.styleSheet() == "":
            return False
        return True

    def plot(self):
        # self.graph.clear()
        for key in self.btn_bar:
            if self.btn_is_pressed(self.btn_bar[key]):
                x = self.plot_values["index"]
                y = self.plot_values[key][1].copy()
                l = len(y)
                if  l < PLOT_RANGE:
                    x = x[:l]
                else:
                    y = y[-PLOT_RANGE:]
                self.plot_values[key][0].setData(x,y)
            else:
                self.plot_values[key][0].setData([],[])
    def update_values(self, values):
        for key in values:
            self.plot_values[key][1].append(values[key])
            if (len(self.plot_values[key][1]) > 2000):
                self.plot_values[key] = (self.plot_values[key][0],self.plot_values[key][1][-1000:])