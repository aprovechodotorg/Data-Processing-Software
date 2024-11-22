'''
Created on Nov 11, 2010

@author: surya
'''

import re
import os
import sys
import json
import logging
import StringIO
import traceback
from datetime import datetime

from gridfs import *
from mongoengine import *
from Logging.Logger import getLog
from bson.objectid import ObjectId
from ImageUtils import ImageResize
from IANASettings.Settings import ExitCode
from IANASettings.Settings import ResizeImageConstants
from mongoengine.connection import _get_db
from DANA.DANAFramework import DANAFramework
from FeatureExtractor import featureExtractor
from Collections.SuryaProcessResult import *
from Collections.SuryaProcessingList import *
from Collections.SuryaDeploymentData import *
from Collections.SuryaCalibrationData import *
from BCCResultComputation import bccResultComputation
from DANAExceptions.ResultSavingError import ResultSavingError
from DANAExceptions.PreProcessingError import PreProcessingError
from DANAExceptions.PprocCalibrationError import PprocCalibrationError
from DANAExceptions.CompuCalibrationError import CompuCalibrationError
from DANAExceptions.ResultComputationError import ResultComputationError


class PreProcessingResult:
    """ Results after the Image has been preprocessed.
    """

    def __init__(self, features, result):
        """ Constructor

            Keyword Arguments:
            features -- The features extracted from the Image
            result   -- The SuryaImagePreProcessingResult
                        Embedded Document
        """
        self.features = features
        self.result = result


class DanaResult:
    """ Results after the computation of Black Carbon Concentration (BCVol)
    """

    def __init__(self, bccResult, exitcode, result):
        """ Constructor

            Keyword Arguments:
            bccResult -- The Collections.SuryaProcessResult.BccResult object
            exitcode  -- The result on computation of a the BCVol
            result    -- A partially constructed SuryaImageAnalysisResult object
        """
        self.bccResult = bccResult
        self.exitcode = exitcode
        self.result = result  # Partially constructed SuryaImageAnalysisResult object with the ChartImage Field set


class IANAFramework(DANAFramework):
    """                 The Image ANAlysis Framework Implementation
                        -------------------------------------------
        This class implementss functionality to analyze Uploaded Images to compute the
        black carbon concentration(BCVol) in those images.
    """

    log = getLog("IANAFramework")

    def __init__(self, level=logging.DEBUG):
        """ Constructor

            Keyword Arguments:
            level -- The logging level
        """

        self.log.setLevel(level)
        self.ianatags = self.danatags + " IANA "
        self.fs = GridFS(_get_db())

    def getDataItems(self):
        """ Refer DANAFramework.getDataItems() for documentation
        """

        return SuryaIANAProcessingList.objects(processedFlag=False)

    def getItemName(self, dataItem):
        """ Refer DanaFramework.getItemName() for documentation
        """
        return dataItem.processEntity.filename

    def isValid(self, dataItem):
        """ Refer DANAFramework.isValid() for documentation
        """
        return dataItem.processEntity.validFlag

    def getPreProcessingConfiguration(self, itemname, dataItem):
        """ Refer DANAFramework.getPreProcessingConfiguration for documentation
        """
        try:
            # Set the logging tags
            tags = self.ianatags + itemname + " PPROCCALIB"

            self.log.info("Done Running PPROCCALIB", extra=tags)

            # here we actually fetch and store the updated preProcessing config
        except Exception as err:
            self.log.error("Error in gePreProcConf:", extra=tags, exc_info=True)
            raise PprocCalibrationError(err)

    def preProcessDataItem(self, itemname, dataItem):
        """ Refer DANAFramework.preProcessDataItem() for documentation
        """
        try:
            # Set the logging tags
            tags = self.ianatags + itemname + " PPROC"

            self.log.info("Running PPROC", extra=tags)

            # Create a new pre-processin result object
            result = SuryaImagePreProcessingResult()

            # Fetch the image
            imagefile = dataItem.processEntity.file

            # Fetch the debugImage
            debugImagename = (itemname + ".debug." + str(dataItem.preProcessingConfiguration.calibrationId) + ".png")

            # Check if the image already exists, delete it
            if self.fs.exists(filename=debugImagename):
                debugImage = self.fs.get_last_version(debugImagename)
                self.fs.delete(debugImage.__getattr__("_id"))

            result.debugImage.new_file(filename=debugImagename, content_type='image/png')

            # Get the Features from the image
            features, exitcode = featureExtractor(imagefile, 1, result.debugImage, dataItem.preProcessingConfiguration,
                                                  dataItem.computationConfiguration, tags, logging.DEBUG)

            # If failed, maybe we need to shrink/grow image down
            for resizeSize in ResizeImageConstants.LargestSide:
                if exitcode is not ExitCode.Success:
                    self.log.info("Resizing image to %d first" % (resizeSize), extra=tags)
                    imgtoshrink = dataItem.processEntity.origFile.get()
                    imgtoshrink.seek(0)
                    shrunkimage = ImageResize.imageResize(imgtoshrink, resizeSize)
                    replimg = StringIO.StringIO()
                    shrunkimage.save(replimg, format="JPEG")
                    replimg.seek(0)
                    self.log.info("Resizing image to: %d" % (replimg.len), extra=tags)
                    dataItem.processEntity.file.replace(replimg, content_type='image/jpeg')
                    imagefile = dataItem.processEntity.file
                    # redo the debug image
                    if self.fs.exists(filename=debugImagename):
                        debugImage = self.fs.get_last_version(debugImagename)
                        self.fs.delete(debugImage.__getattr__("_id"))

                        result.debugImage.new_file(filename=debugImagename, content_type='image/png')

                    # run QR detection again
                    self.log.info("Rerunning featureExtractor with resized image", extra=tags)
                    features, exitcode = featureExtractor(imagefile, 1, result.debugImage,
                                                          dataItem.preProcessingConfiguration,
                                                          dataItem.computationConfiguration, tags, logging.DEBUG)

                # try tipping 45 degress
                if exitcode is not ExitCode.Success:
                    self.log.info("Rotating image to %d deg" % (ResizeImageConstants.RotateDegrees), extra=tags)
                    rotimage = ImageResize.imageRotate(shrunkimage, resizeSize)
                    replimg = StringIO.StringIO()
                    rotimage.save(replimg, format="JPEG")
                    replimg.seek(0)
                    dataItem.processEntity.file.replace(replimg, content_type='image/jpeg')
                    imagefile = dataItem.processEntity.file
                    # redo the debug image
                    if self.fs.exists(filename=debugImagename):
                        debugImage = self.fs.get_last_version(debugImagename)
                        self.fs.delete(debugImage.__getattr__("_id"))

                        result.debugImage.new_file(filename=debugImagename, content_type='image/png')

                    # run QR detection again
                    self.log.info("Rerunning featureExtractor with resized image", extra=tags)
                    features, exitcode = featureExtractor(imagefile, 1, result.debugImage,
                                                          dataItem.preProcessingConfiguration,
                                                          dataItem.computationConfiguration, tags, logging.DEBUG)

            # Set the result status
            result.status = ExitCode.toString[exitcode]

            if exitcode is not ExitCode.Success:
                result.validFlag = False
                raise PreProcessingError(ExitCode.toString[exitcode], result, None)

            result.validFlag = True
            result.sampled = features[0]
            result.gradient = features[2]

            self.log.info("Done Running PPROC", extra=tags)
            return PreProcessingResult(features, result)
        except Exception as err:
            if isinstance(err, PreProcessingError):
                raise err
            result = SuryaImagePreProcessingResult()
            result.item = dataItem.processEntity
            result.preProcessingConfiguration = dataItem.preProcessingConfiguration
            result.validFlag = False
            result.status = traceback.format_exc()
            raise PreProcessingError(result.status, result, err)

    def getComputationConfiguration(self, itemname, dataItem, preProcessingResult):
        """ Refer DANAFramework.getComputationConfiguration for documentation
        """

        try:
            # Set the logging tags
            tags = self.ianatags + itemname + " COMPUCALIB"

            self.log.info("Running COMPUCALIB", extra=tags)
            if dataItem.overrideFlag:
                # TODO:
                # a) from pre-processing result get aux_id : the aux_id, dataItem.deploymentId as the key
                #    fetch an air_flow_rate from the pumps table.
                # b) from the misc field fetch any calibration data.
                # combining a) and b) over the defaut calibration data, get and add a new calibration entry
                # to the calibration data table.
                # and use this new calibration entry for computing BCVol
                #
                try:
                    misc = dataItem.processEntity.misc
                    misc_dict = json.loads(misc)
                except ValueError as ve:
                    self.log.error(
                        '[ Sanity ] The misc input is not a json syntax string. Store it as { "rawstring": (...input...)} . The orignial Input:' + str(
                            misc) + "Reason:" + str(ve), extra=tags)

                # Get the exposedtime, flowrate, filterradius params and VALIDATE!
                isnew = False
                try:
                    if misc_dict.has_key("duration"):
                        exposedtime = float(misc_dict['duration'])
                        isnew = True
                    elif misc_dict.has_key("exposedtime"):
                        exposedtime = float(misc_dict['exposedtime'])
                        isnew = True
                    elif misc_dict.has_key("d"):
                        exposedtime = float(misc_dict['d'])
                        isnew = True
                    else:
                        exposedtime = dataItem.computationConfiguration.exposedTime
                except ValueError as e:
                    exposedtime = dataItem.computationConfiguration.exposedTime

                # time units for the duration
                if misc_dict.has_key("timeunits"):
                    timeunits = misc_dict['timeunits']
                    isnew = True
                else:
                    timeunits = dataItem.computationConfiguration.timeUnits

                # see if there is an real recordDate time
                try:
                    newdatestr = ""
                    newtimestr = "00:00"
                    newdatetime = None
                    if misc_dict.has_key("date"):
                        newdatestr = misc_dict['date']
                    if misc_dict.has_key("start"):
                        newtimestr = misc_dict['start']
                    if newdatestr != "":
                        newdatetime = datetime.strptime(newdatestr + " " + newtimestr, "%Y-%m-%d %H:%M")
                        dataItem.processEntity.recordDatetime = newdatetime
                        dataItem.processEntity.save()
                except Exception as e:
                    self.log.error("Unabel to parse time: " + newdatestr + " " + newtimestr)

                # filter radius override
                if misc_dict.has_key("filterradius"):
                    filterradius = float(misc_dict['filterradius'])
                    isnew = True
                else:
                    filterradius = dataItem.computationConfiguration.filterRadius

                # use the mas number to override the filter
                flowrate_mas = 0
                flowrate = 0.0
                try:
                    mas_num = ""
                    if misc_dict.has_key("mas"):
                        mas_g = re.search('\d+', misc_dict['mas'])
                        if mas_g != None:
                            mas_num = mas_g.group()
                    if misc_dict.has_key("m"):
                        mas_g = re.search('\d+', misc_dict['m'])
                        if mas_g != None:
                            mas_num = mas_g.group()
                    if mas_num != "":
                        mas = SuryaPump.objects(pumpId=mas_num)
                        if len(mas) > 0:
                            flowrate_mas = mas[0].airFlowRate
                            self.log.error("Set flow rate from pump " + str(mas_num) + " mas as: " + str(flowrate_mas))
                except Exception as e:
                    self.log.error("Unable to extrac mas information", exc_info=True)

                if misc_dict.has_key("flow"):
                    flowrate = float(misc_dict['flow'])
                    isnew = True
                elif misc_dict.has_key("flowrate"):
                    flowrate = float(misc_dict['flowrate'])
                    isnew = True
                elif misc_dict.has_key("f"):
                    flowrate = float(misc_dict['f'])
                    isnew = True
                else:
                    if flowrate_mas != 0:
                        self.log.error("Using flowrate: " + str(flowrate_mas))
                        flowrate = flowrate_mas
                    else:
                        flowrate = dataItem.computationConfiguration.airFlowRate
                        self.log.error("Using default flowrate: " + str(flowrate))

                # bc detector
                bcdetector = dataItem.computationConfiguration.bcDetectorType
                self.log.debug("bcdetector is: " + str(bcdetector))

                if isnew:
                    bcarea = 3.14 * filterradius * filterradius  # NOTE: unused to remove
                    calibId = 0
                    calibId = SuryaCalibrationData.objects.order_by(
                        '-calibrationId').first().calibrationId  # Todo change this
                    if calibId > 0:
                        if calibId < 10000:
                            calibId = 10000
                        calibId = calibId + 1
                        try:
                            # check if calibration data exists
                            dataItem.computationConfiguration, added = SuryaImageAnalysisCalibrationData.objects.get_or_create(
                                exposedTime=exposedtime,
                                timeUnits=timeunits,
                                filterRadius=filterradius,
                                airFlowRate=flowrate,
                                bcDetectorType=bcdetector,
                                defaults={'calibrationId': calibId,
                                          'exposedTime': exposedtime,
                                          'timeUnits': timeunits,
                                          'filterRadius': filterradius,
                                          'airFlowRate': flowrate,
                                          'bcArea': bcarea,
                                          'bcDetectorType': bcdetector})

                        except OperationError as oe:
                            self.log.error("Failed to save the retrieved calibration data", extra=tags)
                            raise CompuCalibrationError(oe, preProcessingResult)

                    if misc_dict.has_key("bcstrips"):
                        bcstrip = misc_dict['bcstrips'].split(",")
                        try:
                            if len(bcstrip) == 10:
                                fbcstrip = []
                                for bcstripval in bcstrip:
                                    fbcstrip.append(float(bcstripval))
                                try:
                                    if not isnew:
                                        calibId = 0
                                        calibId = SuryaCalibrationData.objects.order_by(
                                            '-calibrationId').first().calibrationId  # Todo change this

                                    calibId = calibId + 1
                                    if calibId > 0:
                                        dataItem.bcStrips, added = SuryaImageAnalysisBCStripData.objects.get_or_create(
                                            bcStrips=fbcstrip, defaults={'calibrationId': calibId,
                                                                         'bcStrips': fbcstrip})
                                except OperationError as oe:
                                    self.log.error("Failed to save the retrieved bcstrip data", extra=tags)
                                    raise CompuCalibrationError(oe, preProcessingResult)

                        except ValueError as ve:
                            self.log.error("invalid bcstrip string encountered: " + misc_dict['bcstrip'], extra=tags)
                            # done overriding

            self.log.info("Done Running COMPUCALIB", extra=tags)
            return dataItem.computationConfiguration, dataItem.bcStrips
        except Exception as err:
            if isinstance(err, CompuCalibrationError):
                raise err
            raise CompuCalibrationError(err, preProcessingResult)

    def computeDANAResult(self, itemname, dataItem, preProcessingResult):
        """ Refer DANAFramework.computeDANAResult for documentation
        """

        try:
            # Set the logging tags
            tags = self.ianatags + itemname + " COMPU"

            self.log.info("Running COMPU", extra=tags)

            result = SuryaImageAnalysisResult()
            chartFileName = (itemname + ".chart." + str(dataItem.computationConfiguration.calibrationId) + ".png")

            # Check if the image already exists if not create a new file
            if self.fs.exists(filename=chartFileName):
                chartImg = self.fs.get_last_version(chartFileName)
                self.fs.delete(chartImg.__getattr__("_id"))

            result.chartImage.new_file(filename=chartFileName, content_type='image/png')

            chartImage = result.chartImage
            sampledRGB, aux, gradient = preProcessingResult.features

            filterRadius = dataItem.computationConfiguration.filterRadius
            exposedTime = dataItem.computationConfiguration.exposedTime
            airFlowRate = dataItem.computationConfiguration.airFlowRate
            timeUnits = dataItem.computationConfiguration.timeUnits
            bcGradient = dataItem.bcStrips.bcStrips

            # convert to minutes
            if timeUnits == "hours":
                exposedTime = exposedTime * 60.0
            if timeUnits == "seconds":
                exposedTime = exposedTime / 60.0

            # Compute the BCCResult
            bccResult, exitcode = bccResultComputation(sampledRGB, filterRadius, exposedTime, airFlowRate, bcGradient,
                                                       gradient, chartImage, tags, logging.DEBUG)
            chartImage.close()
            if exitcode is not ExitCode.Success:
                result.status = ExitCode.toString[exitcode]
                result.validFlag = False
                raise ResultComputationError(result.status, preProcessingResult, result)

            bccResult_ = BccResult(fitRed=bccResult.fitRed,
                                   fitGreen=bccResult.fitGreen,
                                   fitBlue=bccResult.fitBlue,
                                   rSquaredRed=bccResult.rSquaredRed,
                                   rSquaredGreen=bccResult.rSquaredGreen,
                                   rSquaredBlue=bccResult.rSquaredBlue,
                                   BCAreaRed=bccResult.BCAreaRed,
                                   BCAreaGreen=bccResult.BCAreaGreen,
                                   BCAreaBlue=bccResult.BCAreaBlue,
                                   BCVolRed=bccResult.BCVolRed,
                                   BCVolGreen=bccResult.BCVolGreen,
                                   BCVolBlue=bccResult.BCVolBlue)
            result.result = bccResult_
            result.status = ExitCode.toString[exitcode]
            result.validFlag = True

            self.log.info("Done Running COMPU", extra=tags)
            return result
        except Exception as err:
            if isinstance(err, ResultComputationError):
                raise err
            result = SuryaImageAnalysisResult()
            result.validFlag = False
            result.status = str(err)
            raise ResultComputationError(err, preProcessingResult, result)

    def checkExistingResult(self, itemname, dataItem, tags):
        """ Make sure we override any existing results
        """
        result = SuryaIANAResult.objects(item=dataItem.processEntity)
        if len(result) == 0:
            result = SuryaIANAFailedResult.objects(item=dataItem.processEntity)
            if len(result) == 0:
                return False
        ares = result[0]
        if ares.preProcessingResult != None:
            if ares.preProcessingResult.debugImage != None:
                self.log.info("Deleting existing debug image", extra=tags)
                ares.preProcessingResult.debugImage.delete()
        if ares.computationResult != None:
            if ares.computationResult.chartImage != None:
                self.log.info("Deleting existing chart image", extra=tags)
                ares.computationResult.chartImage.delete()
        self.log.info("Deleting existing result for %s" % (itemname), extra=tags)
        ares.delete()
        return True

    def saveDANAResult(self, itemname, dataItem, preProcessingResult, computationResult):
        """ Result DANAFramework.saveDANAResult fro documentation
        """
        try:
            dataItem.processedFlag = True
            dataItem.save()

            # Set the logging tags
            tags = self.ianatags + itemname + " SAVIN"

            self.log.info("Running SAVIN", extra=tags)

            existed = self.checkExistingResult(itemname, dataItem, tags)

            result = SuryaIANAResult()

            result.item = dataItem.processEntity
            result.preProcessingConfiguration = dataItem.preProcessingConfiguration
            result.preProcessingResult = preProcessingResult.result
            result.computationConfiguration = dataItem.computationConfiguration
            result.bcStrips = dataItem.bcStrips
            result.computationResult = computationResult
            result.status = "COMPLETE"
            if existed:
                result.isEmailed = True
            else:
                result.isEmailed = False
            result.date = datetime.now()
            result.save()

            self.log.info("Done Running SAVIN", extra=tags)
        except Exception as err:
            self.log.error("Unable to Save", exc_info=True)
            raise ResultSavingError(err)

    def onError(self, itemname, dataItem, err, phase):
        """ Refer DANAFramework.onError for documentation
        """

        dataItem.processedFlag = True
        dataItem.save()

        # Set the logging tags
        tags = self.ianatags + str(itemname) + " " + str(phase)

        self.log.error(str(phase) + " Failed, cause: " + str(err), extra=tags)

        existed = self.checkExistingResult(itemname, dataItem, tags)

        failedResult = SuryaIANAFailedResult()

        failedResult.item = dataItem.processEntity
        if existed:
            failedResult.isEmailed = True
        else:
            failedResult.isEmailed = False
        failedResult.status = phase
        failedResult.date = datetime.now()

        if phase == "PPROCCALIB" or phase == "SAVIN":
            failedResult.save()

        if phase == "PPROC" or phase == "COMPUCALIB":
            failedResult.preProcessingConfiguration = dataItem.preProcessingConfiguration
            failedResult.preProcessingResult = err.preProcessingResult
            failedResult.save()

        if phase == "COMPU":
            failedResult.preProcessingConfiguration = dataItem.preProcessingConfiguration
            failedResult.preProcessingResult = err.preProcessingResult
            failedResult.computationConfiguration = dataItem.computationConfiguration
            failedResult.bcStrips = dataItem.bcStrips
            failedResult.computationResult = err.computationResult
            failedResult.save()


if __name__ == "__main__":
    runinterval = 10
    if len(sys.argv) > 1:
        runinterval = int(sys.argv[1])
    connect("SuryaDB", tz_aware=True)
    iana = IANAFramework(logging.DEBUG)
    iana.run("IANAFramework.pid", "IANAFramework", runinterval)
