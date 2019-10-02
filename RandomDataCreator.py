import json
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit
import vtk
import numpy as np
import math, cmath, random, time
import os
from lxml import etree
from standardWidgets import removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load

import matplotlib.pyplot as plt



class timeVarDat(load):
    def __init__(self):
        super(timeVarDat, self).__init__()






        dimx = 8
        dimy = 4
        dimz = 1
        points = dimx*dimy*dimz         #number of points

        ##create point set
        self.pointset = []
        for x in np.arange(-0.3, 0.7, 0.2):
            for y in np.arange(-0.3, 0.1, 0.2):
                for z in range(dimz):
                    self.pointset.append(str([x,y,z]))

        ##create SPL set
        sample_rate = 1024 #acc. to nyquist: gives us frequencies up to 512Hz. To get higher freqs, a higher sample rate is needed.
        dt = 1.0/sample_rate
        t = np.arange(sample_rate)*dt  # 1 second of samples
        freq = 440
        amp = 1.0

        self.splset = []
        for x in range (points):
            rand = random.randint(-50,50)

            sine1 = amp*np.sin(2*np.pi*freq*t)
            sine2 = .2*np.sin(2*np.pi*(freq+rand)*t)
            sinsum = sine1 + sine2
            self.splset.append(sinsum.tolist())

        self.sp = [[-0.7, -0.30000000000000004, 0.0], [-0.7000000000000001, 0.10000000000000004, 0.0], [-0.9000000000000001, -0.2, 0.0], [-0.7000000000000001, -0.1, 0.0], [-0.5000000000000001, -0.3, 0.0]]

        #self.sp = [[0.7, 0.3, 0.0], [0.5, 0.3, 0.0], [0.30000000000000004, 0.3, 0.0], [0.1, 0.3, 0.0], [-0.1, 0.3, 0.0], [-0.3, 0.3, 0.0], [-0.5, 0.3, 0.0], [-0.7000000000000001, 0.3, 0.0], [0.7, 0.1, 0.0], [0.5, 0.1, 0.0], [0.30000000000000004, 0.1, 0.0], [0.1, 0.1, 0.0], [-0.1, 0.1, 0.0], [-0.3, 0.1, 0.0], [-0.5, 0.1, 0.0], [-0.7000000000000001, 0.1, 0.0], [0.7, -0.1, 0.0], [0.5, -0.1, 0.0], [0.30000000000000004, -0.1, 0.0], [0.1, -0.1, 0.0], [-0.1, -0.1, 0.0], [-0.3, -0.1, 0.0], [-0.5, -0.1, 0.0], [-0.7000000000000001, -0.1, 0.0], [0.7, -0.30000000000000004, 0.0], [0.5, -0.30000000000000004, 0.0], [0.30000000000000004, -0.30000000000000004, 0.0], [0.1, -0.30000000000000004, 0.0], [-0.1, -0.30000000000000004, 0.0], [-0.3, -0.30000000000000004, 0.0], [-0.5, -0.30000000000000004, 0.0], [-0.7000000000000001, -0.30000000000000004, 0.0]]

        self.filename = 'randdat5.json'
        self.saveData()
        #datanew = self.loadData(self.filename)
        #print(self.ld.keys(), len(self.ld.keys()))
        self.nearestNeighbor()
        self.timeToFreq()
        self.matchDataPoints()
        self.getPhases()


    ##create data container
    def saveData(self):
        data = dict(zip(self.pointset, self.splset))
        # print(data.get((1,0,0))
        with open('randdatSmall.json', 'w') as f:
            json.dump(data, f)

    ##load data

    def loadData(self, filename):
        with open(filename) as f:
            ld = json.load(f)
        keys = list(ld.keys())
        values = ld.values()
        for npt, pt in enumerate(keys):
            ptlist = pt[1:-1].split(',')
            keys[npt] = [float(x.strip()) for x in ptlist]
        keystup = [tuple(point) for point in keys]
        self.ld = dict(zip(keystup, values))
        self.ldkeys = keys
        self.timeValues = list(values)
        #print(self.timeValues[2])
        ## aus Tupeln dringend Listen machen. Die als String in der dict speichern.
        ## Problem ist nämlich: Werte in Tupeln werden ungeordnet gespeichert. Das wirft evtl. die Koordinaten durcheinander.
        ## Die werden ja eh ständig in Listen und strings konvertiert.



    #print(datanew)


    def nearestNeighbor(self):
        #self.findRelevantPoints()
        surfdata = np.array(self.sp)
        #xyzdata = np.array([list(x) for x in list(self.ld.keys())])
        xyzdata = np.array(self.ldkeys)
        #np.random.shuffle(xyzdata)
        dist = np.empty(shape=(len(xyzdata), len(surfdata), 3))
        for k in range(len(xyzdata)):
            for i in range(len(surfdata)):
                diff = (xyzdata[k] - surfdata[i])
                dist[k,i,0] = diff[0]
                dist[k,i,1] = diff[1]
                dist[k,i,2] = diff[2]

        eucl = np.sqrt(np.square(dist[:,:,0]) + np.square(dist[:,:,1]) + np.square(dist[:,:,2]))
        self.euclNearest = []
        #a = eucl[22]
        #b = a.argsort()
        #print(eucl, a, b, len(b))
        for p in range(len(eucl)):
            self.euclNearest.append(eucl[p].argsort()[0])
        print(euclNearest, len(euclNearest))



    ## combines nearest points and data
    def matchDataPoints(self):
        self.FreqData = [0 for x in self.sp]#np.zeros(shape=(len(self.sp)))
        i=0
        for x in self.euclNearest:
            self.FreqData[x] = self.FreqValues[i]
            i+=1
        print(self.euclNearest, self.FreqData[0][123])
        #surfaceTimeData = dict(zip([(str(list(self.sp[x]))) for x in self.euclNearest], self.ld.values()))
        #print(surfaceTimeData.keys(), len(surfaceTimeData.keys()))


    def timeToFreq(self):
        self.FreqValues = []
        self.freqLenVec = []
        for nd, data in enumerate(self.timeValues):
            N=len(data)
            T=1/N
            Y = np.fft.fft(np.array(data))
            yf = 2.0/N * (Y[:N//2])
            self.FreqValues.append(yf.tolist())
            xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
            self.freqLenVec.append(len(xf))
        print(self.freqLenVec)
            #fig, ax = plt.subplots()
            #ax.plot(xf, 2.0/N * np.abs(yf[:N//2]))
            #plt.show()

    def getPhases(self):
        self.surfacePhases = np.zeros((max(self.freqLenVec),len(self.sp)))
        for nf in range(max(self.freqLenVec)):
            for ne in range(len(self.sp)):
                if self.FreqData[ne] == 0:
                    self.surfacePhases[nf,ne] = 0
                else:
                    self.surfacePhases[nf,ne] = cmath.phase(self.FreqData[ne][nf])
        print(self.surfacePhases)




start = timeVarDat()













##
