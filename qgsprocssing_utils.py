
import os
import pathlib

cur_dir = pathlib.Path(__file__).parent


from qgis.core import (
                    QgsVectorLayer,
                    QgsVectorFileWriter,
                    QgsProcessingFeatureSourceDefinition
                    )


from processing.core.Processing import Processing
Processing.initialize()
import processing


class qgsprocessUtils:
    def __init__(self, feedback, context, debugmode=False):
        self.debugging = debugmode
        self.feedback = feedback
        self.context = context

    def run_algprocessing(self, algname, params):
        if self.feedback.isCanceled(): return None
        result = processing.run(algname,
                                params,
                                context=self.context,
                                feedback=self.feedback)
        return result


    def bufferwithQgis(self, input, onlyselected, distance, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:multiringconstantbuffer'

        # self.feedback.pushInfo(str(type(input)))
        inputsource = input
        if onlyselected:
            inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      DISTANCE=distance,
                      OUTPUT=output,
                      RINGS=1)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def createGridfromLayer(self, sourcelayer, gridsize, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = "qgis:creategrid"

        layer = sourcelayer
        # layer = QgsVectorLayer(path=sourcelayer)

        extent = layer.extent()
        xmin, ymin, xmax, ymax = extent.toRectF().getCoords()
        extent = str(xmin) + ',' + str(xmax) + ',' + str(ymin) + ',' + str(ymax)

        params = dict(TYPE=0,
                      EXTENT=extent,
                      HSPACING=gridsize,
                      VSPACING=gridsize,
                      HOVERLAY=0,
                      VOVERLAY=0,
                      CRS=layer.crs(),
                      OUTPUT=output
                      )

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def clipwithQgis(self, input, onlyselected, overlay, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = "native:clip"

        inputsource = input
        if onlyselected:
            inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      OVERLAY=overlay,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def dissolvewithQgis(self, input, onlyselected, field=None, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:dissolve'

        inputsource = input
        if onlyselected:
            inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      Field=field,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def addField(self, input, fid, ftype, flen, fprecision, output='TEMPORARY_OUTPUT'):

        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'qgis:addfieldtoattributestable'

        inputsource = input
        # if onlyselected:
        #     inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      FIELD_NAME=fid,
                      FIELD_TYPE=ftype,
                      FIELD_LENGTH=flen,
                      FIELD_PRECISION=fprecision,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def fieldCalculate(self, input, fid, ftype, flen, fprecision, formula, newfield=False,
                       output='TEMPORARY_OUTPUT'):

        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        # algname = 'qgis:advancedpythonfieldcalculator'
        algname = 'qgis:fieldcalculator'

        inputsource = input
        # if onlyselected:
        #     inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      FIELD_NAME=fid,
                      FIELD_TYPE=ftype,
                      FIELD_LENGTH=flen,
                      FIELD_PRECISION=fprecision,
                      NEW_FIELD=newfield,
                      FORMULA=formula,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']


    def renameField(self, layer, fromName, toName, baseName='renamedlayer'):
        vector = QgsVectorLayer(path=layer, baseName=baseName)
        vector.startEditing()
        # idx = result.fieldNameIndex('HubName')
        idx = vector.fields().indexFromName(fromName)
        vector.renameAttribute(idx, toName)
        vector.commitChanges()

        return vector.source()

    def intersection(self, input, inputonlyseleceted, inputfields,
                     overlay, overayprefix, overonlyselected=False, overlayer_fields=None,
                     output='TEMPORARY_OUTPUT'):

        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:intersection'

        inputsource = input
        if inputonlyseleceted: inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        overlaysource = overlay
        if overonlyselected: overlaysource = QgsProcessingFeatureSourceDefinition(overlay, True)

        params = dict(INPUT=inputsource,
                      INPUT_FIELDS=inputfields,
                      OVERLAY=overlaysource,
                      OVERLAY_FIELDS_PREFIX=overayprefix,
                      OVERLAY_FIELDS=overlayer_fields,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']




    def countpointsinpolygon(self, polygons, points, field, polyonlyselected=False, pointonlyseleced=False, weight=None, classfield=None, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'qgis:countpointsinpolygon'

        polyinputsource = polygons
        if polyonlyselected: polyinputsource = QgsProcessingFeatureSourceDefinition(polygons, True)

        pointinputsource = points
        if pointonlyseleced: pointinputsource = QgsProcessingFeatureSourceDefinition(points, True)

        params = dict(POLYGONS=polyinputsource,
                      POINTS=pointinputsource,
                      FIELD=field,
                      WEIGHT=weight,
                      CLASSFIELD=classfield,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def centroidlayer(self, input, onlyselected, allparts=False, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:centroids'

        inputsource = input
        if onlyselected: inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      ALL_PARTS=allparts,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']


        # {'ALL_PARTS': False,
        #  'INPUT': '/Users/ansup0402/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/soc_locator/data/pop_102082.shp',
        #  'OUTPUT': 'TEMPORARY_OUTPUT'}



    def nearesthubpoints(self, input, onlyselected, sf_hub, hubfield, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = "qgis:distancetonearesthubpoints"

        inputsource = input
        if onlyselected:
            # self.feedback.pushInfo('onlyselected')
            inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      HUBS=sf_hub,
                      FIELD=hubfield,
                      UNIT=0,
                      OUTPUT=output)

        result = self.run_algprocessing(algname=algname, params=params)['OUTPUT']

        if output.find('TEMPORARY_OUTPUT') < 0:
            basename = 'output'
            result = self.renameField(layer=result, fromName='HubName', toName=hubfield, baseName=basename)
        else:
            result.startEditing()
            idx = result.fields().indexFromName('HubName')
            result.renameAttribute(idx, hubfield)
            result.commitChanges()
        return result

            # 이함수는 좀 더 테스트 필요
    def statisticsfromfield(self, input, numericfield, output_html='TEMPORARY_OUTPUT'):
        if output_html is None or output_html == '': output_html = 'TEMPORARY_OUTPUT'
        algname = 'qgis:basicstatisticsforfields'

        inputsource = input
        params = dict(INPUT_LAYER=inputsource,
                      FIELD_NAME=numericfield,
                      OUTPUT_HTML_FILE=output_html)

        return self.run_algprocessing(algname=algname, params=params)

    def distancematrix(self, input, inputonlyselected, inputfield, target, targetonlyseleted, targetfield,
                       matrixtype=2, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'qgis:distancematrix'

        inputsource = input
        tarsource = target
        if inputonlyselected: inputsource = QgsProcessingFeatureSourceDefinition(input, True)
        if targetonlyseleted: tarsource = QgsProcessingFeatureSourceDefinition(target, True)

        params = dict(INPUT=inputsource,
                      INPUT_FIELD=inputfield,
                      TARGET=tarsource,
                      TARGET_FIELD=targetfield,
                      MATRIX_TYPE=matrixtype,
                      NEAREST_POINTS=0,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def multiparttosingleparts(self, input, onlyselected, output='TEMPORARY_OUTPUT'):

        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:multiparttosingleparts'

        inputsource = input
        if onlyselected: inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      OUTPUT=output)
        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def joinattributetable(self, input1, input1onlyselected, input2, input2onlyselected, field1, field2,
                           prefix='M_', output='TEMPORARY_OUTPUT'):

        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'native:joinattributestable'

        inputsource1 = input1
        inputsource2 = input2
        if input1onlyselected: inputsource1 = QgsProcessingFeatureSourceDefinition(input1, True)
        if input2onlyselected: inputsource2 = QgsProcessingFeatureSourceDefinition(input2, True)

        params = dict(INPUT=inputsource1,
                      FIELD=field1,
                      INPUT_2=inputsource2,
                      FIELD_2=field2,
                      FIELDS_TO_COPY=[],
                      METHOD=1,
                      PREFIX=prefix,
                      DISCARD_NONMATCHING=False,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def selectbyexpression(self, input, expression):
        algname = "qgis:selectbyexpression"
        params = dict(INPUT=input,
                      EXPRESSION=expression,
                      METHOD=0)
        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def saveselectedfeatrues(self, input, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = "native:saveselectedfeatures"
        params = dict(INPUT=input,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def duplicate_layer(self, sourcelayer, copylayer):
        algname = "qgis:selectbyexpression"
        params = dict(INPUT=sourcelayer,
                      EXPRESSION='1=1',
                      METHOD=0)
        layer = self.run_algprocessing(algname=algname, params=params)['OUTPUT']

        algname = "native:saveselectedfeatures"
        params = dict(INPUT=layer,
                      OUTPUT=copylayer)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def statisticsbycategories(self, input, onlyselected, categoriesfields, valuefield, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = 'qgis:statisticsbycategories'

        inputsource = input
        if onlyselected: inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        params = dict(INPUT=inputsource,
                      CATEGORIES_FIELD_NAME=categoriesfields,
                      METHOD=0,
                      VALUES_FIELD_NAME=valuefield,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']

    def vectorlayer2ShapeFile(self, vectorlayer, output, destCRS, fileEncoding='utf-8'):
        return QgsVectorFileWriter.writeAsVectorFormat(layer=vectorlayer,
                                                fileName=output,
                                                fileEncoding=fileEncoding,
                                                destCRS=destCRS,
                                                driverName='ESRI Shapefile')

    def differencelayer(self, input, onlyselected, overlay, overonlyselected, output='TEMPORARY_OUTPUT'):
        if output is None or output == '': output = 'TEMPORARY_OUTPUT'
        algname = "native:difference"

        inputsource = input
        if onlyselected: inputsource = QgsProcessingFeatureSourceDefinition(input, True)

        oversource = overlay
        if overonlyselected: oversource = QgsProcessingFeatureSourceDefinition(overlay, True)

        params = dict(INPUT=inputsource,
                      OVERLAY=oversource,
                      OUTPUT=output)

        return self.run_algprocessing(algname=algname, params=params)['OUTPUT']



    def writeAsVectorLayer(self, layername):
        base = os.path.basename(layername)
        baseName = os.path.splitext(base)[0]

        # self.feedback.pushInfo(base)
        # self.feedback.pushInfo(baseName)

        layer = QgsVectorLayer(path=layername, baseName=baseName, providerLib='ogr')
        if layer.isValid():
            return layer
        else:
            self.feedback.pushInfo("%s is not valid" % layername)
            return None
