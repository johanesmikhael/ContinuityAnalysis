from OCC.Display.backend import load_backend
from OCC.gp import gp_Pnt

from PyQt5 import QtCore

from geom import points_to_bezier_curve
from geom import points_to_bspline_curve

load_backend("qt-pyqt5")
from OCC.Display.qtDisplay import qtViewer3d


class IfcViewerWidget(qtViewer3d):
    def __init__(self, *kargs):
        super(IfcViewerWidget, self).__init__(*kargs)
        self._parent = kargs[0]
        self._is_draw_path = False
        self._path_pts = []
        self._path_curve = [None, None]
        self._preview_curve = [None, None]
        self._path_height = None

    def InitDriver(self):
        super(IfcViewerWidget, self).InitDriver()
        r, g, b = self._parent.viewer_bg_color
        self.get_display().set_bg_gradient_color(r, g, b, r, g, b)
        self._path_height = self._parent.path_elevation

    def _SetupKeyMap(self):
        super(IfcViewerWidget, self)._SetupKeyMap()
        self._key_map[ord(' ')] = self.end_draw_path

    def point_from_top_view(self, screen_x, screen_y, height):
        (x, y, z, vx, vy, vz) = self._display.View.ConvertWithProj(screen_x, screen_y)
        pt = gp_Pnt(x, y, height)
        return pt

    def draw_path(self, event, height):
        pt_scr = Point(event.pos())
        pt = self.point_from_top_view(pt_scr.x, pt_scr.y, height)
        pt_shape = self._display.DisplayShape(pt)
        self._path_pts.append((pt, pt_shape))
        self._display.Repaint()

    def preview_path(self, event, height):
        pt_scr = Point(event.pos())
        if len(self._path_pts) > 0:
            pt = self.point_from_top_view(pt_scr.x, pt_scr.y, height)
            temp_pts = self._path_pts[:]
            temp_pts.append((pt, None))
            if len(temp_pts) > 1:
                # self._preview_curve[0] = points_to_bezier_curve(temp_pts)
                self._preview_curve[0] = points_to_bspline_curve(temp_pts, 3)
                if self._preview_curve[1] is not None:
                    self._display.Context.Clear(self._preview_curve[1])
                self._preview_curve[1] = self._display.DisplayShape(self._preview_curve[0])
            self._display.Repaint()

    def end_draw_path(self):
        if self._is_draw_path:
            self.set_draw_path_mode(False)
            self._display.View_Iso()
            # self._display.SetModeShaded()
            if len(self._path_pts) > 1:
                self.clear_path_curve()
                # self._path_curve[0] = points_to_bezier_curve(self._path_pts)
                self._path_curve[0] = points_to_bspline_curve(self._path_pts, 3)
                self._path_curve[1] = self._display.DisplayShape(self._path_curve[0])
            for pt in self._path_pts:
                self._display.Context.Remove(pt[1])
            self._path_pts = []
            self._display.Context.Remove(self._preview_curve[1])
            self._display.FitAll()
            self._display.Repaint()

    def set_draw_path_mode(self, is_draw):
        self._is_draw_path = is_draw
        if self._is_draw_path:
            self._display.View_Top()
            self._display.SetModeWireFrame()
            self._display.FitAll()
            self._display.Repaint()
            self._display.ZoomFactor(0.9)

    def mouseReleaseEvent(self, event):
        if self._is_draw_path and event.button() == QtCore.Qt.LeftButton:
            self.draw_path(event, self._path_height)
        else:
            super(IfcViewerWidget, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        pt = Point(event.pos())
        buttons = int(event.buttons())
        modifiers = event.modifiers()
        # DRAW SPLINE
        if self._is_draw_path:
            self.preview_path(event, self._path_height)
        pass
        # ROTATE
        if (buttons == QtCore.Qt.LeftButton and
                not modifiers == QtCore.Qt.ShiftModifier and not self._is_draw_path):
            # dx = pt.x - self.dragStartPos.x
            # dy = pt.y - self.dragStartPos.y
            self._display.Rotation(pt.x, pt.y)
            self._drawbox = False
        # DYNAMIC ZOOM
        elif buttons == QtCore.Qt.RightButton and not modifiers == QtCore.Qt.ShiftModifier:
            self._display.Repaint()
            self._display.DynamicZoom(abs(self.dragStartPos.x),
                                      abs(self.dragStartPos.y), abs(pt.x),
                                      abs(pt.y))
            self.dragStartPos.x = pt.x
            self.dragStartPos.y = pt.y
            self._drawbox = False
        # PAN
        elif buttons == QtCore.Qt.MidButton:
            dx = pt.x - self.dragStartPos.x
            dy = pt.y - self.dragStartPos.y
            self.dragStartPos.x = pt.x
            self.dragStartPos.y = pt.y
            self._display.Pan(dx, -dy)
            self._drawbox = False
        # DRAW BOX
        # ZOOM WINDOW
        elif buttons == QtCore.Qt.RightButton and modifiers == QtCore.Qt.ShiftModifier:
            self._zoom_area = True
            self.DrawBox(event)
        # SELECT AREA
        elif buttons == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ShiftModifier:
            self._select_area = True
            self.DrawBox(event)
        else:
            self._drawbox = False
            self._display.MoveTo(pt.x, pt.y)

    def get_path_curve(self):
        return self._path_curve

    def clear_path_curve(self):
        if self._path_curve[0] is not None:
            if self._path_curve[1] is not None:
                self._display.Context.Remove(self._path_curve[1])
            self._path_curve[0] = None
            return True
        else:
            return False

    def get_display(self):
        return self._display

    def is_draw_path(self):
        return self._is_draw_path


class Point(object):
    def __init__(self, obj=None):
        self.x = 0
        self.y = 0
        if obj is not None:
            self.set(obj)

    def set(self, obj):
        self.x = obj.x()
        self.y = obj.y()
