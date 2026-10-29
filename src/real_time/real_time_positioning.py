import numpy as np
import matplotlib.pyplot as plt

import serial
import pynmea2
import serial.tools.list_ports
import sys

from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer,Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

ports = serial.tools.list_ports.comports()
for port in ports:
    print(port.device)

ser = serial.Serial('COM3', baudrate=4800, timeout=1)

print("Lecture et décodage des trames $GPGGA...")

print("Lecture brute du port COM3 :")

class position(QMainWindow):
    def __init__(self):
        super().__init__()
        self.debut=True
        self.long=[]
        self.lat=[]
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.x_min=None
        self.x_max=None
        self.y_min=None
        self.y_max=None

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def paintEvent(self, event):
        while self.debut:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if line.startswith('$GPGGA'):
                gga = pynmea2.parse(line)
                self.lat.append(gga.latitude)
                self.long.append(gga.longitude)

                self.x_min = min(self.long)
                self.x_max = max(self.long)
                self.y_min = min(self.lat)
                self.y_max = max(self.lat)

                self.debut=False


        self.ax.clear()
        self.ax.scatter(self.long, self.lat, color='blue')

        # Adapter les axes automatiquement
        dx = (self.x_max - self.x_min) / 10 if self.x_max - self.x_min >0 else 0.1
        dy = (self.y_max - self.y_min) / 10 if self.y_max - self.y_min >0 else 0.1

        self.ax.set_xlim(self.x_min - dx, self.x_max + dx)
        self.ax.set_ylim(self.y_min - dy, self.y_max + dy)

        # Met à jour le canvas
        self.canvas.draw()

    def boucle(self):
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        if line.startswith('$GPGGA'):
            gga = pynmea2.parse(line)
            self.lat.append(gga.latitude)
            self.long.append(gga.longitude)
            self.x_min = min(self.long)
            self.x_max = max(self.long)
            self.y_min = min(self.lat)
            self.y_max = max(self.lat)

        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    graph = position()
    graph.show()
    graph.timer = QTimer()
    graph.timer.timeout.connect(graph.boucle)
    graph.timer.start(100)

    sys.exit(app.exec_())






