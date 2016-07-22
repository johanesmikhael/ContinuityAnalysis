# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'section_visualization.ui'
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

class Ui_Section(object):
    def setupUi(self, Section):
        Section.setObjectName(_fromUtf8("Section"))
        Section.resize(806, 473)
        self.horizontalLayout = QtGui.QHBoxLayout(Section)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.groupBox = QtGui.QGroupBox(Section)
        self.groupBox.setMinimumSize(QtCore.QSize(200, 0))
        self.groupBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout.addWidget(self.groupBox)
        self.section_widget = QtGui.QWidget(Section)
        self.section_widget.setObjectName(_fromUtf8("section_widget"))
        self.groupBox.raise_()
        self.groupBox.raise_()
        self.horizontalLayout.addWidget(self.section_widget)

        self.retranslateUi(Section)
        QtCore.QMetaObject.connectSlotsByName(Section)

    def retranslateUi(self, Section):
        Section.setWindowTitle(_translate("Section", "Form", None))
        self.groupBox.setTitle(_translate("Section", "GroupBox", None))

