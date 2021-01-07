"""
Model exported as python.
Name : StatPlotly
Group :
With QGIS : 31200
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingParameterExpression
import processing
#import plotly.express as px
import numpy as np
import chart_studio.plotly as py
#import plotly.plotly as py
#import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.offline
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsMessageLog
from qgis.core import Qgis


class StatsOfPoints(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('ps', self.tr('PS'), types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('v1', self.tr('Polygon 1'), types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('v2', self.tr('Polygon 2'), types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        #self.addParameter(QgsProcessingParameterField('field', 'field', type=QgsProcessingParameterField.Numeric, parentLayerParameterName='ps', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('Plotted', self.tr('Plots of PS distribution'), fileFilter='HTML files (*.html)', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('Out', self.tr('PS statistics'), optional=True, fileFilter='.csv files (*.csv)', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterExpression('formula', self.tr('New field values calculated by formula for PS statistics'), parentLayerParameterName='ps', defaultValue=''))
        self.addParameter(QgsProcessingParameterVectorDestination('Masked', self.tr('PS clipped by Poly 1 and Poly 2 intersection'), type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Intersectionpoly
        alg_params = {
            'INPUT': parameters['v1'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['v2'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Intersectionpoly'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Clip vector by mask layer
        alg_params = {
            'INPUT': parameters['ps'],
            'MASK': outputs['Intersectionpoly']['OUTPUT'],
            'OPTIONS': '',
            'OUTPUT': parameters['Masked']
        }
        outputs['ClipVectorByMaskLayer'] = processing.run('gdal:clipvectorbypolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Masked'] = outputs['ClipVectorByMaskLayer']['OUTPUT']


        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Field calculator

        # # Advanced Python field calculator
        # alg_params = {
        #     'FIELD_LENGTH': 10,
        #     'FIELD_NAME': 'NewField',
        #     'FIELD_PRECISION': 3,
        #     'FIELD_TYPE': 1,
        #     'FORMULA': '',
        #     'GLOBAL': parameters['formula'],
        #     'INPUT': outputs['ClipVectorByMaskLayer']['OUTPUT'],
        #     'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        # }
        # outputs['AdvancedPythonFieldCalculator'] = processing.run('qgis:advancedpythonfieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'NewField',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': parameters['formula'],
            'INPUT': outputs['ClipVectorByMaskLayer']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': '/tmp/newfield.shp'
        }
        outputs['FieldCalculator'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        #results['Masked'] = outputs['FieldCalculator']['OUTPUT']


        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}


        # Bar plot
        alg_params = {
            'INPUT': outputs['FieldCalculator']['OUTPUT'],
            'NAME_FIELD': 'NewField',
            'OUTPUT': parameters['Plotted']
        }
        self.barplot(alg_params)


        # feedback.setCurrentStep(4)
        # if feedback.isCanceled():
        #     return {}

        # Basic statistics for fields to csv
        alg_params = {
            'FIELD_NAME': 'NewField',
            'INPUT_LAYER': outputs['FieldCalculator']['OUTPUT'],
            'OUTPUT_HTML_FILE': parameters['Out']
        }
        outputs['BasicStatisticsForFieldsToCsv'] = processing.run('script:basicstatisticsforfieldstocsv', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Out'] = outputs['BasicStatisticsForFieldsToCsv']['OUTPUT_HTML_FILE']
        return results

    def barplot(self,parameters):
        #shp = "D:\file.shp"
        QgsMessageLog.logMessage(parameters['INPUT'], 'MyPlugin', level=Qgis.Info)
        layer = QgsVectorLayer(parameters['INPUT'],"capa","ogr")
        count=1
        ValList=[]
        for feat in layer.getFeatures():
            ValList.append(feat[parameters['NAME_FIELD']])
            count = count+1
        df = np.array(ValList)
        #fig = px.histogram(df, x="total_bill")
        fig = go.Figure(go.Histogram(x=df,autobinx=False,xbins={"size": 0.5}))
        #fig.show()
        plotly.offline.plot(fig, filename=parameters['OUTPUT'])

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'StatsPlotly'

    def shortHelpString(self):
        return self.tr("Select two polygon to be intersected and to mask the PS layer. The statistics of the group of points PS selected is saved in .csv file (median, std, max, ...) and then the density distribution is plotted.")

    def displayName(self):
        return 'StatsPlotly'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return StatsOfPoints()
