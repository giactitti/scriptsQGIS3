# -*- coding: utf-8 -*-
"""
/***************************************************************************
P-SARRET
        begin                : 2019-12
        copyright            : (C) 2019 by Stefano Crema, Giacomo Titti,
                               Alessandro Sarretta and Matteo Mantovani,
                               CNR-IRPI, Padova, Dec. 2019
        email                : giacomo.titti@irpi.cnr.it
 ***************************************************************************/

/***************************************************************************
    P-SARRET
    Copyright (C) 2019 by Stefano Crema, Giacomo Titti,Alessandro Sarretta
                          and Matteo Mantovani,CNR-IRPI, Padova, Dec. 2019

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
 ***********************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFolderDestination
                       )
from qgis import processing
import operator
import matplotlib.pyplot as plt
from datetime import datetime as dt
import numpy as np
import inspect
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.offline
import os


class psarret(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    ID = 'ID'
    DF = 'DF'
    START = 'START'
    END = 'END'
    DATE = 'DATE'
    FOLDER = 'FOLDER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return psarret()

    def name(self):
        return 'P-SARRET'

    def displayName(self):
        return self.tr('P-SARRET')

    def group(self):
        return self.tr('PS')

    def groupId(self):
        return 'P-SARRET'

    def shortHelpString(self):
        return self.tr("PS time-series")

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,self.tr('PS'),[QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.ID, 'ID', parentLayerParameterName=self.INPUT, defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.DF, 'Deformation Rate', parentLayerParameterName=self.INPUT, defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.START, 'Start period', parentLayerParameterName=self.INPUT, defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.END, 'End period', parentLayerParameterName=self.INPUT, defaultValue=None))
        self.addParameter(QgsProcessingParameterString(self.DATE, 'Format Date', defaultValue='%Y%m%d'))
        self.addParameter(QgsProcessingParameterFolderDestination(self.FOLDER, 'Folder destination of the graphs', defaultValue=None, createByDefault = True))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('PS selected'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters,self.INPUT,context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs())

        #feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        parameters['id'] = self.parameterAsString(parameters, self.ID, context)
        if parameters['id'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.ID))

        parameters['df'] = self.parameterAsString(parameters, self.DF, context)
        if parameters['df'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.DF))

        parameters['start'] = self.parameterAsString(parameters, self.START, context)
        if parameters['start'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.START))

        parameters['end'] = self.parameterAsString(parameters, self.END, context)
        if parameters['end'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.END))

        parameters['date'] = self.parameterAsString(parameters, self.DATE, context)
        if parameters['date'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.DATE))

        parameters['folder'] = self.parameterAsString(parameters, self.FOLDER, context)
        if parameters['folder'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FOLDER))
        print(parameters['folder'])

        if sink is None:
             raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        alg_params = {
            #'OUTPUT': parameters['outcsv'],
            'id':parameters['id'],
            'df':parameters['df'],
            'ps': source,
            'start': parameters['start'],
            'end': parameters['end'],
            'date': parameters['date'],
            'OUT': parameters['folder']
        }
        self.input(alg_params)

        # total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {self.OUTPUT: dest_id}

    def input(self,parameters):
        try:
            os.mkdir(parameters['OUT'])
        except:
            print('folder already exist')
        # Layer structure
        layer = parameters['ps']#iface.activeLayer()
        fields = layer.fields()
        DATES=[]
        ys=[]
        IDs=[]
        DFs=[]
        lr=[]
        #value=[]
        features = layer.getFeatures()#.Features()
        field_names = [field.name() for field in fields]
        start = field_names.index(parameters['start'])
        end = field_names.index(parameters['end'])
        #if len(features)>0:
            #plot single figure
        count=0
        for feat in features:
            count+=1
            attrs = feat.attributes()
            datetitle = field_names[start:end]
            DATE = [dt.strptime(xk,parameters['date']) for xk in datetitle]
            DATES.append(DATE)
            #date_strings = [d.strftime('%Y-%m-%d') for d in datetitle]
            y = attrs[start:end]#input desired range
            #IDs.append(attrs[0])
            ys.append(y)
            ID=feat[parameters['id']]
            IDs.append(feat[parameters['id']])
            DF=feat[parameters['df']]
            DFs.append(feat[parameters['df']])
            x = range(len(y))
            #coef = np.polyfit(x,y,1) #linear fit
            #poly1d_fn = np.poly1d(coef)
            #lr.append(coef[0])
            fig = go.Figure()
            title='ID: '+str(ID)+' - Deformation rate: '+str(DF)
            fig.update_layout(title=title)
            fig.add_trace(go.Scatter( x=DATE, y=y,mode='lines',name='ID '+str(ID)))
            #fig.add_trace(go.Scatter( x=DATE, y=poly1d_fn(x),line=dict(color='rgb(0,0,0)',width=4, dash='dash'),name='ID '+str(ID)))
            fig.add_trace(go.Scatter( x=DATE, y=y, mode='markers',marker=dict(color='rgb(0,0,0)'),name='ID '+str(ID)))
            fig.update_xaxes(title_text="<b>Date<b>")
            fig.update_yaxes(title_text="<b>Displacement (mm)<b>")
            plotly.offline.plot(fig, filename=parameters['OUT']+'/fig'+str(count)+'.html')

        #plot total figure
        fig = go.Figure()
        for t in range(len(ys)):
            name='ID: '+str(IDs[t])+' - Deformation rate: '+str(DFs[t])
            fig.add_trace(go.Scatter( x=DATES[t], y=ys[t], mode='lines+markers',name=name))
            fig.update_xaxes(title_text="<b>Date<b>")
            fig.update_yaxes(title_text="<b>Displacement (mm)<b>")
        plotly.offline.plot(fig, filename=parameters['OUT']+'/fig_tot.png')
