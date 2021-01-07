#!/usr/bin/python
#coding=utf-8
"""
/***************************************************************************
    Points Sampler
        begin                : 2020-03
        copyright            : (C) 2020 by Giacomo Titti,
                               Padova, March 2020
        email                : giacomotitti@gmail.com
 ***************************************************************************/

/***************************************************************************
    Points Sampler
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
                       QgsProcessingParameterVectorDestination
                       )
from qgis import processing
#import jenkspy
import gdal,ogr,osr
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import roc_auc_score
import math
import operator
import matplotlib.pyplot as plt
import random
from qgis import *
from processing.algs.gdal.GdalUtils import GdalUtils

class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'lsd'
    OUTPUT1 = 'vout'
    OUTPUT2 = 'tout'
    MASK = 'poly'
    NUMBER = 'w'
    NUMBER1 = 'h'
    NUMBER2 = 'train'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        return 'points sampler'

    def displayName(self):
        return self.tr('05 Points Sampler')

    def group(self):
        return self.tr('Vector analysis')

    def groupId(self):
        return 'Vector analysis'

    def shortHelpString(self):
        return self.tr("Sample randomly training and validating datasets separated by grid cells")

    def initAlgorithm(self, config=None):
        # self.addParameter(QgsProcessingParameterRasterLayer('lsi', 'lsi', defaultValue=None))
        # self.addParameter(QgsProcessingParameterFileDestination('edgesJenks', 'edgesJenks', '*.txt', defaultValue=None))
        # self.addParameter(QgsProcessingParameterFileDestination('edgesEqual', 'edgesEqual', '*.txt', defaultValue=None))
        # self.addParameter(QgsProcessingParameterNumber('classes', 'classes', type=QgsProcessingParameterNumber.Integer, defaultValue = None,  minValue=0))
        # self.addParameter(QgsProcessingParameterVectorLayer('lsd', self.tr('Landslides'), types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        # self.addParameter(QgsProcessingParameterFileDestination('edgesGA', 'edgesGA', '*.txt', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Points'), types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer(self.MASK, self.tr('Contour polygon'), types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBER, 'Pixel width', type=QgsProcessingParameterNumber.Integer, defaultValue = 0,  minValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBER1, 'Pixel height', type=QgsProcessingParameterNumber.Integer, defaultValue = 0,  minValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBER2, 'Sample (%)', type=QgsProcessingParameterNumber.Integer, defaultValue = 0,  minValue=0))
        #self.addParameter(QgsProcessingParameterFeatureSink('tout', 'tout', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue='/home/irpi/r.shp'))
        #self.addParameter(QgsProcessingParameterFeatureSink('vout', 'vout', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue='/home/irpi/v.shp'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT1, 'Layer of sample', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT2, 'Layer of 1-sample', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))




    def processAlgorithm(self, parameters, context, model_feedback):

        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        

        parameters['lsd'] = self.parameterAsVectorLayer(parameters, self.INPUT, context).source()
        if parameters['lsd'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        parameters['poly'] = self.parameterAsVectorLayer(parameters, self.MASK, context).source()
        if parameters['poly'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.MASK))
            
        parameters['w'] = self.parameterAsInt(parameters, self.NUMBER, context)
        if parameters['w'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.NUMBER))
            
        parameters['h'] = self.parameterAsInt(parameters, self.NUMBER1, context)
        if parameters['h'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.NUMBER1))
        
        parameters['train'] = self.parameterAsInt(parameters, self.NUMBER2, context)
        if parameters['train'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.NUMBER2))
        
        #parameters['vout']=self.parameterAsSink(parameters,self.OUTPUT1,context)
        #if parameters['vout'] is None:
        #    raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT1))
            
        outFile1 = self.parameterAsOutputLayer(parameters, self.OUTPUT1, context)
        parameters['vout'], outputFormat = GdalUtils.ogrConnectionStringAndFormat(outFile1, context)
        if parameters['vout'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT1))
            
        #parameters['tout']=self.parameterAsSink(parameters,self.OUTPUT2,context)
        #if parameters['tout'] is None:
        #    raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT2))
        
        outFile1 = self.parameterAsOutputLayer(parameters, self.OUTPUT2, context)
        parameters['tout'], outputFormat = GdalUtils.ogrConnectionStringAndFormat(outFile1, context)
        if parameters['tout'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT2))

        alg_params = {
            'INPUT': parameters['lsd'],
            'INPUT1': parameters['poly'],
            'w': parameters['w'],
            'h': parameters['h'],
            'train': parameters['train']
        }
        v,t,xy=self.resampler(alg_params)
        outputs['V'] = v
        outputs['T'] = t
        outputs['xy'] = xy

        alg_params = {
            'INPUT1': parameters['vout'],
            'INPUT2': outputs['V'],
            'INPUT3': outputs['xy']
        }
        self.save(alg_params)

        alg_params = {
            'INPUT1': parameters['tout'],
            'INPUT2': outputs['T'],
            'INPUT3': outputs['xy']
        }
        self.save(alg_params)


        vlayer = QgsVectorLayer(parameters['vout'], 'valid', "ogr")
        QgsProject.instance().addMapLayer(vlayer)


        vlayer1 = QgsVectorLayer(parameters['tout'], 'train', "ogr")
        QgsProject.instance().addMapLayer(vlayer1)

        # # Extract layer extent
        # alg_params = {
        #     'INPUT': parameters['poly'],
        #     'ROUND_TO': 0,
        #     'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        # }
        # outputs['ExtractLayerExtent'] = processing.run('native:polygonfromlayerextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        return results

    def resampler(self,parameters):
        self.poly=parameters['INPUT1']
        vlayer = QgsVectorLayer(self.poly, "layer", "ogr")
        ext=vlayer.extent()#xmin
        self.xmin = ext.xMinimum()
        self.xmax = ext.xMaximum()
        self.ymin = ext.yMinimum()
        self.ymax = ext.yMaximum()
        self.newXNumPxl=(np.ceil(abs(self.xmax-self.xmin)/(parameters['w']))-1).astype(int)
        self.newYNumPxl=(np.ceil(abs(self.ymax-self.ymin)/(parameters['h']))-1).astype(int)
        self.xsize=self.newXNumPxl
        self.ysize=self.newYNumPxl
        self.origine=[self.xmin,self.ymax]
        #########################################

        #try:
        dem_datas=np.zeros((self.ysize,self.xsize),dtype='int64')
        # write the data to output file
        rf1='/tmp/inv_sampler.tif'
        dem_datas1=np.zeros(np.shape(dem_datas),dtype='float32')
        dem_datas1[:]=dem_datas[:]#[::-1]
        w1=parameters['w']
        h1=parameters['h']*(-1)
        self.array2raster(rf1,w1,h1,dem_datas1,self.origine,parameters['INPUT'])##########rasterize inventory
        del dem_datas
        del dem_datas1
        ##################################
        IN1a=rf1
        IN2a='/tmp/invq_sampler.tif'
        IN3a='/tmp/inventorynxn_sampler.tif'
        self.cut(IN1a,IN3a)##########traslate inventory
        #if self.polynum==0:
        #    IN3a=IN1a
        self.ds15=None
        self.ds15 = gdal.Open(IN3a)
        if self.ds15 is None:#####################verify empty row input
            QgsMessageLog.logMessage("ERROR: can't open raster input", tag="WoE")
            raise ValueError  # can't open raster input, see 'WoE' Log Messages Panel
        ap=self.ds15.GetRasterBand(1)
        NoData=ap.GetNoDataValue()
        invmatrix = np.array(ap.ReadAsArray()).astype(np.int64)
        bands = self.ds15.RasterCount
        if bands>1:#####################verify bands
            QgsMessageLog.logMessage("ERROR: input rasters shoud be 1-band raster", tag="WoE")
            raise ValueError  # input rasters shoud be 1-band raster, see 'WoE' Log Messages Panel
        #################################dem
        # except:
        #     QgsMessageLog.logMessage("Failure to save sized inventory", tag="WoE")
        #     raise ValueError  # Failure to save sized inventory, see 'WoE' Log Messages Panel
        ###########################################load inventory
        self.catalog0=np.zeros(np.shape(invmatrix),dtype='int64')
        print(np.shape(invmatrix),'shape catalog')
        self.catalog0[:]=invmatrix[:]
        del invmatrix
        #######################################inventory from shp to tif
        v,t,XY=self.vector2arrayinv(IN3a,parameters['INPUT'],self.catalog0,parameters['train'])
        return v,t,XY

    def array2raster(self,newRasterfn,pixelWidth,pixelHeight,array,oo,lsd):
        ds = ogr.Open(lsd)
        cr=np.shape(array)
        cols=cr[1]
        rows=cr[0]
        originX = oo[0]
        originY = oo[1]
        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(newRasterfn, int(cols), int(rows), 1, gdal.GDT_Float32)
        outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
        outband = outRaster.GetRasterBand(1)
        outband.SetNoDataValue(-9999)
        outband.WriteArray(array)
        #outRasterSRS = osr.SpatialReference()
        #outRasterSRS.ImportFromEPSG(int(self.epsg[self.epsg.rfind(':')+1:]))
        outRaster.SetProjection(ds.GetLayer().GetSpatialRef().ExportToWkt())
        outband.FlushCache()
        print(cols,rows,originX, pixelWidth,originY, pixelHeight, 'array2raster')
        del array

    def cut(self,in1,in3):
        print(self.newYNumPxl,self.newXNumPxl,'cause dimensions')
        #if self.polynum==1:
        try:
            if os.path.isfile(in3):
                os.remove(in3)

            #print(self.newYNumPxl,self.newXNumPxl,self.xmin,self.ymax,self.xmax,self.ymin)

            #os.system('gdal_translate -a_srs '+str(self.epsg)+' -of GTiff -ot Float32 -outsize ' + str(self.newXNumPxl) +' '+ str(self.newYNumPxl) +' -projwin ' +str(self.xmin)+' '+str(self.ymax)+' '+ str(self.xmax) + ' ' + str(self.ymin) + ' -co COMPRESS=DEFLATE -co PREDICTOR=1 -co ZLEVEL=6 '+ in1 +' '+in2)

            #processing.run('gdal:cliprasterbyextent', {'INPUT': in1,'PROJWIN': parameters['v'], 'NODATA': -9999, 'ALPHA_BAND': False, 'KEEP_RESOLUTION': True, 'MULTITHREADING': True, 'OPTIONS': '', 'DATA_TYPE': 6,'OUTPUT': in3})

                    # alg_params = {
    #     'DATA_TYPE': 0,
    #     'EXTRA': '',
    #     'INPUT': parameters['r'],
    #     'NODATA': -9999,
    #     'OPTIONS': '',
    #     'PROJWIN': parameters['v'],
    #     'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
    # }

            processing.run('gdal:cliprasterbymasklayer', {'INPUT': in1,'MASK': self.poly, 'NODATA': -9999, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': True, 'MULTITHREADING': True, 'OPTIONS': '', 'DATA_TYPE': 6,'OUTPUT': in3})

            #print('gdal:cliprasterbymasklayer', {'INPUT': in1,'MASK': self.poly, 'NODATA': -9999, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': False, 'KEEP_RESOLUTION': True, 'MULTITHREADING': True, 'OPTIONS': '', 'DATA_TYPE': 6,'OUTPUT': in2})

            #print('gdal_translate -a_srs '+str(self.epsg)+' -of GTiff -ot Float32 -outsize ' + str(self.newXNumPxl) +' '+ str(self.newYNumPxl) +' -projwin ' +str(self.xmin)+' '+str(self.ymax)+' '+ str(self.xmax) + ' ' + str(self.ymin) + ' -co COMPRESS=DEFLATE -co PREDICTOR=1 -co ZLEVEL=6 '+ in1 +' '+in2)
        except:
            QgsMessageLog.logMessage("Failure to save sized /tmp input", tag="WoE")
            raise ValueError  # Failure to save sized /tmp input Log Messages Panel

    def vector2arrayinv(self,raster,lsd,invzero,parameters):
        rlayer = QgsRasterLayer(raster, "layer")
        if not rlayer.isValid():
            print("Layer failed to load!")
        ext=rlayer.extent()#xmin
        xm = ext.xMinimum()
        xM = ext.xMaximum()
        ym = ext.yMinimum()
        yM = ext.yMaximum()
        pxlw=rlayer.rasterUnitsPerPixelX()
        pxlh=rlayer.rasterUnitsPerPixelY()
        newXNumPxl=(np.ceil(abs(xM-xm)/(rlayer.rasterUnitsPerPixelX()))-1).astype(int)
        newYNumPxl=(np.ceil(abs(yM-ym)/(rlayer.rasterUnitsPerPixelY()))-1).astype(int)
        sizex=newXNumPxl
        sizey=newYNumPxl
        origine=[xm,yM]
        driverd = ogr.GetDriverByName('ESRI Shapefile')
        ds9 = driverd.Open(lsd)
        layer = ds9.GetLayer()
        self.ref = layer.GetSpatialRef()
        count=0
        for feature in layer:
            count+=1
            geom = feature.GetGeometryRef()
            xy=np.array([geom.GetX(),geom.GetY()])
            try:
                XY=np.vstack((XY,xy))
            except:
                XY=xy
        size=np.array([pxlw,pxlh])
        OS=np.array([xm,yM])
        NumPxl=(np.ceil(abs((XY-OS)/size)-1)).astype(int)#from 0 first cell
        print(NumPxl)
        print(sizey,sizex,'dimensioni inventario')
        valuess=np.zeros(np.shape(invzero),dtype='float32')
        #try:
        #print(np.max(NumPxl[0,1]))
        #print(np.max(NumPxl[0,0]))
        #print(np.min(NumPxl[0,1]))
        #print(NumPxl[0,0])
        #print(count)
        for i in range(count):
            #print(i,'i')
            if XY[i,1]<=yM and XY[i,1]>=ym and XY[i,0]<=xM and XY[i,0]>=xm:
                valuess[NumPxl[i,1].astype(int),NumPxl[i,0].astype(int)]=1
        # except:#only 1 feature
        #     if XY[1]<=yM and XY[1]>=ym and XY[0]<=xM and XY[0]>=xm:
        #         valuess[NumPxl[1].astype(int),NumPxl[0].astype(int)]=1
        #fuori = valuess.astype(np.float32)
        rows,cols=np.where(valuess==1)

        l=len(rows)
        vec=np.arange(l)
        tt=np.ceil((parameters/100.)*l).astype(int)
        tr=np.asarray(random.sample(range(0, l), tt))
        vec[tr]=-1
        va=vec[vec>-1]

        trow=rows[tr]
        tcol=cols[tr]
        traincells=np.array([trow,tcol]).T

        vrow=rows[va]
        vcol=cols[va]
        validcells=np.array([vrow,vcol]).T
        #print(traincells, 'celles')
        #print(np.where(NumPxl[:,1]==traincells[1,0]),'where')
        v=[]
        t=[]
        for i in range(len(traincells)):
            #print(i)
            ttt=np.where((NumPxl[:,1]==traincells[i,0]) & (NumPxl[:,0]==traincells[i,1]))
            #print(ttt)
            #print(np.where(NumPxl[:,0]==traincells[i,0]))
            t=t+list(ttt[0])

        for i in range(len(validcells)):
            vv=np.where((NumPxl[:,1]==validcells[i,0]) & (NumPxl[:,0]==validcells[i,1]))
            v=v+list(vv[0])
            #print(ciao)
        #print(t)
        return v,t,XY

    def save(self,parameters):
        # XY=parameters['INPUT3']
        # driver = ogr.GetDriverByName("ESRI Shapefile")
        # #if os.path.exists(parameters['INPUT1']):
        # #    driver.DeleteDataSource(parameters['INPUT1'])
        # # define fields for feature attributes. A QgsFields object is needed
        # fields = QgsFields()
        # fields.append(QgsField("id", QVariant.Int))
        #
        # crs = QgsProject.instance().crs()
        # transform_context = QgsProject.instance().transformContext()
        # save_options = QgsVectorFileWriter.SaveVectorOptions()
        # save_options.driverName = "ESRI Shapefile"
        # save_options.fileEncoding = "UTF-8"
        #
        # writer = QgsVectorFileWriter.create(parameters['INPUT1'], fields, QgsWkbTypes.Point, crs, transform_context, save_options)
        #
        # if writer.hasError() != QgsVectorFileWriter.NoError:
        #     print("Error when creating shapefile: ",  writer.errorMessage())
        #
        # for i in range(len(parameters['INPUT2'])):
        # # add a feature
        #     fet = QgsFeature()
        #
        #     fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(XY[parameters['INPUT2'][i],0]) , float(XY[parameters['INPUT2'][i],1]))))
        #     fet.setAttributes([i])
        #     writer.addFeature(fet)
        #
        #     # delete the writer to flush features to disk
        # del writer



        # vl = QgsVectorLayer(parameters['INPUT1'], "temporary_points", "memory")
        # pr = vl.dataProvider()
        # # add fields
        # pr.addAttributes([QgsField("name", QVariant.String),QgsField("age",  QVariant.Int),QgsField("size", QVariant.Double)])
        # vl.updateFields()
        # # tell the vector layer to fetch changes from the provider
        # # add a feature
        # fet = QgsFeature()
        # fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10,10)))
        # fet.setAttributes(["Johny", 2, 0.3])
        # pr.addFeatures([fet])
        # # update layer's extent when new features have been added# because change of extent in provider is not propagated to the layer
        # vl.updateExtents()





        # #from qgis.PyQt.QtCore import QVariant
        #
        # # define fields for feature attributes. A QgsFields object is needed
        # fields = QgsFields()
        # fields.append(QgsField("first", QVariant.Int))
        # fields.append(QgsField("second", QVariant.String))
        #
        # """ create an instance of vector file writer, which will create the vector file.
        # Arguments:
        # 1. path to new file (will fail if exists already)
        # 2. field map
        # 3. geometry type - from WKBTYPE enum
        # 4. layer's spatial reference (instance of
        #    QgsCoordinateReferenceSystem)
        # 5. coordinate transform context
        # 6. save options (driver name for the output file, encoding etc.)
        # """
        #
        # crs = QgsProject.instance().crs()
        # transform_context = QgsProject.instance().transformContext()
        # save_options = QgsVectorFileWriter.SaveVectorOptions()
        # save_options.driverName = "ESRI Shapefile"
        # save_options.fileEncoding = "UTF-8"
        #
        # writer = QgsVectorFileWriter.create(
        #   "/tmp/a.shp",
        #   fields,
        #   QgsWkbTypes.Point,
        #   crs,
        #   transform_context,
        #   save_options
        # )
        #
        # if writer.hasError() != QgsVectorFileWriter.NoError:
        #     print("Error when creating shapefile: ",  writer.errorMessage())
        #
        # # add a feature
        # fet = QgsFeature()
        #
        # fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10,10)))
        # fet.setAttributes([1, "text"])
        # writer.addFeature(fet)
        #
        # # delete the writer to flush features to disk
        # del writer


        XY=parameters['INPUT3']
        #print(parameters['INPUT2'],'2')
        #print(XY,'3')
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # Remove output shapefile if it already exists
        #print(parameters['INPUT1'],'1')
        if os.path.exists(parameters['INPUT1']):
            driver.DeleteDataSource(parameters['INPUT1'])
        # create the data source
        ds=driver.CreateDataSource(parameters['INPUT1'])
        # create the layer
        layer = ds.CreateLayer("vector", self.ref, ogr.wkbPoint)
        # Add the fields we're interested in
        field_name = ogr.FieldDefn("id", ogr.OFTInteger)
        field_name.SetWidth(100)
        layer.CreateField(field_name)
        # Process the text file and add the attributes and features to the shapefile
        #print(parameters['INPUT2'])
        for i in range(len(parameters['INPUT2'])):
            #print(i)
            # create the feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # Set the attributes using the values from the delimited text file
            feature.SetField("id", i)
            # create the WKT for the feature using Python string formatting
            wkt = "POINT(%f %f)" % (float(XY[parameters['INPUT2'][i],0]) , float(XY[parameters['INPUT2'][i],1]))
            # Create the point from the Well Known Txt
            point = ogr.CreateGeometryFromWkt(wkt)
            # Set the feature geometry using the point
            feature.SetGeometry(point)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Dereference the feature
            feature = None
        # Save and close the data source
        ds = None
        vlayer = QgsVectorLayer(parameters['INPUT1'], 'vector', "ogr")
        # add the layer to the registry
        QgsProject.instance().addMapLayer(vlayer)

    # def saveT(self,parameters):
    #     # set up the shapefile driver
    #     driver = ogr.GetDriverByName("ESRI Shapefile")
    #     # Remove output shapefile if it already exists
    #     if os.path.exists(OutTrain):
    #         driver.DeleteDataSource(OutTrain)
    #     # create the data source
    #     ds=driver.CreateDataSource(OutTrain)
    #     # create the layer
    #     layer = ds.CreateLayer("Training", self.ref, ogr.wkbPoint)
    #     # Add the fields we're interested in
    #     field_name = ogr.FieldDefn("id", ogr.OFTInteger)
    #     field_name.SetWidth(100)
    #     layer.CreateField(field_name)
    #     # Process the text file and add the attributes and features to the shapefile
    #     for i in range(len(t)):
    #         # create the feature
    #         feature = ogr.Feature(layer.GetLayerDefn())
    #         # Set the attributes using the values from the delimited text file
    #         feature.SetField("id", i)
    #         # create the WKT for the feature using Python string formatting
    #         wkt = "POINT(%f %f)" % (float(XY[t[i],0]) , float(XY[t[i],1]))
    #         # Create the point from the Well Known Txt
    #         point = ogr.CreateGeometryFromWkt(wkt)
    #         # Set the feature geometry using the point
    #         feature.SetGeometry(point)
    #         # Create the feature in the layer (shapefile)
    #         layer.CreateFeature(feature)
    #         # Dereference the feature
    #         feature = None
    #     # Save and close the data source
    #     ds = None
