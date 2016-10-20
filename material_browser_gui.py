from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QListWidgetItem, QColorDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from material_browser_ui import Ui_MaterialBrowser

from ifcmaterials import Material

from util import Color, prettify, get_float_from_xml, get_text_from_xml, get_int_from_xml

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom.minidom import Document, parse, parseString

class GuiMaterialBrowser(QtWidgets.QWidget):
    def __init__(self, *args):
        self.parent = args[0]
        QtWidgets.QWidget.__init__(self)
        self.ui = Ui_MaterialBrowser()
        self.ui.setupUi(self)
        self.material_list_widget = self.ui.listWidget_material
        self.material_list_widget.currentItemChanged.connect(self.load_material_data)
        self.initUI()
        self.materials = self.parent.material_dict
        self.setWindowTitle("Material Browser")
        self.material_temp = None
        self.color_temp = None
        self.transparency_temp = None
        self.reflectance_temp = None
        self.reflective_method_temp = None
        self.slip_coefficient_temp = None
        self.imperviousness_temp = None
        self.load_materials()

    def initUI(self):
        self.set_reflectance_method_combo_box_values()
        self.ui.pushButton_colorPicker.clicked.connect(self.set_color_picker_value)
        self.ui.horizontalSlider_transparency.valueChanged.connect(self.set_transparency_value)
        self.ui.horizontalSlider_reflectance.valueChanged.connect(self.set_reflectance_value)
        self.ui.horizontalSlider_slipCoefficient.valueChanged.connect(self.set_slip_coefficient_value)
        self.ui.horizontalSlider_imperviousness.valueChanged.connect(self.set_imperviousness_value)
        self.ui.comboBox_reflectiveMethod.currentIndexChanged.connect(self.set_reflectance_method_value)
        self.ui.pushButton_reset.clicked.connect(self.reset_material_value)
        self.ui.pushButton_saveChanges.clicked.connect(self.save_material_value)
        self.ui.pushButton_saveXML.clicked.connect(self.save_xml_doc)
        self.ui.pushButton_loadXML.clicked.connect(self.load_xml)

    def load_materials(self):
        material_dict = self.materials.material_dict
        self.material_list_widget.clear()
        for name, material in material_dict.iteritems():
            item = QListWidgetItem()
            item.setText(name)
            item.setData(Qt.UserRole + 1, material)
            self.material_list_widget.addItem(item)
        self.material_list_widget.sortItems(Qt.AscendingOrder)
        self.material_list_widget.setCurrentRow(0)
        self.load_material_data()

    def load_material_data(self):
        if not self.material_list_widget.currentItem():
            return
        self.material_temp = self.material_list_widget.currentItem().data(Qt.UserRole + 1)
        self.set_color_picker(self.material_temp)
        self.set_transparency_slider(self.material_temp)
        self.set_reflectance_method_combo_box(self.material_temp)
        self.set_reflectance_slider(self.material_temp)
        self.set_slip_coefficient_slider(self.material_temp)
        self.set_imperviousness_slider(self.material_temp)

    def set_color_picker(self, material):
        button = self.ui.pushButton_colorPicker
        color = material.get_surface_colour()
        self.color_temp = (color[0], color[1], color[2])
        r, g, b = Color.from_factor_to_rgb(color[0], color[1], color[2])
        button.setStyleSheet("background-color: rgb({},{},{})".format(r, g, b))

    def set_color_picker_value(self):
        color = self.color_temp
        r, g, b = Color.from_factor_to_rgb(color[0], color[1], color[2])
        q_color = QColor(r, g, b)
        new_color = QColorDialog.getColor(q_color)
        button = self.ui.pushButton_colorPicker
        self.color_temp = Color.from_rgb_to_factor(new_color.red(), new_color.green(), new_color.blue())
        button.setStyleSheet("background-color: rgb({},{},{})".format(new_color.red(), new_color.green(), new_color.blue()))

    def set_reflectance_method_combo_box_values(self):
        combo_box = self.ui.comboBox_reflectiveMethod
        reflectance_methods = Material.reflectance_methods
        for key, value in reflectance_methods.iteritems():
            combo_box.addItem(value, key)

    def set_reflectance_method_combo_box(self, material):
        combo_box = self.ui.comboBox_reflectiveMethod
        self.reflective_method_temp = material.get_reflectance_method()
        combo_box.setCurrentIndex(self.reflective_method_temp)

    def set_reflectance_method_value(self):
        combo_box = self.ui.comboBox_reflectiveMethod
        self.reflective_method_temp = combo_box.currentIndex()

    def set_transparency_slider(self, material):
        slider = self.ui.horizontalSlider_transparency
        text_label = self.ui.label_tranparency_value
        transparency = material.get_transparency()
        self.transparency_temp = transparency
        scaled_value = int(self.transparency_temp*slider.maximum())
        slider.setValue(scaled_value)
        text_label.setText("%.2f" % self.transparency_temp)

    def set_transparency_value(self):
        slider = self.ui.horizontalSlider_transparency
        text_label = self.ui.label_tranparency_value
        value = slider.value()
        self.transparency_temp = float(value)/slider.maximum()
        text_label.setText("%.2f" % self.transparency_temp)

    def set_reflectance_slider(self, material):
        slider = self.ui.horizontalSlider_reflectance
        text_label = self.ui.label_reflectance_value
        reflectance = material.get_reflectance()
        self.reflectance_temp = reflectance
        scaled_value = int(self.reflectance_temp*slider.maximum())
        slider.setValue(scaled_value)
        text_label.setText("%.2f" % self.reflectance_temp)

    def set_reflectance_value(self):
        slider = self.ui.horizontalSlider_reflectance
        text_label = self.ui.label_reflectance_value
        value = slider.value()
        self.reflectance_temp = float(value)/slider.maximum()
        text_label.setText("%.2f" % self.reflectance_temp)

    def set_slip_coefficient_slider(self, material):
        slider = self.ui.horizontalSlider_slipCoefficient
        text_label = self.ui.label_slip_coefficient
        slip_coefficient = material.get_slip_coefficient()
        self.slip_coefficient_temp = slip_coefficient
        scaled_value = int(self.slip_coefficient_temp*slider.maximum())
        slider.setValue(scaled_value)
        text_label.setText("%.2f" % self.slip_coefficient_temp)

    def set_slip_coefficient_value(self):
        slider = self.ui.horizontalSlider_slipCoefficient
        text_label = self.ui.label_slip_coefficient
        value = slider.value()
        self.slip_coefficient_temp = float(value)/slider.maximum()
        text_label.setText("%.2f" % self.slip_coefficient_temp)

    def set_imperviousness_slider(self, material):
        slider = self.ui.horizontalSlider_imperviousness
        text_label = self.ui.label_imperviousness
        imperviousness = material.get_imperviousness()
        self.imperviousness_temp = imperviousness
        scaled_value = int(self.imperviousness_temp *slider.maximum())
        slider.setValue(scaled_value)
        text_label.setText("%.2f" % self.imperviousness_temp)

    def set_imperviousness_value(self):
        slider = self.ui.horizontalSlider_imperviousness
        text_label = self.ui.label_imperviousness
        value = slider.value()
        self.imperviousness_temp = float(value)/slider.maximum()
        text_label.setText("%.2f" % self.imperviousness_temp)

    def reset_material_value(self):
        self.set_color_picker(self.material_temp)
        self.set_transparency_slider(self.material_temp)
        self.set_reflectance_method_combo_box(self.material_temp)
        self.set_reflectance_slider(self.material_temp)
        self.set_slip_coefficient_slider(self.material_temp)
        self.set_imperviousness_slider(self.material_temp)

    def save_material_value(self):
        color = self.color_temp
        self.material_temp.set_surface_colour(color[0], color[1], color[2])
        self.material_temp.set_transparency(self.transparency_temp)
        self.material_temp.set_reflectance_method(self.reflective_method_temp)
        self.material_temp.set_reflectance(self.reflectance_temp)
        self.material_temp.set_slip_coefficient(self.slip_coefficient_temp)
        self.material_temp.set_imperviousness(self.imperviousness_temp)

    def save_xml(self):
        material_dict = self.materials.material_dict
        filename = self.parent.filename
        materials_xml = Element("materials")
        for name, material in material_dict.iteritems():
            material_xml = SubElement(materials_xml, "material")
            name_xml = SubElement(material_xml, "name")
            name_xml.text = name
            surface_color_xml = SubElement(material_xml, "surface_color")
            red_xml = SubElement(surface_color_xml, "red")
            green_xml = SubElement(surface_color_xml, "green")
            blue_xml = SubElement(surface_color_xml, "blue")
            red_xml.text = str(material.get_surface_colour()[0])
            green_xml.text = str(material.get_surface_colour()[1])
            blue_xml.text = str(material.get_surface_colour()[2])
            transparency_xml = SubElement(material_xml, "transparency")
            transparency_xml.text = str(material.get_transparency())
            reflectance_method_xml = SubElement(material_xml, "reflectance_method")
            reflectance_method_xml.text = str(material.get_reflectance_method())
            reflectance_xml = SubElement(material_xml, "reflectance")
            reflectance_xml.text = str(material.get_reflectance())
            slip_coefficient_xml = SubElement(material_xml, "slip_coefficient")
            slip_coefficient_xml.text = str(material.get_slip_coefficient())
            imperviousness_xml = SubElement(material_xml, "imperviousness")
            imperviousness_xml.text = str(material.get_imperviousness())
        print prettify(materials_xml)

    def save_xml_doc(self):
        material_dict = self.materials.material_dict
        doc = Document()
        filename = self.parent.filename
        materials_xml = doc.createElement("materials")
        doc.appendChild(materials_xml)
        for name, material in material_dict.iteritems():
            material_xml = doc.createElement("material")
            materials_xml.appendChild(material_xml)
            name_xml = doc.createElement("name")
            material_xml.appendChild(name_xml)
            name_text = doc.createTextNode(name)
            name_xml.appendChild(name_text)
            surface_color_xml = doc.createElement( "surface_color")
            material_xml.appendChild(surface_color_xml)
            red_xml = doc.createElement("red")
            surface_color_xml.appendChild(red_xml)
            green_xml = doc.createElement("green")
            surface_color_xml.appendChild(green_xml)
            blue_xml = doc.createElement("blue")
            surface_color_xml.appendChild(blue_xml)
            red_text = doc.createTextNode(str(material.get_surface_colour()[0]))
            red_xml.appendChild(red_text)
            green_text = doc.createTextNode(str(material.get_surface_colour()[1]))
            green_xml.appendChild(green_text)
            blue_text = doc.createTextNode(str(material.get_surface_colour()[2]))
            blue_xml.appendChild(blue_text)
            transparency_xml = doc.createElement("transparency")
            material_xml.appendChild(transparency_xml)
            transparency_text = doc.createTextNode(str(material.get_transparency()))
            transparency_xml.appendChild(transparency_text)
            reflectance_method_xml = doc.createElement("reflectance_method")
            material_xml.appendChild(reflectance_method_xml)
            reflectance_method_text = doc.createTextNode(str(material.get_reflectance_method()))
            reflectance_method_xml.appendChild(reflectance_method_text)
            reflectance_xml = doc.createElement("reflectance")
            material_xml.appendChild(reflectance_xml)
            reflectance_text = doc.createTextNode(str(material.get_reflectance()))
            reflectance_xml.appendChild(reflectance_text)
            slip_coefficient_xml = doc.createElement("slip_coefficient")
            material_xml.appendChild(slip_coefficient_xml)
            slip_coefficient_text = doc.createTextNode(str(material.get_slip_coefficient()))
            slip_coefficient_xml.appendChild(slip_coefficient_text)
            imperviousness_xml = doc.createElement("imperviousness")
            material_xml.appendChild(imperviousness_xml)
            imperviousness_text = doc.createTextNode(str(material.get_imperviousness()))
            imperviousness_xml.appendChild(imperviousness_text)

        doc.writexml( open(filename+".xml", 'w'),
                          indent="  ",
                          addindent="  ",
                          newl='\n')
        doc.unlink()

    def load_xml(self):
        filename = self.parent.filename
        from os.path import isfile
        if isfile(filename+".xml"):
            dom = parse(filename+".xml")
            self.process_xml(dom)
        else:
            print "no xml data"
        pass

    def process_xml(self, dom):
        material_dict = self.materials.material_dict
        material_xml_list = dom.getElementsByTagName("material")
        for material_xml in material_xml_list:
            name_xml = material_xml.getElementsByTagName("name")[0]
            name_value = get_text_from_xml(name_xml)
            surface_color_xml = material_xml.getElementsByTagName("surface_color")[0]
            red_xml = surface_color_xml.getElementsByTagName("red")[0]
            green_xml = surface_color_xml.getElementsByTagName("green")[0]
            blue_xml = surface_color_xml.getElementsByTagName("blue")[0]
            r = get_float_from_xml(red_xml)
            g = get_float_from_xml(green_xml)
            b = get_float_from_xml(blue_xml)
            transparency_xml = material_xml.getElementsByTagName("transparency")[0]
            transparency_value = get_float_from_xml(transparency_xml)
            reflectance_method_xml = material_xml.getElementsByTagName("reflectance_method")[0]
            reflectance_method_value= get_int_from_xml(reflectance_method_xml)
            reflectance_xml = material_xml.getElementsByTagName("reflectance")[0]
            reflectance_value = get_float_from_xml(reflectance_xml)
            slip_coefficient_xml = material_xml.getElementsByTagName("slip_coefficient")[0]
            slip_coefficient_value = get_float_from_xml(slip_coefficient_xml)
            imperviousness_xml = material_xml.getElementsByTagName("imperviousness")[0]
            imperviousness_value = get_float_from_xml(imperviousness_xml)
            material = material_dict[name_value]
            if material:
                material.set_surface_colour(r, g, b)
                material.set_transparency(transparency_value)
                material.set_reflectance_method(reflectance_method_value)
                material.set_reflectance(reflectance_value)
                material.set_slip_coefficient(slip_coefficient_value)
                material.set_imperviousness(imperviousness_value)
        self.load_materials()


