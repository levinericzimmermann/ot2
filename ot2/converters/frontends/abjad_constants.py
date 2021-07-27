class PaperFormat(object):
    def __init__(self, name: str, height: float, width: float):
        self.name = name
        self.height = height
        self.width = width


A4 = PaperFormat("a4", 210, 297)
A3 = PaperFormat("a3", 297, 420)
A2 = PaperFormat("a2", 420, 594)
