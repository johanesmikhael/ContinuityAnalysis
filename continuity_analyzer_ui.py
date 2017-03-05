# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'continuity_analyzer.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_main_gui(object):
    def setupUi(self, main_gui):
        main_gui.setObjectName("main_gui")
        main_gui.resize(791, 509)
        self.centralwidget = QtWidgets.QWidget(main_gui)
        self.centralwidget.setObjectName("centralwidget")
        main_gui.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(main_gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 791, 21))
        self.menubar.setObjectName("menubar")
        main_gui.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(main_gui)
        self.statusbar.setObjectName("statusbar")
        main_gui.setStatusBar(self.statusbar)

        self.retranslateUi(main_gui)
        QtCore.QMetaObject.connectSlotsByName(main_gui)

    def retranslateUi(self, main_gui):
        _translate = QtCore.QCoreApplication.translate
        main_gui.setWindowTitle(_translate("main_gui", "MainWindow"))



