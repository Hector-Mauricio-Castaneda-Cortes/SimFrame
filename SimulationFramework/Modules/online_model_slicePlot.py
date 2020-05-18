import sys, os, time, math, datetime, copy, re,  h5py
from collections import OrderedDict
import glob
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
sys.path.append(os.path.abspath(os.path.realpath(__file__)+'/../../../'))
import SimulationFramework.Modules.read_beam_file as raf
import SimulationFramework.Modules.read_twiss_file as rtf
from SimulationFramework.Modules.multiPlot import multiPlotWidget
sys.path.append(os.path.realpath(__file__)+'/../../../../')

class mainWindow(QMainWindow):
    def __init__(self):
        super(mainWindow, self).__init__()
        self.resize(1800,900)
        self.centralWidget = QWidget()
        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.tab = QTabWidget()
        self.slicePlot = slicePlotWidget()

        self.layout.addWidget(self.slicePlot)

        self.setCentralWidget(self.centralWidget)

        self.setWindowTitle("ASTRA Data Plotter")
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

class slicePlotWidget(multiPlotWidget):
    # Layout oder for the individual Tiwss plot items
    plotParams = [
        {'label': 'Horizontal Emittance (normalised)', 'quantity': 'slice_normalized_horizontal_emittance', 'units': 'm-rad', 'name': '&epsilon;<sub>n,x</sub>'},
        {'label': 'Vertical Emittance (normalised)', 'quantity': 'slice_normalized_vertical_emittance', 'units': 'm-rad', 'name': '&epsilon;<sub>n,y</sub>'},
        'next_row',
        {'label': 'Current', 'quantity': 'slice_peak_current', 'units': 'A', 'text': 'I', 'name': 'I'},
        {'label': 'Relative Momentum Spread', 'quantity': 'slice_relative_momentum_spread', 'units': '%', 'name': '&sigma;<sub>cp</sub>/p'},
        'next_row',
        {'label': 'Horizontal Beta Function', 'quantity': 'slice_beta_x', 'units': 'm', 'name': '&beta;<sub>x</sub>'},
        {'label': 'Vertical Beta Function', 'quantity': 'slice_beta_y', 'units': 'm', 'name': '&beta;<sub>y</sub>'},
    ]

    def __init__(self, **kwargs):
        super(slicePlotWidget, self).__init__(**kwargs)
        self.beams = {}
        self.slicePlotSliceWidthWidget = QSpinBox()
        self.slicePlotSliceWidthWidget.setMaximum(500)
        self.slicePlotSliceWidthWidget.setValue(100)
        self.slicePlotSliceWidthWidget.setSingleStep(10)
        self.slicePlotSliceWidthWidget.setSuffix(" slices")
        self.slicePlotSliceWidthWidget.setSpecialValueText('Automatic')
        self.slicePlotSliceWidthWidget.setMaximumWidth(150)
        # self.multiaxisPlotAxisLayout.addWidget(self.slicePlotSliceWidthWidget)
        self.slicePlotSliceWidthWidget.valueChanged.connect(self.changeSliceLengths)

    def addsliceDataFiles(self, dicts):
        '''
            add multiple data dictionaries

            Keyword arguments:
            dicts -- dictionary containing directory definitions:
                [
                    {'directory': <dir location>,           'filename': [<list of HDF5 beam files>]},
                    ...
                ]
        '''
        for d in dicts:
            self.addsliceDataFile(**d)

    def addsliceDataObject(self, beamobject, name):
        '''
            addsliceDirectory - read the data files in a directory and add a plotItem to the relevant slicePlotItems

            Keyword arguments:
            beamobject -- beam object
            name -- key index name
        '''
        ''' load the data files into the slice dictionary '''
        if str(type(beamobject)) == "<class 'SimulationFramework.Modules.read_beam_file.beam'>":
            self.beams[name] = beamobject
            beamobject.bin_time()
            color = self.colors[self.plotColor % len(self.colors)]
            pen = pg.mkPen(color, width=3, style=self.styles[int(self.plotColor / len(self.styles))])
            if name not in self.curves:
                self.curves[name] = {}
                self.plotColor += 1
            for n, param in enumerate(self.plotParams):
                if not param == 'next_row':
                    label = param['label']
                    # color = self.colors[n]
                    # pen = pg.mkPen(color=color, style=self.styles[self.plotColor % len(self.styles)], width=3)
                    exponent = np.floor(np.log10(np.abs(beamobject.slice_length)))
                    x = 10**(12) * np.array((beamobject.slice_bins - np.mean(beamobject.slice_bins)))
                    # self.multiPlot.setRange(xRange=[min(x),max(x)])
                    y = getattr(beamobject, param['quantity'])
                    # print('#################################################################')
                    # print(name, name in self.curves, label, self.curves)#, label, label in self.curves[name], self.curves[name])
                    # print('#################################################################')
                    if name in self.curves and label in self.curves[name]:
                        print('Updating curve: ', name, label)
                        self.updateCurve(x, y, name, label)
                    else:
                        print('ADDING curve: ', name, label)
                        self.addCurve(x, y, name, label, pen)


    def addsliceDataFile(self, directory, filename=None):
        '''
            addsliceDirectory - read the data files in a directory and call addsliceDataObject on the beam object

            Keyword arguments:
            directory -- location of beam file(s)
            filenames -- HDF5 filenames of beam file(s)
        '''
        if not isinstance(filename, (list, tuple)):
            filename = [filename]
        for f in filename:
            datafile = directory + '/' + f if f is not None else directory
            if os.path.isfile(datafile):
                beam = raf.beam()
                beam.read_HDF5_beam_file(datafile)
                self.addsliceDataObject(beam, datafile)

    def changeSliceLengths(self):
        ''' change the time slice length for all beam objects '''
        for d in self.beams:
            self.changeSliceLength(d)
        # self.updateMultiAxisPlot()

    def changeSliceLength(self, name):
        ''' change the time slice length for a beam data object and update the plot '''
        beam = self.beams[name]
        beam.slices = self.slicePlotSliceWidthWidget.value()
        beam.bin_time()
        for n, param in enumerate(self.plotParams):
            if not param == 'next_row':
                label = param['label']
                exponent = np.floor(np.log10(np.abs(beam.slice_length)))
                x = 10**(12) * np.array((beam.slice_bins - np.mean(beam.slice_bins)))
                # self.multiPlotWidgets[label].setRange(xRange=[min(x),max(x)])
                y = getattr(beam, param['quantity'])
                self.updateCurve(x, y, name, label)
                # self.curves[datafile][label].setData(x=x, y=y)

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
def main():
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    ex = mainWindow()
    ex.show()
    ex.multiPlot.addsliceDataFiles([
    {'directory': 'OnlineModel_test_data/basefiles_4_250pC', 'filename': 'CLA-S02-APER-01.hdf5'},
    {'directory': 'OnlineModel_test_data/test_4', 'filename': ['CLA-L02-APER.hdf5','CLA-S04-APER-01.hdf5']}])
    ex.multiPlot.addsliceDataFile('OnlineModel_test_data/test_4/CLA-S03-APER.hdf5')
    # ex.multiPlot.removePlot('base+4')
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()