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
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Left, Top, Right, Bottom margins
        
        # Date selection layout
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        
        # Calculate current week's Monday and Sunday
        current_date = QDate.currentDate()
        days_since_monday = current_date.dayOfWeek() - 1  #1 for Monday
        
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
        filter_layout.setSpacing(10) 
        
        # Stage filter
        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(5)
        stage_label = QLabel("Stage:")
        stage_label.setFixedWidth(50)
        self.stage_filter = QComboBox(self)
        self.stage_filter.addItems(['All','open', 'Sample Preparation', 'Testing'])
        self.stage_filter.currentTextChanged.connect(self.update_data)
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self.stage_filter)
        filter_layout.addLayout(stage_layout)
        
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
        view_type = 'Cumulative'

        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        data = self.data_processor.get_data("MTEST", start_date, end_date, stages, view_type)
        self.update_plot(data, view_type)

    def update_plot(self, data, view_type):
        self.plot_widget.clear()
        
        # Disable mouse interactions
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.getPlotItem().getViewBox().setMenuEnabled(False)
        self.plot_widget.getPlotItem().getViewBox().setLimits(xMin=None, xMax=None, yMin=0, yMax=None)
        
        # Define fixed order of stages and their colors
        STAGE_ORDER = ['Open','Sample Preparation', 'Testing']
        colors = {
            'Open': pg.mkColor('#FFBB00'),               #yellow-orange
            'Sample Preparation': pg.mkColor('#375E97'), #deep blue
            'Testing': pg.mkColor('#FB6542')            #orange-red
        }
        
        # Remove old legend if it exists
        if hasattr(self, 'legend'):
            self.plot_widget.removeItem(self.legend)
            delattr(self, 'legend')
        
        df = data['aggregated_data']
        
        # Set y-axis range, handling NaN values
        if df.empty or df.isna().all().all():  # Check if DataFrame is empty or all NaN
            y_max = 5
        else:
            # Replace NaN with 0 before finding max
            data_max = int(np.ceil(df.fillna(0).values.max()))
            y_max = max(5, data_max)
        
        self.plot_widget.setYRange(0, y_max)
        
        # Create new legend first
        self.legend = self.plot_widget.addLegend(offset=(10, 10))
        
        # Plot data if available
        if not df.empty:
            x = np.array([pd.Timestamp(date).timestamp() for date in df.index])
            
            for stage in STAGE_ORDER:
                color = colors[stage]
                y_values = df[stage].fillna(0).values  # Replace NaN with 0
                
                # Create line plot
                plot_item = self.plot_widget.plot(
                    x=x,
                    y=y_values,
                    pen=pg.mkPen(color, width=2),
                    name=stage,
                    symbol='o',
                    symbolSize=8,
                    symbolBrush=color,
                    symbolPen=color
                )
                
                # Add value labels next to each point
                for i, (x_val, y_val) in enumerate(zip(x, y_values)):
                    if y_val > 0:
                        text = pg.TextItem(
                            text=str(int(y_val)),
                            color=color,
                            anchor=(0, 1)
                        )
                        self.plot_widget.addItem(text)
                        x_offset = (x[-1] - x[0]) * 0.001
                        text.setPos(x_val + x_offset, y_val)
        
        # Set labels
        y_label = 'Total Number of Jobs' if view_type == 'Cumulative' else 'Number of Jobs'
        self.plot_widget.setLabel('left', y_label)
        
        # Fix for x-axis label
        plot_item = self.plot_widget.getPlotItem()
        bottom_axis = plot_item.getAxis('bottom')
        bottom_axis.enableAutoSIPrefix(False)  # Disable SI prefix notation
        bottom_axis.setLabel('Date')  # Set label without any units
        
        # Set x-axis range
        self.plot_widget.getPlotItem().setXRange(
            min(x) - (x[-1] - x[0]) * 0.05,
            max(x) + (x[-1] - x[0]) * 0.05
        )
        
        # Set x-axis ticks
        bottom_axis.setTicks([[(timestamp, pd.Timestamp(timestamp, unit='s').strftime('%a %Y-%m-%d')) 
                            for timestamp in x]])
        
        y_axis = self.plot_widget.getAxis('left')
        if y_max <= 20:
            step = 1
        elif y_max <= 50:
            step = 5
        elif y_max <= 100:
            step = 10
        else:
            step = 20
        
        y_ticks = [(i, str(i)) for i in range(0, y_max + 1, step)]
        y_axis.setTicks([y_ticks])
        
        self.plot_widget.setBackground('black')
