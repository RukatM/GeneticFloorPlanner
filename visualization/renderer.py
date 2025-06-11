import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF

from genetic.chromosome import Chromosome
from genetic.individual import Individual


from PyQt5.QtGui import QPolygonF
from PyQt5.QtCore import QPointF

class BuildingWidget(QWidget):
    def __init__(self, individual, building_outline, entrances=None, parent=None):
        super().__init__(parent)
        self.individual = individual
        self.outline = building_outline
        self.entrances = entrances if entrances else []
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

        painter.setBrush(QColor(0, 255, 0))  # Zielony kolor
        painter.setPen(QPen(Qt.darkGreen, 2))

        for entrance in self.entrances:
            x = entrance['x'] * scale
            y = entrance['y'] * scale
            size = 6
            painter.drawEllipse(QPointF(x, y), size, size)


class MainWindow(QMainWindow):
    def __init__(self, individual, outline, entrances):
        super().__init__()
        self.setWindowTitle("Building Layout Visualization")
        self.setCentralWidget(BuildingWidget(individual, outline, entrances))


def preview(individual, building_outline, entrances):
    app = QApplication(sys.argv)

    window = MainWindow(individual, building_outline, entrances)
    window.show()
    sys.exit(app.exec_())