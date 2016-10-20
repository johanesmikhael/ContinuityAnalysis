from OCC.Display.backend import load_backend
from PyQt5 import QtCore

# load_backend("qt-pyqt4")
from OCC.Display.qtDisplay import qtViewer3d
from PyQt5 import QtGui


class SectionVisualizationWidget(qtViewer3d):
    def __init__(self, *kargs):
        super(SectionVisualizationWidget, self).__init__(*kargs)
        self._parent = kargs[0]

    def InitDriver(self):
        super(SectionVisualizationWidget, self).InitDriver()
        r, g, b = self._parent.viewer_bg_color
        self.get_display().set_bg_gradient_color(r, g, b, r, g, b)

    def get_display(self):
        return self._display

    def mouseMoveEvent(self, event):
        super(SectionVisualizationWidget, self).mouseMoveEvent(event)
        self.update()

    def wheelEvent(self, event):
        super(SectionVisualizationWidget, self).wheelEvent(event)
        self.update()

    def draw_path_mark(self, painter):
        for p in self._is_draw_path_mark:
            screen_x, screen_y = self._display.View.Convert(p[0], p[1], p[2])
            painter.drawText(screen_x, screen_y, p[3])

    def paintEvent(self, event):
        if self._inited:
            self._display.Context.UpdateCurrentViewer()
            # important to allow overpainting of the OCC OpenGL context in Qt
            # self.swapBuffers()

        if self._drawbox:
            self.makeCurrent()
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 1))
            rect = QtCore.QRect(*self._drawbox)
            self.swapBuffers()
            painter.drawRect(rect)
            painter.end()
            self.doneCurrent()

        if self._is_draw_path_mark:
            self.makeCurrent()
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 1))
            self.swapBuffers()
            self.draw_path_mark(painter)
            painter.end()
            self.doneCurrent()