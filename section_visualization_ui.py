# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'section_visualization.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_section_visualization_gui(object):
    def setupUi(self, section_visualization_gui):
        section_visualization_gui.setObjectName("section_visualization_gui")
        section_visualization_gui.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(section_visualization_gui)
        self.centralwidget.setObjectName("centralwidget")
        section_visualization_gui.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(section_visualization_gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        section_visualization_gui.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(section_visualization_gui)
        self.statusbar.setObjectName("statusbar")
        section_visualization_gui.setStatusBar(self.statusbar)

        self.retranslateUi(section_visualization_gui)
        QtCore.QMetaObject.connectSlotsByName(section_visualization_gui)

    def retranslateUi(self, section_visualization_gui):
        _translate = QtCore.QCoreApplication.translate
        section_visualization_gui.setWindowTitle(_translate("section_visualization_gui", "MainWindow"))

