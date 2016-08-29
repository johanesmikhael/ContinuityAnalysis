from OCC.Display.backend import load_backend
from PyQt4 import QtCore

load_backend("qt-pyqt4")
from OCC.Display.qtDisplay import qtViewer3d


class SectionVisualizationWidget(qtViewer3d):
    def __init__(self, *kargs):
        super(SectionVisualizationWidget, self).__init__(*kargs)

    def InitDriver(self):
        super(SectionVisualizationWidget,self).InitDriver()
        self.get_display().set_bg_gradient_color(38,38,38,38,38,38)

    def get_display(self):
        return self._display