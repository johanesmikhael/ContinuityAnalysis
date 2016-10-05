from OCC.Display.backend import load_backend
from PyQt5 import QtCore

# load_backend("qt-pyqt4")
from OCC.Display.qtDisplay import qtViewer3d


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
