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
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_distance = QtWidgets.QLabel(self.centralwidget)
        self.label_distance.setObjectName("label_distance")
        self.gridLayout_2.addWidget(self.label_distance, 0, 0, 1, 1)
        self.verticalSlider_distance = QtWidgets.QSlider(self.centralwidget)
        self.verticalSlider_distance.setMaximum(100)
        self.verticalSlider_distance.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_distance.setObjectName("verticalSlider_distance")
        self.gridLayout_2.addWidget(self.verticalSlider_distance, 1, 0, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 1, 1, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 1)
        self.listWidget_elements = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget_elements.setMaximumSize(QtCore.QSize(750, 16777215))
        self.listWidget_elements.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.listWidget_elements.setObjectName("listWidget_elements")
        self.gridLayout.addWidget(self.listWidget_elements, 1, 2, 1, 1)
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
        self.label_distance.setText(_translate("analysis_visualization_gui", "TextLabel"))

