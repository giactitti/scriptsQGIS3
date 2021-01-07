#!/usr/bin/python
#coding=utf-8
"""
/***************************************************************************
LSD kernel graphs
        begin                : 2020-03
        copyright            : (C) 2020 by Giacomo Titti,
                               Padova, March 2020
        email                : giacomotitti@gmail.com
 ***************************************************************************/

/***************************************************************************
    LSD kernel graphs
    Copyright (C) 2020 by Giacomo Titti, Padova, March 2020

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

#in input la tabella attributi costruita usando le funzioni
#di saga: grid statistic for points, add raster values to points

from qgis.PyQt.QtCore import QCoreApplication,QVariant
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
                       QgsVectorLayer,
                       QgsRasterLayer,
                       QgsProject,
                       QgsField,
                       QgsFields,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFolderDestination
                       )
from qgis import processing
import gdal,ogr,osr
import numpy as np
import math
import operator
import random
from qgis import *
##############################
from osgeo import gdal,osr,ogr
import sys,os
import math
import csv
import matplotlib.pyplot as plt
from osgeo import gdal,osr,ogr
import sys
import math
import csv

# import plotly.tools as plotly_tools
# import plotly.graph_objs as go
# import chart_studio.plotly as py
# from IPython.display import HTML
# import chart_studio
# import plotly.offline
# from plotly.subplots import make_subplots

class statistic(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    STRING = 'STRING'
    FOLDER = 'FOLDER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return statistic()

    def name(self):
        return 'points kernel graphs'

    def displayName(self):
        return self.tr('04 Points kernel graphs')

    def group(self):
        return self.tr('Vector analysis')

    def groupId(self):
        return 'Vector analysis'

    def shortHelpString(self):
        return self.tr("from '03 Points Kernel Statistics' create graphs")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Points'), types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        #self.addParameter(QgsProcessingParameterNumber('BufferRadiousInPxl', 'Buffer radiou in pixels', type=QgsProcessingParameterNumber.Integer, defaultValue = 2,  minValue=1))
        #self.addParameter(QgsProcessingParameterFileDestination('outcsv', 'outcsv', '*.csv', defaultValue='/media/jack/MyBook/irpi/OutputPaperBRI/Travis/lsd06-2020.csv'))
        #self.addParameter(QgsProcessingParameterField('fieldID', 'fieldID', type=QgsProcessingParameterField.Any, parentLayerParameterName='lsd', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.STRING, 'ID field', parentLayerParameterName=self.INPUT, defaultValue=None))
        #self.addParameter(QgsProcessingParameterString(self.STRING, 'fieldID', multiLine=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterFolderDestination(self.FOLDER, 'Folder destination of the graphs', defaultValue=None, createByDefault = True))

        #self.addParameter(QgsProcessingParameterRasterLayer('slope', 'raster', defaultValue='/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/Data/Slope_SE_250m_3857Travis.tif'))
        #self.addParameter(QgsProcessingParameterVectorDestination('Out', 'out', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        #parameters['fieldID']='ev_id'

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}
        
        parameters['lsd'] = self.parameterAsVectorLayer(parameters, self.INPUT, context).source()
        if parameters['lsd'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        parameters['fieldID'] = self.parameterAsString(parameters, self.STRING, context)
        if parameters['fieldID'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.STRING))
            
        parameters['folder'] = self.parameterAsString(parameters, self.FOLDER, context)
        if parameters['folder'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FOLDER))

        # parameters['Out']='/tmp/lsdkernel.shp'
        # parameters['Out1']='/tmp/lsdkernel1.shp'
        # # Grid statistics for points
        # alg_params = {
        #     'COUNT': True,
        #     'GRIDS': parameters['slope'],
        #     'KERNEL_SIZE': parameters['BufferRadiousInPxl'],
        #     'KERNEL_TYPE': 0,
        #     'MAX': True,
        #     'MEAN': True,
        #     'MIN': True,
        #     'NAMING': 0,
        #     'POINTS': parameters['lsd'],
        #     'QUANTILE': 0,
        #     'RANGE': True,
        #     'STDDEV': True,
        #     'SUM': True,
        #     'VAR': True,
        #     'RESULT': parameters['Out']
        # }
        # outputs['GridStatisticsForPoints'] = processing.run('saga:gridstatisticsforpoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        # results['Out'] = outputs['GridStatisticsForPoints']['RESULT']
        #
        # # Add raster values to points
        # alg_params = {
        #     'GRIDS': parameters['slope'],
        #     'RESAMPLING': 0,
        #     'SHAPES': parameters['Out'],
        #     'RESULT': parameters['Out1']
        # }
        # outputs['AddRasterValuesToPoints'] = processing.run('saga:addrastervaluestopoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        #
        # vlayer = QgsVectorLayer(parameters['Out1'], 'kernel', "ogr")
        # QgsProject.instance().addMapLayer(rlayer)

        alg_params = {
            #'OUTPUT': parameters['outcsv'],
            'ID': parameters['fieldID'],
            'INPUT2': parameters['lsd'],
            'OUT': parameters['folder']
        }
        self.input(alg_params)

        #vlayer = QgsVectorLayer(parameters['Out1'], 'vector', "ogr")
        #QgsProject.instance().addMapLayer(vlayer)

        ##############################################


    def input(self,parameters):
        shapefile = parameters['INPUT2']
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(shapefile, 0)
        layer = dataSource.GetLayer()
        layerDefinition = layer.GetLayerDefn()
        list_field=[]
        for i in range(layerDefinition.GetFieldCount()):
            fieldname=[layerDefinition.GetFieldDefn(i).GetName()]
            list_field=list_field+fieldname
        count=0
        valuesrow={}
        for feature in layer:
            valuesrow[count] = [feature.GetField(j) for j in list_field]
            count+=1
        count=0
        valuesfield={}
        for ii in range(len(list_field)):
            vf=[]
            for i in range(len(valuesrow.keys())):
                vf=vf+[valuesrow[i][ii]]
                count+=1
            valuesfield[list_field[ii]]=vf
        #print(valuesfield['mean']==)
        matrice=np.array([np.asarray(valuesfield['real']),np.asarray(valuesfield['max']),
        valuesfield['min'],valuesfield['std'],valuesfield['sum'],
        valuesfield['average'],valuesfield['mean'],valuesfield['real3km']])
        #print(valuesfield['mean'])
        
        matrice = matrice[::, matrice[0,].argsort()]
        # Plot
        lista=['real','max','min','std','sum','average','mean','real3km']
        for i in range(8):
            fig=plt.figure()


            #plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[7,:])
            #plt.title('')
            plt.xlabel('landslides')
            plt.ylabel('Slope degree')
            plt.legend(lista[i],loc="upper left")
            plt.grid()

            plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[i,:])
            plt.savefig(parameters['OUT']+'/fig'+lista[i]+'.png',bbox_inches='tight')

            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[2,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[2]+'.png',bbox_inches='tight')
            #
            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[3,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[3]+'.png',bbox_inches='tight')
            #
            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[0,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[0]+'.png',bbox_inches='tight')
            #
            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[4,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[4]+'.png',bbox_inches='tight')
            #
            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[5,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[5]+'.png',bbox_inches='tight')
            #
            # plt.plot(np.arange(len(valuesfield['ev_id'])), matrice[6,:])
            # plt.savefig('/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis062020/fig_lsd'+'/fig'+lista[6]+'.png',bbox_inches='tight')

        #plt.show()

        # fig = make_subplots(specs=[[{"secondary_y": True}]])
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[0,:], mode="lines",name='true'), secondary_y=False)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[1,:], mode="lines",name='min'), secondary_y=False)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[2,:], mode="lines",name='max'), secondary_y=False)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[3,:], mode="lines",name='mean'), secondary_y=False)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[4,:], mode="lines",name='range'), secondary_y=False)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[6,:], mode="lines",name='variance'), secondary_y=True)
        # fig.add_trace(go.Scatter( x=np.arange(len(valuesfield['ev_id'])), y=matrice[7,:], mode="lines",name='std'), secondary_y=True)
        # fig.update_xaxes(title_text="<b>Landslides<b>")
        # fig.update_yaxes(title_text="<b>Slope degree</b>", secondary_y=False)
        # # plotly.offline.plot(fig, filename='/home/irpi/SinoItalian_Lab/Tier1_SouthAsia/OutputPaperBRI/Travis/'+'fig_contour_stat'+'.html')
