import sys
import os

from PyQt4 import QtGui
from main_gui import GuiMainWindow

app = QtGui.QApplication(sys.argv)
my_app = GuiMainWindow()
my_app.show()
my_app.canvas.InitDriver()
my_app.setup_ifcopenshell_viewer(app)
my_app.start_display(app)