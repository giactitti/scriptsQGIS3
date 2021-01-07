#!/usr/bin/python
#coding=utf-8
"""
/***************************************************************************
    01 Class Pixel Counter
        begin                : 2020-12
        copyright            : (C) 2019 by Giacomo Titti CNR-IRPI, Padova, Dec. 2020
        email                : giacomotitti@gmail.com
 ***************************************************************************/

/***************************************************************************
    01 Class Pixel Counter                            
    Copyright (C) 2020 by Giacomo Titti,CNR-IRPI, Padova, Dec. 2020          

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsMessageLog,
                       Qgis,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFile)
from qgis import processing
#import jenkspy
import gdal,ogr
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import roc_auc_score
import math
import operator
import matplotlib.pyplot as plt
import csv

class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'lsi'
    FILE = 'class'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        return 'pixel counter'

    def displayName(self):
        return self.tr('01 Class Pixel Counter')

    def group(self):
        return self.tr('Raster analysis')

    def groupId(self):
        return 'Raster analysis'

    def shortHelpString(self):
        return self.tr("Calculate the % of area covered by classes on raster")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, 'Raster', defaultValue=None))
        #self.addParameter(QgsProcessingParameterFileDestination('out', 'out', '*.txt', defaultValue=None))
        self.addParameter(QgsProcessingParameterFile(self.FILE, 'Txt classes', QgsProcessingParameterFile.File, '', defaultValue=None))
        



    def processAlgorithm(self, parameters, context, model_feedback):
        parameters['lsi'] = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if parameters['lsi'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        parameters['class'] = self.parameterAsFile(parameters, self.FILE, context).source()
        if parameters['class'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FILE))

        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}
        # Input
        alg_params = {
            'INPUT': inLayer.source()
        }
        outputs['open']=self.raster2array(alg_params)
        #list_of_values=list(np.arange(10))
        #self.list_of_values=outputs['open'][outputs['open']>-9999].reshape(-1)
        #QgsMessageLog.logMessage(str(len(self.list_of_values)), 'MyPlugin', level=Qgis.Info)

        alg_params = {
            'INPUT': outputs['open'],
            'INPUT1': parameters['class']
        }
        outputs['class']=self.classification(alg_params)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        return results

    def raster2array(self,parameters):
        self.ds22 = gdal.Open(parameters['INPUT'])
        if self.ds22 is None:#####################verify empty row input
            #QgsMessageLog.logMessage("ERROR: can't open raster input", tag="WoE")
            raise ValueError  # can't open raster input, see 'WoE' Log Messages Panel
        self.gt=self.ds22.GetGeoTransform()
        self.xsize = self.ds22.RasterXSize
        self.ysize = self.ds22.RasterYSize
        #print(w,h,xmin,xmax,ymin,ymax,self.xsize,self.ysize)
        aa=self.ds22.GetRasterBand(1)
        NoData=aa.GetNoDataValue()
        matrix = np.array(aa.ReadAsArray())
        bands = self.ds22.RasterCount
        if bands>1:#####################verify bands
            #QgsMessageLog.logMessage("ERROR: input rasters shoud be 1-band raster", tag="WoE")
            raise ValueError  # input rasters shoud be 1-band raster, see 'WoE' Log Messages Panel
        return matrix

    def classification(self,parameters):###############classify causes according to txt classes
        Min={}
        Max={}
        clas={}
        matrix=parameters['INPUT']
        with open(parameters['INPUT1'], 'r') as f:
            c = csv.reader(f,delimiter=' ')
            count=1
            for cond in c:
                b=np.array([])
                b=np.asarray(cond)
                Min[count]=b[0].astype(np.float32)
                Max[count]=b[1].astype(np.float32)
                clas[count]=b[2]#.astype(int)
                count+=1
        key_max=None
        key_min=None
        key_max = max(Max.keys(), key=(lambda k: Max[k]))
        key_min = min(Min.keys(), key=(lambda k: Min[k]))
        a={}
        a[0]=np.count_nonzero(matrix>-9999)
        print(a[0])
        with open('/tmp/classes.csv', 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile)
            for i in range(1,count):
                a[clas[i]]=np.count_nonzero((matrix>=Min[i])&(matrix<Max[i]))
                print(Min[i],' <= ',a[clas[i]]/a[0]*100,' < ',Max[i])
                print(a[clas[i]])
                spamwriter.writerow([Min[i],' <= ',a[clas[i]]/a[0]*100,' < ',Max[i]])

            #self.matrix[(self.matrix>=Min[i])&(self.matrix<Max[i])]=clas[i]
