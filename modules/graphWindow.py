
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class graphWindow(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 3), dpi=100)
        FigureCanvas.__init__(self, self.fig)
        self.fig.set_label('mainFig')
        self.fig.tight_layout()
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.setLabels('Frequency [Hz]', 'Mean Amplitude  [Pa]')
        self.setAxesLimits([0, 100.],[0, 1.])
        self.axes.grid(1)
        self.currentFrequency = 10.
        #self.frequencyLine = self.fig.gca().plot([self.currentFrequency, self.currentFrequency+1], [0, 1], 'k', '--')
        self.frequencyLine = self.axes.plot([self.currentFrequency, self.currentFrequency], [0, 1], linestyle='--', color='k')
        self.currentPlotX = 0
        self.currentPlotY = 0
        self.draw()
    
    def setLabels(self, xlabel, ylabel): 
        self.axes.set_xlabel(str(xlabel))
        self.axes.set_ylabel(str(ylabel))
        self.draw()
    
    def setAxesLimits(self, xlim, ylim): 
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)
        self.draw()
       
    def plot(self, x, y, myLabel, col='k', lin='-', wid=1):
        for artist in self.fig.gca().lines + self.fig.gca().collections:
          artist.remove()
        self.currentPlotX = x
        self.currentPlotY = y
        self.axes.plot(x, y, color=col, linestyle=lin, linewidth=wid, label=myLabel)
        self.setAxesLimits([min(x), max(x)], [min(y), max(y)])
        self.axes.legend()
        self.frequencyLine = self.axes.plot([self.currentFrequency, self.currentFrequency], self.axes.get_ylim(), linestyle='--', color='k')
        self.draw()
        
    def updateWindow(self, myModel): 
        for artist in self.fig.gca().lines + self.fig.gca().collections:
            artist.remove()
        # Amplitudes of loads
        for load in myModel.loads:
            if load.drawCheck.isChecked(): 
                [x, y, color] = load.getXYdata()
                self.plot(x, y, color)
        #self.setLabels('Frequency [Hz]', 'Mean Amplitude  [Pa]')
        # Set appropriate x/y limits
        self.axes.set_xlim([min(myModel.frequencies), max(myModel.frequencies)])
        # Vertical line at current Frequency
        self.frequencyLine = self.axes.plot([self.currentFrequency, self.currentFrequency], self.axes.get_ylim(), linestyle='--', color='k')
        # Redraw canvas
        self.draw()
    
    def updateFrequencySelector(self):
        self.frequencyLine.pop(0).remove()
        self.frequencyLine = self.axes.plot([self.currentFrequency, self.currentFrequency], self.axes.get_ylim(), linestyle='--', color='k')
        self.draw()
    
    def saveDataPicture(self, fileName):
      print(fileName)
      self.fig.savefig(fileName, dpi = 300)
      
    def saveDataAscii(self, fileName):
      if self.currentPlotX != 0: 
        myArray = np.zeros((len(self.currentPlotX), 2))
        myArray[:,0] = self.currentPlotX
        myArray[:,1] = self.currentPlotY
        np.savetxt(fileName, myArray)
      #self.fig.savefig(fileName, dpi = 300)