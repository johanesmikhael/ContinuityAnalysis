# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'continuity_analyzer.ui'
#
# Created: Tue May 31 17:50:47 2016
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_main_gui(object):
    def setupUi(self, main_gui):
        main_gui.setObjectName(_fromUtf8("main_gui"))
        main_gui.resize(800, 509)
        self.centralwidget = QtGui.QWidget(main_gui)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        main_gui.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(main_gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        main_gui.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(main_gui)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        main_gui.setStatusBar(self.statusbar)

        self.retranslateUi(main_gui)
        QtCore.QMetaObject.connectSlotsByName(main_gui)

    def retranslateUi(self, main_gui):
        main_gui.setWindowTitle(_translate("main_gui", "MainWindow", None))

