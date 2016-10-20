# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'material_browser.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MaterialBrowser(object):
    def setupUi(self, MaterialBrowser):
        MaterialBrowser.setObjectName("MaterialBrowser")
        MaterialBrowser.setWindowModality(QtCore.Qt.NonModal)
        MaterialBrowser.resize(631, 496)
        MaterialBrowser.setMinimumSize(QtCore.QSize(600, 0))
        self.verticalLayout = QtWidgets.QVBoxLayout(MaterialBrowser)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget_material = QtWidgets.QListWidget(MaterialBrowser)
        self.listWidget_material.setMinimumSize(QtCore.QSize(0, 0))
        self.listWidget_material.setMaximumSize(QtCore.QSize(300, 16777215))
        self.listWidget_material.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.listWidget_material.setObjectName("listWidget_material")
        self.horizontalLayout.addWidget(self.listWidget_material)
        self.groupBox = QtWidgets.QGroupBox(MaterialBrowser)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalSlider_slipCoefficient = QtWidgets.QSlider(self.groupBox)
        self.horizontalSlider_slipCoefficient.setMaximum(100)
        self.horizontalSlider_slipCoefficient.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_slipCoefficient.setObjectName("horizontalSlider_slipCoefficient")
        self.gridLayout_2.addWidget(self.horizontalSlider_slipCoefficient, 7, 2, 1, 1, QtCore.Qt.AlignTop)
        self.comboBox_reflectiveMethod = QtWidgets.QComboBox(self.groupBox)
        self.comboBox_reflectiveMethod.setObjectName("comboBox_reflectiveMethod")
        self.gridLayout_2.addWidget(self.comboBox_reflectiveMethod, 5, 2, 1, 1, QtCore.Qt.AlignTop)
        self.horizontalSlider_transparency = QtWidgets.QSlider(self.groupBox)
        self.horizontalSlider_transparency.setMaximum(100)
        self.horizontalSlider_transparency.setSingleStep(1)
        self.horizontalSlider_transparency.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_transparency.setObjectName("horizontalSlider_transparency")
        self.gridLayout_2.addWidget(self.horizontalSlider_transparency, 2, 2, 1, 1, QtCore.Qt.AlignTop)
        self.horizontalSlider_reflectance = QtWidgets.QSlider(self.groupBox)
        self.horizontalSlider_reflectance.setMaximum(100)
        self.horizontalSlider_reflectance.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_reflectance.setObjectName("horizontalSlider_reflectance")
        self.gridLayout_2.addWidget(self.horizontalSlider_reflectance, 4, 2, 1, 1, QtCore.Qt.AlignTop)
        self.pushButton_colorPicker = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_colorPicker.setObjectName("pushButton_colorPicker")
        self.gridLayout_2.addWidget(self.pushButton_colorPicker, 0, 2, 1, 1, QtCore.Qt.AlignTop)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 5, 0, 1, 1, QtCore.Qt.AlignTop)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1, QtCore.Qt.AlignTop)
        self.horizontalSlider_imperviousness = QtWidgets.QSlider(self.groupBox)
        self.horizontalSlider_imperviousness.setMaximum(100)
        self.horizontalSlider_imperviousness.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_imperviousness.setObjectName("horizontalSlider_imperviousness")
        self.gridLayout_2.addWidget(self.horizontalSlider_imperviousness, 9, 2, 1, 1)
        self.pushButton_saveChanges = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_saveChanges.setObjectName("pushButton_saveChanges")
        self.gridLayout_2.addWidget(self.pushButton_saveChanges, 10, 2, 1, 1)
        self.pushButton_reset = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_reset.setObjectName("pushButton_reset")
        self.gridLayout_2.addWidget(self.pushButton_reset, 10, 0, 1, 1)
        self.label_tranparency_value = QtWidgets.QLabel(self.groupBox)
        self.label_tranparency_value.setObjectName("label_tranparency_value")
        self.gridLayout_2.addWidget(self.label_tranparency_value, 1, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 3, 0, 1, 1)
        self.label_reflectance_value = QtWidgets.QLabel(self.groupBox)
        self.label_reflectance_value.setObjectName("label_reflectance_value")
        self.gridLayout_2.addWidget(self.label_reflectance_value, 3, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_slip_coefficient = QtWidgets.QLabel(self.groupBox)
        self.label_slip_coefficient.setObjectName("label_slip_coefficient")
        self.gridLayout_2.addWidget(self.label_slip_coefficient, 6, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 6, 0, 1, 1)
        self.label_imperviousness = QtWidgets.QLabel(self.groupBox)
        self.label_imperviousness.setObjectName("label_imperviousness")
        self.gridLayout_2.addWidget(self.label_imperviousness, 8, 2, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_6.setObjectName("label_6")
        self.gridLayout_2.addWidget(self.label_6, 8, 0, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_loadXML = QtWidgets.QPushButton(MaterialBrowser)
        self.pushButton_loadXML.setObjectName("pushButton_loadXML")
        self.horizontalLayout_2.addWidget(self.pushButton_loadXML)
        self.pushButton_saveXML = QtWidgets.QPushButton(MaterialBrowser)
        self.pushButton_saveXML.setObjectName("pushButton_saveXML")
        self.horizontalLayout_2.addWidget(self.pushButton_saveXML)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(MaterialBrowser)
        QtCore.QMetaObject.connectSlotsByName(MaterialBrowser)

    def retranslateUi(self, MaterialBrowser):
        _translate = QtCore.QCoreApplication.translate
        MaterialBrowser.setWindowTitle(_translate("MaterialBrowser", "Form"))
        self.groupBox.setTitle(_translate("MaterialBrowser", "Properties"))
        self.pushButton_colorPicker.setText(_translate("MaterialBrowser", "Color Picker"))
        self.label_4.setText(_translate("MaterialBrowser", "Reflective Method"))
        self.label.setText(_translate("MaterialBrowser", "Color"))
        self.pushButton_saveChanges.setText(_translate("MaterialBrowser", "Save Changes"))
        self.pushButton_reset.setText(_translate("MaterialBrowser", "Reset"))
        self.label_tranparency_value.setText(_translate("MaterialBrowser", "TextLabel"))
        self.label_3.setText(_translate("MaterialBrowser", "Reflectance"))
        self.label_reflectance_value.setText(_translate("MaterialBrowser", "TextLabel"))
        self.label_2.setText(_translate("MaterialBrowser", "Transparency"))
        self.label_slip_coefficient.setText(_translate("MaterialBrowser", "TextLabel"))
        self.label_5.setText(_translate("MaterialBrowser", "Slip Coefficient"))
        self.label_imperviousness.setText(_translate("MaterialBrowser", "TextLabel"))
        self.label_6.setText(_translate("MaterialBrowser", "Imperviousness"))
        self.pushButton_loadXML.setText(_translate("MaterialBrowser", "Load XML"))
        self.pushButton_saveXML.setText(_translate("MaterialBrowser", "Save XML"))

