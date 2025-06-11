import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QSlider, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

from runner.runner import run_evolution
from .renderer import BuildingWidget


class MainWindow(QMainWindow):
    def __init__(self, comm):
        super().__init__()
        self.setWindowTitle("Genetic Floor Planner")
        self.setGeometry(100, 100, 1200, 800)

        self.comm = comm
        self.params = None
        self.config_file_path = None

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

        self.start_button.clicked.connect(self.start)
        self.choose_file_button.clicked.connect(self.open_file_dialog)


    def _create_top_bar(self):
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_panel.setStyleSheet("background-color: #333; color: white;")
        
        params_layout = QHBoxLayout()
        self.params_widgets = {} 
        pop_label = QLabel("Population Size:")
        pop_widget = QSpinBox(); pop_widget.setRange(10, 10000); pop_widget.setValue(500); pop_widget.setMinimumWidth(60)
        self.params_widgets["population_size"] = pop_widget
        params_layout.addWidget(pop_label); params_layout.addWidget(pop_widget); params_layout.addSpacing(20)
        gen_label = QLabel("Number of Generations:")
        gen_widget = QSpinBox(); gen_widget.setRange(1, 10000); gen_widget.setValue(500); gen_widget.setMinimumWidth(60)
        self.params_widgets["num_generations"] = gen_widget
        params_layout.addWidget(gen_label); params_layout.addWidget(gen_widget); params_layout.addSpacing(20)
        tour_label = QLabel("Tournament Size:")
        tour_widget = QSpinBox(); tour_widget.setRange(2, 20); tour_widget.setValue(6); tour_widget.setMinimumWidth(60)
        self.params_widgets["tournament_size"] = tour_widget
        params_layout.addWidget(tour_label); params_layout.addWidget(tour_widget); params_layout.addSpacing(20)
        cross_label = QLabel("Crossover Probability:")
        cross_widget = QDoubleSpinBox(); cross_widget.setRange(0.0, 1.0); cross_widget.setSingleStep(0.05); cross_widget.setValue(0.8); cross_widget.setMinimumWidth(60)
        self.params_widgets["crossover_prob"] = cross_widget
        params_layout.addWidget(cross_label); params_layout.addWidget(cross_widget); params_layout.addSpacing(20)
        mut_label = QLabel("Mutation Probability:")
        mut_widget = QDoubleSpinBox(); mut_widget.setRange(0.0, 1.0); mut_widget.setSingleStep(0.05); mut_widget.setValue(0.6); mut_widget.setMinimumWidth(60)
        self.params_widgets["mutation_prob"] = mut_widget
        params_layout.addWidget(mut_label); params_layout.addWidget(mut_widget)
        params_layout.addStretch()
        top_layout.addLayout(params_layout)

        controls_layout = QHBoxLayout()
        self.file_label = QLabel("")
        self.choose_file_button = QPushButton("Choose File")
        self.start_button = QPushButton("Start Evolution")
        self.start_button.setStyleSheet("font-size: 14px; padding: 5px 15px;")
        
        controls_layout.addWidget(self.file_label); controls_layout.addWidget(self.choose_file_button)
        controls_layout.addSpacing(20); controls_layout.addWidget(self.start_button)
        controls_layout.addStretch(); top_layout.addLayout(controls_layout)

        return top_panel


    def _create_bottom_bar(self):
        bottom_panel = QWidget()
        bottom_panel.setStyleSheet("background-color: #333; color: white;")
        bottom_layout = QHBoxLayout(bottom_panel)
        self.iter_slider = QSlider(Qt.Horizontal); self.iter_label = QLabel("Generation: 0")
        self.save_button = QPushButton("Save Result")
        bottom_layout.addSpacing(20); bottom_layout.addWidget(self.iter_slider, 1) 
        bottom_layout.addWidget(self.iter_label); bottom_layout.addWidget(self.save_button)
        bottom_layout.addSpacing(20)
        return bottom_panel


    def open_file_dialog(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Wybierz plik konfiguracyjny", "", "JSON Files (*.json);;All Files (*)", options=options)
        if filePath:
            self.config_file_path = filePath
            self.file_label.setText(f"Wybrany plik: {os.path.basename(filePath)}")
            print(f"Wybrano nowy plik konfiguracyjny: {self.config_file_path}")


    def start(self):
        if not self.config_file_path:
            QMessageBox.warning(self, "Brak pliku", "Proszę wybrać plik konfiguracyjny przed rozpoczęciem ewolucji.")
            return

        self.params = {
            key: widget.value() for key, widget in self.params_widgets.items()
        }

        self.params['config_file'] = self.config_file_path

        size = self.comm.Get_size()

        for worker in range(1, size):
            self.comm.send("START", dest=worker, tag=900)

        run_evolution(self.comm, self.params)


    def get_params(self):
        return self.params


    def closeEvent(self, a0):
        size = self.comm.Get_size()

        for worker in range(1, size):
            self.comm.send("STOP", dest=worker, tag=900)
