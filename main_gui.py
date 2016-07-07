import sys

from continuity_analyzer_ui import Ui_main_gui
from PyQt4 import QtGui, QtCore

from ifc_viewer_widget import IfcViewerWidget

from ifcopenshell.geom import occ_utils
import ifcopenshell

# from OCC.Utils import Topo
from OCC import V3d
from OCC.gp import gp_Pln, gp_Dir
from OCC.GeomAdaptor import GeomAdaptor_Curve
from OCC.GCPnts import GCPnts_AbscissaPoint
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.TopTools import TopTools_HSequenceOfShape
from OCC.TopTools import Handle_TopTools_HSequenceOfShape

from OCC.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds


class GuiMainWindow(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.ui = Ui_main_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Main GUI")
        self.resize(1024, 640)
        self.canvas = IfcViewerWidget(self)
        self.setCentralWidget(self.canvas)
        if not sys.platform == "darwin":
            self.menu_bar = self.menuBar()
        else:
            self.menu_bar = QtGui.QMenuBar()
        self._menus = {}
        self._menu_methods = {}
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()

        self.ifcopenshell_setting = ifcopenshell.geom.settings()
        self.ifcopenshell_setting.set(self.ifcopenshell_setting.USE_PYTHON_OPENCASCADE, True)
        self.ifc_file = None
        self.products = []
        self.section_planes = []

    def setup_ifcopenshell_viewer(self, _app):
        display = self.canvas.get_display()

        def add_menu(*args, **kwargs):
            self.add_menu(*args, **kwargs)

        def add_function_to_menu(*args, **kwargs):
            self.add_function_to_menu(*args, **kwargs)

        def start_display():
            self.start_display(_app)

        occ_utils.handle = display
        occ_utils.main_loop = start_display
        occ_utils.add_menu = add_menu
        occ_utils.add_function_to_menu = add_function_to_menu

        viewer_handle = occ_utils.handle.GetViewer()
        viewer = viewer_handle.GetObject()
        while True:
            viewer.InitActiveLights()
            try:
                active_light = viewer.ActiveLight()
            except:
                break
            viewer.DelLight(active_light)
            viewer.NextActiveLights()
        for direction in [(1, 2, -3), (-2, -1, 1)]:
            light = V3d.V3d_DirectionalLight(viewer_handle)
            light.SetDirection(*direction)
            viewer.SetLightOn(light.GetHandle())

    def start_display(self, app):
        self.raise_()
        app.exec_()

    def add_menu(self, menu_name):
        _menu = self.menu_bar.addMenu("&" + menu_name)
        self._menus[menu_name] = _menu

    def add_function_to_menu(self, menu_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtGui.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            _action.setMenuRole(QtGui.QAction.NoRole)
            self.connect(_action, QtCore.SIGNAL('triggered()'), _callable)
            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError("the menu item %s does not exist" % menu_name)

    def add_toolbar(self, toolbar_name):
        _toolbar = self.addToolBar(toolbar_name)
        self._toolbars[toolbar_name] = _toolbar

    def add_function_to_toolbar(self, toolbar_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtGui.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            self.connect(_action, QtCore.SIGNAL('triggered()'), _callable)
            self._toolbars[toolbar_name].addSeparator()
            self._toolbars[toolbar_name].addAction(_action)
        except KeyError:
            raise ValueError("the %s toolbar does not exist" % toolbar_name)

    def setup_toolbar(self):
        self.add_toolbar("Main Toolbar")
        self.add_function_to_toolbar("Main Toolbar", self.open_file)
        self.add_function_to_toolbar("Main Toolbar", self.draw_path)
        self.add_function_to_toolbar("Main Toolbar", self.generate_section_plane)
        self.add_function_to_toolbar("Main Toolbar", self.process_section)

    def draw_path(self):
        if self.ifc_file is None:
            print "no file opened"
            return
        if not self.canvas.is_draw_path():
            self.canvas.set_draw_path_mode(True)
        else:
            print "drawing mode already On"

    def open_file(self):
        from Tkinter import Tk
        import tkFileDialog
        root = Tk()
        root.withdraw()
        file_name = tkFileDialog.askopenfilename(filetypes=[("IFC files", "*.ifc")])
        root.destroy()
        from os.path import isfile
        if isfile(file_name):
            self.close_file() # reset the program
            self.products = []
            self.ifc_file = ifcopenshell.open(str(file_name))
            self.display_ifc_file()
        else:
            print "No file opened"

    def close_file(self):
        # clear section plane if exist
        self.clear_crv_sections()
        # clear section path if exist
        self.clear_section_path()
        # clear ifc products
        self.clear_products()

    def display_ifc_file(self):
        products = self.ifc_file.by_type('IfcProduct')
        display = self.canvas.get_display()
        for product in products:
            # print "ee------------------------------------------ee"
            # print product
            # print product.GlobalId
            # print product.OwnerHistory
            # print product.Name
            # print product.ObjectType
            # print product.ObjectPlacement
            # print product.ReferencedBy
            if product.Representation is not None:
                shape = ifcopenshell.geom.create_shape(self.ifcopenshell_setting, product).geometry
                model_display = display.DisplayShape(shape, transparency=0.5)
                self.products.append((product, shape, model_display))
        display.FitAll()

    def generate_section_plane(self):
        section_success = self.create_section_plane(2)
        if not section_success:
            print "no curve drawn yet"

    def create_section_plane(self, section_distance):
        crv = self.canvas.get_path_curve()[0]
        display = self.canvas.get_display()
        if crv is not None:
            div_crv_param = self.divide_curve(crv, section_distance)
            self.clear_crv_sections()
            for i in div_crv_param:
                pt = crv.Value(i)
                pt_vec = crv.DN(i, 1)
                pt_sec_plane = gp_Pln(pt, gp_Dir(pt_vec))
                section_face = BRepBuilderAPI_MakeFace(pt_sec_plane, -5, 5, -5, 5).Face()
                section_face_display = display.DisplayShape(section_face, transparency=0.99, color=255)
                self.section_planes.append((i, section_face, section_face_display))
            display.Repaint()
            return True
        else:
            return False

    def clear_crv_sections(self):
        display = self.canvas.get_display()
        for section_plane in self.section_planes:
            display.Context.Clear(section_plane[2])
        self.section_planes = []

    def clear_section_path(self):
        self.canvas.clear_path_curve()

    def clear_products(self):
        display = self.canvas.get_display()
        display.Context.RemoveAll()
        self.products = []
        self.ifc_file = None

    @staticmethod
    def divide_curve(crv, distance):
        geom_adaptor_curve = GeomAdaptor_Curve(crv.GetHandle())
        curve_param = [0]
        param = 0
        while param < 1:
            gcpnts_abscissa_point = GCPnts_AbscissaPoint(geom_adaptor_curve, distance, param)
            param = gcpnts_abscissa_point.Parameter()
            if param <= 1:
                curve_param.append(param)
        return curve_param

    def process_section(self):
        #self.coba_01()
        for section_plane in self.section_planes:
            section_plane_face = section_plane[1]
            for product in self.products:
                shape = product[1]
                section = BRepAlgoAPI_Section(section_plane_face, shape)
                edge_list = section.SectionEdges()
                if not edge_list.IsEmpty():
                    edges = TopTools_HSequenceOfShape()
                    edges_handle = Handle_TopTools_HSequenceOfShape(edges)
                    wires = TopTools_HSequenceOfShape()
                    wires_handle = Handle_TopTools_HSequenceOfShape(wires)
                    edge_list_iterator = TopTools_ListIteratorOfListOfShape(edge_list)
                    while edge_list_iterator.More():
                        edge = edge_list_iterator.Value()
                        edge_list_iterator.Next()
                        edges.Append(edge)
                    ShapeAnalysis_FreeBounds.ConnectEdgesToWires(edges_handle, 1e-5, True, wires_handle)
                    wires = wires_handle.GetObject()

    def coba_01(self):
        for product in self.products:
            associations = product[0].HasAssociations
            print "product type:"
            print product[0].is_a()
            print product[0].Name
            for association in associations:
                materials = association.RelatingMaterial
                if materials.is_a("IfcMaterial"):
                    print "relating material type: IfcMaterial"
                    pass
                elif materials.is_a("IfcMaterialList"):
                    print "relating material type:IfcMaterialList"
                    pass
                elif materials.is_a("IfcMaterialLayer"):
                    print "relating material type:IfcMaterialLayer"
                    pass
                elif materials.is_a("IfcMaterialLayerSet"):
                    print "relating material type:IfcMaterialLayerSet"
                    pass
                elif materials.is_a("IfcMaterialLayerSetUsage"):
                    print "relating material type:IfcMaterialLayerSetUsage"
                    representations = product[0].Representation.Representations
                    '''for representation in representations:
                        print representation
                        print representation.ContextOfItems
                        print representation.ContextOfItems.ParentContext
                        print representation.ContextOfItems.ParentContext.TrueNorth
                        print representation.ContextOfItems.ParentContext.TrueNorth.DirectionRatio
                        print representation.RepresentationIdentifier
                        print representation.RepresentationType
                        print representation.Items
                        for item in representation.Items:
                            if representation.RepresentationIdentifier == "Axis":
                                print "axis"
                                print item
                        print representation.RepresentationMap
                        print representation.LayerAssignments
                        print representation.OfProductRepresentation'''
                    placement = product[0].ObjectPlacement
                    print placement
                    print placement.RelativePlacement
                    print placement.RelativePlacement.RefDirection
                    print materials.LayerSetDirection
                    for material in materials.ForLayerSet.MaterialLayers:
                        print material.Material.Name
                        print material.LayerThickness
