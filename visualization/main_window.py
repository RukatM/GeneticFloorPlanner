import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,  QPushButton, QSlider, QFrame)
from PyQt5.QtCore import Qt

from .renderer import BuildingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Genetic Floor Planner")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)
        
        self.building_widget = BuildingWidget(None, []) 
        main_layout.addWidget(self.building_widget, 1)

        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

    def _create_top_bar(self):
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_panel.setStyleSheet("background-color: #333; color: white;")
        
        params_layout = QHBoxLayout()
        
        self.params_widgets = {} 

        pop_label = QLabel("Population Size:")
        pop_widget = QSpinBox()
        pop_widget.setRange(10, 1000)
        pop_widget.setValue(50)
        pop_widget.setMinimumWidth(60)
        self.params_widgets["Population Size:"] = pop_widget 
        params_layout.addWidget(pop_label)
        params_layout.addWidget(pop_widget)
        params_layout.addSpacing(20)

        gen_label = QLabel("Number of Generations:")
        gen_widget = QSpinBox()
        gen_widget.setRange(1, 10000)
        gen_widget.setValue(100)
        gen_widget.setMinimumWidth(60)
        self.params_widgets["Number of Generations:"] = gen_widget 
        params_layout.addWidget(gen_label)
        params_layout.addWidget(gen_widget)
        params_layout.addSpacing(20)

        tour_label = QLabel("Tournament Size:")
        tour_widget = QSpinBox()
        tour_widget.setRange(2, 20)
        tour_widget.setValue(3)
        tour_widget.setMinimumWidth(60)
        self.params_widgets["Tournament Size:"] = tour_widget 
        params_layout.addWidget(tour_label)
        params_layout.addWidget(tour_widget)
        params_layout.addSpacing(20)

        cross_label = QLabel("Crossover Probability:")
        cross_widget = QDoubleSpinBox()
        cross_widget.setRange(0.0, 1.0)
        cross_widget.setSingleStep(0.05)
        cross_widget.setValue(0.8)
        cross_widget.setMinimumWidth(60)
        self.params_widgets["Crossover Probability:"] = cross_widget 
        params_layout.addWidget(cross_label)
        params_layout.addWidget(cross_widget)
        params_layout.addSpacing(20)

        mut_label = QLabel("Mutation Probability:")
        mut_widget = QDoubleSpinBox()
        mut_widget.setRange(0.0, 1.0)
        mut_widget.setSingleStep(0.05)
        mut_widget.setValue(0.1)
        mut_widget.setMinimumWidth(60)
        self.params_widgets["Mutation Probability:"] = mut_widget 
        params_layout.addWidget(mut_label)
        params_layout.addWidget(mut_widget)
        
        params_layout.addStretch()
        
        top_layout.addLayout(params_layout)

        controls_layout = QHBoxLayout()
        self.file_label = QLabel("File: building.json")
        self.choose_file_button = QPushButton("Choose File")
        self.start_button = QPushButton("Start Evolution")
        self.start_button.setStyleSheet("font-size: 14px; padding: 5px 15px;")
        
        controls_layout.addWidget(self.file_label)
        controls_layout.addWidget(self.choose_file_button)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.start_button)
        controls_layout.addStretch()
        top_layout.addLayout(controls_layout)

        return top_panel
        
    def _create_bottom_bar(self):
        bottom_panel = QWidget()
        bottom_panel.setStyleSheet("background-color: #333; color: white;")
        bottom_layout = QHBoxLayout(bottom_panel)
        
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_label = QLabel("Generation: 0")
        self.save_button = QPushButton("Save Result")
        
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.iter_slider, 1) 
        bottom_layout.addWidget(self.iter_label)
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addSpacing(20)
        
        return bottom_panel

if __name__ == '__main__':

    class DummyBuildingWidget(QWidget):
        def __init__(self, individual, outline, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: #555;")
        def paintEvent(self, event):
            pass 
    
    BuildingWidget = DummyBuildingWidget

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())