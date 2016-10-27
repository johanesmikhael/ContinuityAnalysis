from PyQt5 import QtGui, QtWidgets, QtCore


class AnalysisViewWidget(QtWidgets.QGraphicsView):
    def __init__(self, *kargs):
        super(AnalysisViewWidget, self).__init__(*kargs)
        self.scale_factor = 1


    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            zoom_factor = 1.125
        else:
            zoom_factor = 0.8
        self.scale_factor = self.scale_factor * zoom_factor
        self.scale(zoom_factor, zoom_factor)



