from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox, QDateEdit, QLabel
from PyQt5.QtCore import QTimer, QDate
import pyqtgraph as pg
import pandas as pd
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self, data_processor):
        super().__init__()
        self.data_processor = data_processor
        self.init_ui()
        self.update_data()  # Initial data update

    def init_ui(self):
        self.setWindowTitle('Live Job Tracking')
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout()

        # Date selection
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit(self)
        self.start_date.setDate(QDate.currentDate().addDays(-6))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(QLabel("Start Date:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit(self)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(QLabel("End Date:"))
        date_layout.addWidget(self.end_date)

        layout.addLayout(date_layout)

        # Stage filter
        filter_layout = QHBoxLayout()
        self.stage_filter = QComboBox(self)
        self.stage_filter.addItems(['All', 'Sample Preparation', 'Testing', 'Other'])
        self.stage_filter.currentTextChanged.connect(self.update_data)
        filter_layout.addWidget(QLabel("Stage:"))
        filter_layout.addWidget(self.stage_filter)

        # Refresh button
        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.update_data)
        filter_layout.addWidget(self.refresh_button)

        layout.addLayout(filter_layout)

        # Plot area
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def on_date_changed(self):
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        if start_date.daysTo(end_date) != 6:
            if self.sender() == self.start_date:
                self.end_date.setDate(start_date.addDays(6))
            else:
                self.start_date.setDate(end_date.addDays(-6))
        self.update_data()

    def update_data(self):
        stage = self.stage_filter.currentText()
        stages = [stage] if stage != 'All' else None

        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        data = self.data_processor.get_data("MTEST", start_date, end_date, stages)
        self.update_plot(data)

    def update_plot(self, data):
        self.plot_widget.clear()
        df = data['aggregated_data']
        
        # Convert index to timestamp for plotting
        x = np.array([pd.Timestamp(date).timestamp() for date in df.index])
        
        colors = ['r', 'g', 'b', 'c', 'm', 'y']  # Add more colors if needed
        for i, stage in enumerate(df.columns):
            color = colors[i % len(colors)]
            self.plot_widget.plot(x, df[stage].values, name=stage, pen=color)
        
        self.plot_widget.setLabel('left', 'Total Number of Jobs')
        self.plot_widget.setLabel('bottom', 'Date')
        
        # Set x-axis tick format to display dates with weekday abbreviations
        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([[(timestamp, pd.Timestamp(timestamp, unit='s').strftime('%a %Y-%m-%d')) for timestamp in x]])
        
        # Add legend
        self.plot_widget.addLegend()
        
        # Set background to white
        self.plot_widget.setBackground('black')
