########################################################################
# This script creates a GUI for the job tracking application.          #
########################################################################

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
        self.stage_filter.addItems(['All', 'Open', 'Sample Preparation', 'Testing', 'Report'])
        self.stage_filter.currentTextChanged.connect(self.update_data)
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self.stage_filter)
        filter_layout.addLayout(stage_layout)
        
        # Location filter
        location_layout = QHBoxLayout()
        location_layout.setSpacing(5)
        location_label = QLabel("Location:")
        location_label.setFixedWidth(70)
        self.location_filter = QComboBox(self)
        self.location_filter.addItems(['All', 'Toronto', 'Montreal', 'Edmonton'])
        self.location_filter.currentTextChanged.connect(self.update_data)
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_filter)
        filter_layout.addLayout(location_layout)
        
        # Unit filter
        unit_layout = QHBoxLayout()
        unit_layout.setSpacing(5)
        unit_label = QLabel("Unit:")
        unit_label.setFixedWidth(50)
        self.unit_filter = QComboBox(self)
        self.unit_filter.addItems(['Job Number', 'Test Number'])
        self.unit_filter.currentTextChanged.connect(self.update_data)
        unit_layout.addWidget(unit_label)
        unit_layout.addWidget(self.unit_filter)
        filter_layout.addLayout(unit_layout)
        
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
        """Ensure dates always align to Monday-Friday weeks."""
        # Store current dates before modification
        current_start = self.start_date.date()
        current_end = self.end_date.date()
        
        if self.sender() == self.start_date:
            # Adjust to Monday if needed
            days_to_monday = current_start.dayOfWeek() - 1
            if days_to_monday > 0:
                new_start = current_start.addDays(-days_to_monday)
            else:
                new_start = current_start
                
            # Set end date to Friday (4 days after Monday)
            new_end = new_start.addDays(4)
            
            # Only update if dates have changed
            if new_start != current_start:
                self.start_date.setDate(new_start)
            if new_end != current_end:
                self.end_date.setDate(new_end)
                
        elif self.sender() == self.end_date:
            # Adjust to Friday if needed
            days_to_friday = 5 - current_end.dayOfWeek()
            if days_to_friday != 0:
                new_end = current_end.addDays(days_to_friday)
            else:
                new_end = current_end
                
            # Set start date to Monday (4 days before Friday)
            new_start = new_end.addDays(-4)
            
            # Only update if dates have changed
            if new_end != current_end:
                self.end_date.setDate(new_end)
            if new_start != current_start:
                self.start_date.setDate(new_start)
        
        # Update data only if dates have actually changed
        if (current_start != self.start_date.date() or 
            current_end != self.end_date.date()):
            self.update_data()

    def update_data(self):
        stage = self.stage_filter.currentText()
        stages = [stage] if stage != 'All' else None
        
        location = self.location_filter.currentText()
        locations = [location] if location != 'All' else None
        
        unit = self.unit_filter.currentText()
        view_type = 'Cumulative'
        
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        data = self.data_processor.get_data(
            "MTEST", 
            start_date, 
            end_date, 
            stages, 
            view_type,
            locations,
            unit
        )
        self.update_plot(data, view_type, unit)

    def update_plot(self, data, view_type, unit):
        self.plot_widget.clear()
        
        # Disable mouse interactions
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.getPlotItem().getViewBox().setMenuEnabled(False)
        self.plot_widget.getPlotItem().getViewBox().setLimits(xMin=None, xMax=None, yMin=0, yMax=None)
        
        # Define fixed order of stages and their colors
        ALL_STAGES = ['Open', 'Sample Preparation', 'Testing', 'Report']
        colors = {
            'Open': pg.mkColor('#FFBB00'),
            'Sample Preparation': pg.mkColor('#375E97'),
            'Testing': pg.mkColor('#FB6542'),
            'Report': pg.mkColor('#008000')
        }
        
        # Only plot selected stage if not 'All'
        selected_stage = self.stage_filter.currentText()
        stages_to_plot = [selected_stage] if selected_stage != 'All' else ALL_STAGES
        
        # Remove old legend if it exists
        if hasattr(self, 'legend'):
            self.plot_widget.removeItem(self.legend)
            delattr(self, 'legend')
        
        df = data['aggregated_data']
        
        # Filter out weekends
        if not df.empty:
            df = df[df.index.map(lambda x: pd.Timestamp(x).weekday() < 5)]  # 0-4 are Monday-Friday
            
            x = np.array([pd.Timestamp(date).timestamp() for date in df.index])
            
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
                for stage in stages_to_plot:  # Only plot selected stages
                    if stage in colors:  # Make sure we have a color for this stage
                        color = colors[stage]
                        y_values = df[stage].fillna(0).values
                        
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
            
            # Update y-axis label based on unit
            y_label = f'Total {"Test" if unit == "Test Number" else "Job"} Numbers'
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
