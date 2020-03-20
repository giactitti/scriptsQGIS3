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
import processing
#import plotly.express as px
import numpy as np
import chart_studio.plotly as py
#import plotly.plotly as py
#import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.offline


class StatsOfPoints(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('ps', 'PS', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('v1', 'V1', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('v2', 'V2', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('field', 'field', type=QgsProcessingParameterField.Numeric, parentLayerParameterName='ps', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Masked', 'masked', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('Plotted', 'plotted', fileFilter='HTML files (*.html)', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('Out', 'out', optional=True, fileFilter='.csv files (*.csv)', createByDefault=True, defaultValue=None))

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

        # Bar plot
        alg_params = {
            'INPUT': outputs['ClipVectorByMaskLayer']['OUTPUT'],
            'NAME_FIELD': parameters['field'],
            #'VALUE_FIELD': QgsExpression('formula').evaluate(),
            'OUTPUT': parameters['Plotted']
        }
        self.barplot(alg_params)
        #outputs['BarPlot'] = processing.run('qgis:barplot', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        #results['Plotted'] = outputs['BarPlot']['OUTPUT']

        #feedback.setCurrentStep(3)
        #if feedback.isCanceled():
        #    return {}

        # Basic statistics for fields to csv
        alg_params = {
            'FIELD_NAME': parameters['field'],
            'INPUT_LAYER': outputs['ClipVectorByMaskLayer']['OUTPUT'],
            'OUTPUT_HTML_FILE': parameters['Out']
        }
        outputs['BasicStatisticsForFieldsToCsv'] = processing.run('script:basicstatisticsforfieldstocsv', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Out'] = outputs['BasicStatisticsForFieldsToCsv']['OUTPUT_HTML_FILE']
        return results

    def barplot(self,parameters):
        #shp = "D:\file.shp"
        layer = QgsVectorLayer(parameters['INPUT'],"capa","ogr")
        #driver = ogr.GetDriverByName('ESRI Shapefile')
        #dataSource = driver.Open(shp,0)
        #layer=dataSource.GetLayer()
        ValList = []
        count=1
        #idx = layer.fieldNameIndex(parameters['NAME_FIELD'])
        #print(feature.attributes()[idx])
        for feat in layer.getFeatures():
            #ValList.append(layer.getFeature(count).attributes()[2])
            ValList.append(feat[parameters['NAME_FIELD']])
            #print(ValList)
            count = count+1
        df = np.array(ValList)
        #fig = px.histogram(df, x="total_bill")
        fig = go.Figure(go.Histogram(x=df,autobinx=False,xbins={"size": 0.5}))
        #fig.show()
        plotly.offline.plot(fig, filename=parameters['OUTPUT'])

#        self.rebinnable_interactive_histogram(df, "air_time")
#        #py.iplot(data, filename='basic histogram')
#        #fig.show()
#
#    def rebinnable_interactive_histogram(self,series, initial_bin_width=10):
#        figure_widget = go.FigureWidget(
#            data=[go.Histogram(x=series, xbins={"size": initial_bin_width})]
#        )
#
#       bin_slider = widgets.FloatSlider(
#           value=initial_bin_width,
#            min=1,
#            max=30,
#            step=1,
#            description="Bin width:",
 #           readout_format=".0f",  # display as integer
##        )
#
 #       histogram_object = figure_widget.data[0]
#
 #       def set_bin_size(change):
#            histogram_object.xbins = {"size": change["new"]}
#
#        bin_slider.observe(set_bin_size, names="value")
#
#        output_widget = widgets.VBox([figure_widget, bin_slider])
#        return output_widget

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
