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
        self.update_data()

    def init_ui(self):
        self.setWindowTitle('Live Job Tracking')
        self.setGeometry(100, 100, 1000, 600)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)  # Vertical spacing between layouts
        main_layout.setContentsMargins(10, 10, 10, 10)  # Left, Top, Right, Bottom margins
        
        # Date selection layout
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)  # Horizontal spacing between widgets
        
        # Calculate current week's Monday and Sunday
        current_date = QDate.currentDate()
        days_since_monday = current_date.dayOfWeek() - 1  # Qt uses 1 for Monday
        
        # Get this week's Monday
        this_monday = current_date.addDays(-days_since_monday)
        this_sunday = this_monday.addDays(6)  # Sunday is 6 days after Monday
        
        # Start date section
        start_date_layout = QHBoxLayout()
        start_date_layout.setSpacing(5)
        self.start_date = QDateEdit(self)
        self.start_date.setDate(this_monday)  # Set to this week's Monday
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.on_date_changed)
        start_label = QLabel("Start Date:")
        start_label.setFixedWidth(70)
        start_date_layout.addWidget(start_label)
        start_date_layout.addWidget(self.start_date)
        date_layout.addLayout(start_date_layout)
        
        # Add spacing between start and end date
        date_layout.addSpacing(30)
        
        # End date section
        end_date_layout = QHBoxLayout()
        end_date_layout.setSpacing(5)
        self.end_date = QDateEdit(self)
        self.end_date.setDate(this_sunday)  # Set to this week's Sunday
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.on_date_changed)
        end_label = QLabel("End Date:")
        end_label.setFixedWidth(70)
        end_date_layout.addWidget(end_label)
        end_date_layout.addWidget(self.end_date)
        date_layout.addLayout(end_date_layout)
        
        main_layout.addLayout(date_layout)
        
        # Add spacing before filter layout
        main_layout.addSpacing(10)
        
        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)  # Horizontal spacing between widgets
        
        # Stage filter
        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(5)
        stage_label = QLabel("Stage:")
        stage_label.setFixedWidth(50)
        self.stage_filter = QComboBox(self)
        self.stage_filter.addItems(['All', 'Sample Preparation', 'Testing', 'Other'])
        self.stage_filter.currentTextChanged.connect(self.update_data)
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self.stage_filter)
        filter_layout.addLayout(stage_layout)
        
        # View type selector
        view_layout = QHBoxLayout()
        view_layout.setSpacing(5)
        view_label = QLabel("View Type:")
        view_label.setFixedWidth(70)
        self.view_type = QComboBox(self)
        self.view_type.addItems(['Daily Count', 'Cumulative'])
        self.view_type.currentTextChanged.connect(self.update_data)
        view_layout.addWidget(view_label)
        view_layout.addWidget(self.view_type)
        filter_layout.addLayout(view_layout)
        
        # Add spacing before refresh button
        filter_layout.addSpacing(20)
        
        # Refresh button
        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.update_data)
        filter_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(filter_layout)
        
        # Add spacing before plot
        main_layout.addSpacing(20)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        main_layout.addWidget(self.plot_widget)
        
        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def on_date_changed(self):
        """Ensure dates always align to Monday-Sunday weeks."""
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        
        # If start date changed, adjust it to Monday and set end date to Sunday
        if self.sender() == self.start_date:
            # Adjust to Monday if needed
            days_to_monday = start_date.dayOfWeek() - 1
            if days_to_monday > 0:
                start_date = start_date.addDays(-days_to_monday)
                self.start_date.setDate(start_date)
            
            # Set end date to Sunday
            end_date = start_date.addDays(6)
            self.end_date.setDate(end_date)
        
        # If end date changed, adjust it to Sunday and set start date to Monday
        elif self.sender() == self.end_date:
            # Adjust to Sunday if needed
            days_to_sunday = 7 - end_date.dayOfWeek()
            if days_to_sunday < 7:
                end_date = end_date.addDays(days_to_sunday)
                self.end_date.setDate(end_date)
            
            # Set start date to Monday
            start_date = end_date.addDays(-6)
            self.start_date.setDate(start_date)
        
        self.update_data()

    def update_data(self):
        stage = self.stage_filter.currentText()
        stages = [stage] if stage != 'All' else None
        view_type = self.view_type.currentText()

        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        data = self.data_processor.get_data("MTEST", start_date, end_date, stages, view_type)
        self.update_plot(data, view_type)

    def update_plot(self, data, view_type):
        self.plot_widget.clear()
        
        # Define fixed order of stages and their colors
        STAGE_ORDER = ['Sample Preparation', 'Testing', 'Other']
        colors = {
            'Sample Preparation': pg.mkColor('#375E97'), #deep blue
            'Testing': pg.mkColor('#FB6542'),            #orange-red
            'Other': pg.mkColor('#FFBB00')               #yellow-orange
        }
        
        # Safely remove old legend
        if hasattr(self.plot_widget, 'legend') and self.plot_widget.legend is not None:
            try:
                self.plot_widget.legend.scene().removeItem(self.plot_widget.legend)
            except:
                pass
        
        df = data['aggregated_data']
        
        # Set y-axis range
        if df.empty:
            y_max = 5
        else:
            data_max = int(np.ceil(df.values.max()))
            y_max = max(5, data_max)
        
        self.plot_widget.setYRange(0, y_max)
        
        # Plot data if available
        if not df.empty:
            x = np.array([pd.Timestamp(date).timestamp() for date in df.index])
            
            if len(x) > 1:
                bar_width = (x[1] - x[0]) * 0.2
            else:
                bar_width = 86400 * 0.2
            
            x_offset = -bar_width
            # Use fixed order for plotting
            for stage in STAGE_ORDER:
                color = colors[stage]
                bars = pg.BarGraphItem(
                    x=x + x_offset,
                    height=df[stage].values,
                    width=bar_width,
                    brush=color,
                    name=stage
                )
                self.plot_widget.addItem(bars)
                x_offset += bar_width
        
        # Set labels
        y_label = 'Total Number of Jobs' if view_type == 'Cumulative' else 'Daily Number of Jobs'
        self.plot_widget.setLabel('left', y_label)
        self.plot_widget.setLabel('bottom', 'Date')
        
        # Set y-axis ticks
        y_axis = self.plot_widget.getAxis('left')
        y_ticks = [(i, str(i)) for i in range(y_max + 1)]
        y_axis.setTicks([y_ticks])
        
        # Set x-axis ticks if data exists
        if not df.empty:
            axis = self.plot_widget.getAxis('bottom')
            axis.setTicks([[(timestamp, pd.Timestamp(timestamp, unit='s').strftime('%a %Y-%m-%d')) 
                            for timestamp in x]])
        
        # Create legend with fixed order
        self.plot_widget.legend = self.plot_widget.addLegend(offset=(-750, 30))
        for stage in STAGE_ORDER:
            sample = pg.PlotDataItem(pen=colors[stage])
            self.plot_widget.legend.addItem(sample, stage)
        
        self.plot_widget.setBackground('black')
