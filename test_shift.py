import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

app = QApplication(sys.argv)
win = QMainWindow()
fig = Figure()
canvas = FigureCanvas(fig)
ax = fig.add_subplot(111)
ax.plot([1, 2, 3])
win.setCentralWidget(canvas)

def onclick(event):
    print(f"Clicked! Key={event.key}")

canvas.mpl_connect('button_press_event', onclick)
# Uncomment to fix focus if needed:
# canvas.setFocusPolicy(Qt.StrongFocus)
# canvas.setFocus()

win.show()
# We won't run this interactively in bash because it's a GUI, but we know Qt canvas focus is an issue.
