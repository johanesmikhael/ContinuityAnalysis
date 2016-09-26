from OCC.Quantity import Quantity_TOC_RGB, Quantity_Color


class Color:
    def __init__(self):
        pass

    white = 255, 255, 255
    gray = 127, 127, 127
    dark_gray = 32, 32, 32

    ais_yellow = Quantity_Color(1, 1, 0, Quantity_TOC_RGB)
    ais_blue = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
    ais_green = Quantity_Color(0, 1, 0, Quantity_TOC_RGB)
    ais_red = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
