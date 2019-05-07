# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slice_visualization.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_slice_visualization_gui(object):
    def setupUi(self, slice_visualization_gui):
        slice_visualization_gui.setObjectName("slice_visualization_gui")
        slice_visualization_gui.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(slice_visualization_gui)
        self.centralwidget.setObjectName("centralwidget")
        slice_visualization_gui.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(slice_visualization_gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        slice_visualization_gui.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(slice_visualization_gui)
        self.statusbar.setObjectName("statusbar")
        slice_visualization_gui.setStatusBar(self.statusbar)

        self.retranslateUi(slice_visualization_gui)
        QtCore.QMetaObject.connectSlotsByName(slice_visualization_gui)

    def retranslateUi(self, slice_visualization_gui):
        _translate = QtCore.QCoreApplication.translate
        slice_visualization_gui.setWindowTitle(_translate("slice_visualization_gui", "MainWindow"))

