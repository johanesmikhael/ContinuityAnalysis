# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'analysis_visualization.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_analysis_visualization_gui(object):
    def setupUi(self, analysis_visualization_gui):
        analysis_visualization_gui.setObjectName("analysis_visualization_gui")
        analysis_visualization_gui.resize(755, 553)
        self.centralwidget = QtWidgets.QWidget(analysis_visualization_gui)
        self.centralwidget.setEnabled(True)
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        analysis_visualization_gui.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(analysis_visualization_gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 755, 21))
        self.menubar.setObjectName("menubar")
        analysis_visualization_gui.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(analysis_visualization_gui)
        self.statusbar.setObjectName("statusbar")
        analysis_visualization_gui.setStatusBar(self.statusbar)

        self.retranslateUi(analysis_visualization_gui)
        QtCore.QMetaObject.connectSlotsByName(analysis_visualization_gui)

    def retranslateUi(self, analysis_visualization_gui):
        _translate = QtCore.QCoreApplication.translate
        analysis_visualization_gui.setWindowTitle(_translate("analysis_visualization_gui", "MainWindow"))

