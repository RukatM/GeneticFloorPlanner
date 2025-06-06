import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF

from genetic.chromosome import Chromosome
from genetic.individual import Individual


from PyQt5.QtGui import QPolygonF
from PyQt5.QtCore import QPointF

class BuildingWidget(QWidget):
    def __init__(self, individual, building_outline, parent=None):
        super().__init__(parent)
        self.individual = individual
        self.outline = building_outline
        self.setMinimumSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.individual.chromosomes:
            return

        # Zbieramy wszystkie współrzędne (pokoje + obrys budynku)
        all_x = [room.x + room.width for room in self.individual.chromosomes] + [p['x'] for p in self.outline]
        all_y = [room.y + room.height for room in self.individual.chromosomes] + [p['y'] for p in self.outline]

        max_x = max(all_x)
        max_y = max(all_y)

        widget_width = self.width()
        widget_height = self.height()

        # Obliczamy skalę tak, by zmieścić wszystko z marginesem
        scale_x = widget_width / (max_x + 2)
        scale_y = widget_height / (max_y + 2)
        scale = min(scale_x, scale_y)

        # Rysuj tło – zarys budynku
        painter.setPen(QPen(Qt.gray, 2, Qt.DashLine))
        painter.setBrush(QColor(230, 230, 230))

        polygon = QPolygonF([QPointF(p['x'] * scale, p['y'] * scale) for p in self.outline])
        painter.drawPolygon(polygon)

        # Rysuj pokoje
        for room in self.individual.chromosomes:
            color = QColor.fromHsv(hash(room.room_type) % 360, 255, 200)
            painter.setBrush(color)
            painter.setPen(QPen(Qt.black, 2))

            rect_x = int(room.x * scale)
            rect_y = int(room.y * scale)
            rect_w = int(room.width * scale)
            rect_h = int(room.height * scale)

            painter.drawRect(rect_x, rect_y, rect_w, rect_h)
            painter.setPen(Qt.black)
            painter.drawText(rect_x + 5, rect_y + 15, room.room_type)


class MainWindow(QMainWindow):
    def __init__(self, individual, outline):
        super().__init__()
        self.setWindowTitle("Building Layout Visualization")
        self.setCentralWidget(BuildingWidget(individual, outline))


def preview(individual, building_outline):
    app = QApplication(sys.argv)

    # building_outline = [
    #     {'x': 1, 'y': 1},
    #     {'x': 20, 'y': 1},
    #     {'x': 20, 'y': 15},
    #     {'x': 10, 'y': 15},
    #     {'x': 10, 'y': 25},
    #     {'x': 1, 'y': 25},
    # ]

    window = MainWindow(individual, building_outline)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    app = QApplication(sys.argv)

    rooms = [
        Chromosome("Living Room", 2, 2, 6, 5),
        Chromosome("Kitchen", 9, 2, 4, 4),
        Chromosome("Bedroom", 2, 8, 5, 5),
        Chromosome("Bathroom", 8, 9, 3, 3),
    ]
    layout = Individual(chromosomes=rooms, fitness=0.85)

    building_outline = [
        {'x': 1, 'y': 1},
        {'x': 20, 'y': 1},
        {'x': 20, 'y': 15},
        {'x': 10, 'y': 15},
        {'x': 10, 'y': 25},
        {'x': 1, 'y': 25},
    ]

    window = MainWindow(layout, building_outline)
    window.show()
    sys.exit(app.exec_())

