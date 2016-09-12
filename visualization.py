# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'visualization.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_section_visualization(object):
    def setupUi(self, section_visualization):
        section_visualization.setObjectName(_fromUtf8("section_visualization"))
        section_visualization.resize(806, 491)
        self.verticalLayout_4 = QtGui.QVBoxLayout(section_visualization)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.verticalLayout_toolbar = QtGui.QVBoxLayout()
        self.verticalLayout_toolbar.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.verticalLayout_toolbar.setObjectName(_fromUtf8("verticalLayout_toolbar"))
        self.verticalLayout_4.addLayout(self.verticalLayout_toolbar)
        self.horizontalLayout_main = QtGui.QHBoxLayout()
        self.horizontalLayout_main.setObjectName(_fromUtf8("horizontalLayout_main"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_main.addLayout(self.verticalLayout)
        self.verticalLayout_4.addLayout(self.horizontalLayout_main)

        self.retranslateUi(section_visualization)
        QtCore.QMetaObject.connectSlotsByName(section_visualization)

    def retranslateUi(self, section_visualization):
        section_visualization.setWindowTitle(_translate("section_visualization", "Form", None))

