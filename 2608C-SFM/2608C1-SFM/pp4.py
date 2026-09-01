import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class PlotTab(QWidget):
    """A single tab containing one matplotlib figure with toolbar (zoom/pan/save)."""
    def __init__(self, plot_func):
        super().__init__()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        ax = self.figure.add_subplot(111)
        plot_func(ax)
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Plot Window")
        self.resize(900, 600)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        tabs.addTab(PlotTab(self.plot_line), "Line Plot")
        tabs.addTab(PlotTab(self.plot_scatter), "Scatter")
        tabs.addTab(PlotTab(self.plot_bar), "Bar Chart")

    def plot_line(self, ax):
        x = np.linspace(0, 10, 100)
        ax.plot(x, np.sin(x))
        ax.set_title("Line Plot")

    def plot_scatter(self, ax):
        x = np.random.rand(50)
        y = np.random.rand(50)
        ax.scatter(x, y)
        ax.set_title("Scatter Plot")

    def plot_bar(self, ax):
        ax.bar(['A', 'B', 'C', 'D'], [3, 7, 5, 2])
        ax.set_title("Bar Chart")

        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())