
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class graphWindow(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 3), dpi=100)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.currentFrequency = 0.
        self.clearGraphs()
    
    def clearGraphs(self): 
        self.axes.cla()
        self.axes.set_xlabel('Frequency [Hz]')
        self.axes.set_ylabel('Mean Amplitude  [Pa]')
        self.fig.tight_layout()
        self.draw()
       
    def plot(self, x, y, col='k', lin='-', wid=1):
        self.axes.plot(x, y, color=col, linestyle=lin, linewidth=wid)
        self.fig.tight_layout()
        self.draw()
        
    def updateWindow(self, myModel): 
        self.clearGraphs()
        # Ampltudes of loads
        for load in myModel.loads:
            if load.drawCheck.isChecked(): 
                [x, y] = load.getXYdata()
                self.plot(x, y)
        # Vertical line at current Frequency
        self.plot([self.currentFrequency, self.currentFrequency], self.axes.get_ylim(), 'k', '--')
        # Set appropriate x/y limits
        self.axes.set_xlim([min(myModel.calculationObjects[0].frequencies), max(myModel.calculationObjects[0].frequencies)])
        # Redraw canvas
        self.draw()
    