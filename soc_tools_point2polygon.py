# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SAOLA
                                 A QGIS plugin
Spatial accessibility and optimal location analysis tool (SAOLA)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-15
        copyright            : (C) 2019 by Ansup
        email                : ansup0402@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Ansup'
__date__ = '2019-08-15'
__copyright__ = '(C) 2019 by Ansup'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorDestination
                       )


class LivingSOCToolsPoint2Polygon(QgsProcessingAlgorithm):


    IN_ORGPOINT = 'IN_ORGPOINT'
    IN_GRID_SIZE = 'IN_GRID_SIZE'
    OUTPUT = 'OUTPUT'
    __debugging = False
    __cur_dir = None

    @property
    def debugmode(self):
        global __debugging
        return __debugging
        # return self.__debugging

    @debugmode.setter
    def debugmode(self, value):
        global __debugging
        __debugging = value
        # self.__debugging = value

    @property
    def temporaryDirectory(self):
        global __cur_dir
        return __cur_dir

    @temporaryDirectory.setter
    def temporaryDirectory(self, value):
        global __cur_dir
        __cur_dir = value

    def initAlgorithm(self, config):

        # 원본 포인트
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_ORGPOINT,
                '❖ ' + self.tr('Input point vector layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False)
        )

        # 분석 최소단위(잠재적 위치 격자 사이즈)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_GRID_SIZE,
                "❖ " + self.tr('Polygon Size(Unit : m)'),
                QgsProcessingParameterNumber.Integer,
                100, False, 10, 100000)        #디폴트, 옵션, 미니멈, 맥시멈
        )

        # 최종 결과
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Specify the output vector layer')
            )
        )

    def onlyselectedfeature(self, parameters, context, paramID):
        layersource = self.parameterAsSource(parameters, paramID, context)
        layervertor = self.parameterAsVectorLayer(parameters, paramID, context)
        onlyselectedFeature = (layersource.featureCount() >= 0 and layervertor is None)
        return onlyselectedFeature

    def getLayerfromParameter(self, parameters, context, paramID):
        layer = self.parameterAsSource(parameters, paramID, context)
        if layer is None:
            return None, 0
        else:
            return layer, self.onlyselectedfeature(parameters, context, paramID)

    def parameter2Dict(self, parameters, context):
        keyword = {}
        keyword['IN_ORGPOINT'], keyword['IN_ORGPOINT_ONLYSELECTED'] = self.getLayerfromParameter(parameters, context, self.IN_ORGPOINT)
        keyword['IN_GRID_SIZE'] = self.parameterAsInt(parameters, self.IN_GRID_SIZE, context)
        keyword['OUTPUT'] = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        return keyword

    def processAlgorithm(self, parameters, context, feedback):
        params = self.parameter2Dict(parameters, context)

        # if self.check_userinput(parameters=params) == False: return None

        try:
            from .soc_locator_launcher import soc_locator_launcher
        except ImportError:
            from soc_locator_launcher import soc_locator_launcher

        if self.debugmode:
            feedback.pushInfo("****** [START DEBUG] ******")
            feedback.pushInfo(self.temporaryDirectory)

        launcher = soc_locator_launcher(feedback=feedback, context=context, parameters=params, debugging=self.debugmode,
                                        workpath=self.temporaryDirectory)

        out_vector = launcher.execute_tools_point2polygone()

        return {self.OUTPUT: out_vector}



    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Convert to Polygon'
        # return 'Equity Based Location Analysis(Euclidean)'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        # return 'Life-Friendly SOC Locator'
        return 'Koala Support Tool'


    def tr(self, string):
        return QCoreApplication.translate('koala', string)

    def createInstance(self):
        return LivingSOCToolsPoint2Polygon()