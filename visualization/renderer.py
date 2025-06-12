import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF

from genetic.individual import Individual

class BuildingWidget(QWidget):
    def __init__(self, individual, building_outline, entrances=None, parent=None):
        super().__init__(parent)
        self.individual = individual
        self.outline = building_outline if building_outline else []
        self.entrances = entrances if entrances else []
        self.setMinimumSize(400, 400)

    def update_plan(self, individual, building_outline, entrances=None):
        """
        Updates the widget with a new floor plan
        """

        self.individual = individual
        self.outline = building_outline
        self.entrances = entrances if entrances else []
        self.update()

    def paintEvent(self, event):
        """
        Handles the painting of the widget.
        """
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.outline:
            return

        room_coords_x = []
        room_coords_y = []
        if self.individual and self.individual.chromosomes:
            room_coords_x = [room.x + room.width for room in self.individual.chromosomes]
            room_coords_y = [room.y + room.height for room in self.individual.chromosomes]

        all_x = room_coords_x + [p['x'] for p in self.outline]
        all_y = room_coords_y + [p['y'] for p in self.outline]
        
        if not all_x or not all_y:
            return
            
        plan_min_x = min([p['x'] for p in self.outline])
        plan_max_x = max(all_x)
        plan_min_y = min([p['y'] for p in self.outline])
        plan_max_y = max(all_y)
        
        plan_width = plan_max_x - plan_min_x
        plan_height = plan_max_y - plan_min_y

        if plan_width == 0 or plan_height == 0:
            return
            
        widget_width = self.width()
        widget_height = self.height()
        
        scale_x = widget_width / plan_width * 0.95
        scale_y = widget_height / plan_height * 0.95
        scale = min(scale_x, scale_y)

        scaled_plan_width = plan_width * scale
        scaled_plan_height = plan_height * scale
        x_offset = (widget_width - scaled_plan_width) / 2
        y_offset = (widget_height - scaled_plan_height) / 2
        
        painter.setPen(QPen(Qt.gray, 2, Qt.DashLine))
        painter.setBrush(QColor(230, 230, 230))
        
        polygon_points = []
        for p in self.outline:
            px = (p['x'] - plan_min_x) * scale + x_offset
            py = (p['y'] - plan_min_y) * scale + y_offset
            polygon_points.append(QPointF(px, py))
            
        polygon = QPolygonF(polygon_points)
        painter.drawPolygon(polygon)

        if self.individual and self.individual.chromosomes:
            for room in self.individual.chromosomes:
                color = QColor.fromHsv(hash(room.room_type) % 360, 255, 200)
                painter.setBrush(color)
                painter.setPen(QPen(Qt.black, 2))
                rect_x = int((room.x - plan_min_x) * scale + x_offset)
                rect_y = int((room.y - plan_min_y) * scale + y_offset)
                rect_w = int(room.width * scale)
                rect_h = int(room.height * scale)
                painter.drawRect(rect_x, rect_y, rect_w, rect_h)
                painter.setPen(Qt.black)
                painter.drawText(rect_x + 5, rect_y + 15, room.room_type)

        painter.setBrush(QColor(0, 255, 0))
        painter.setPen(QPen(Qt.darkGreen, 2))
        if self.entrances:
            for entrance in self.entrances:
                x = (entrance['x'] - plan_min_x) * scale + x_offset
                y = (entrance['y'] - plan_min_y) * scale + y_offset
                size = 6
                painter.drawEllipse(QPointF(x, y), size, size)