########################################################################
# This is the main script that runs the live job tracking application. #
########################################################################

import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from data_processor import JiraDataProcessor

def main():
    app = QApplication(sys.argv)
    data_processor = JiraDataProcessor()
    window = MainWindow(data_processor)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()