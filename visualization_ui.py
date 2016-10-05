# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'visualization.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_section_visualization(object):
    def setupUi(self, section_visualization):
        section_visualization.setObjectName("section_visualization")
        section_visualization.resize(806, 491)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(section_visualization)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_toolbar = QtWidgets.QVBoxLayout()
        self.verticalLayout_toolbar.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_toolbar.setObjectName("verticalLayout_toolbar")
        self.verticalLayout_4.addLayout(self.verticalLayout_toolbar)
        self.horizontalLayout_main = QtWidgets.QHBoxLayout()
        self.horizontalLayout_main.setObjectName("horizontalLayout_main")
        self.verticalLayout_4.addLayout(self.horizontalLayout_main)

        self.retranslateUi(section_visualization)
        QtCore.QMetaObject.connectSlotsByName(section_visualization)

    def retranslateUi(self, section_visualization):
        _translate = QtCore.QCoreApplication.translate
        section_visualization.setWindowTitle(_translate("section_visualization", "Form"))

