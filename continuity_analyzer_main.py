import sys

from PyQt5 import QtGui, QtWidgets
from main_gui import GuiMainWindow


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    my_app = GuiMainWindow()
    my_app.show()
    my_app.canvas.InitDriver()
    my_app.setup_ifcopenshell_viewer(app)
    my_app.start_display(app)