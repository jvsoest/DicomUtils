import pydicom
import os

class DicomDatabase:
    def __init__(self):
        self.patient = dict()
    
    def parseFolder(self, folderPath):
        for root, subdirs, files in os.walk(folderPath):
            for filename in files:
                file_path = os.path.join(root, filename)
                if ".dcm" in file_path:
                    try:
                        dcmHeader = pydicom.dcmread(file_path)
                        patientId = dcmHeader[0x10,0x20].value
                        patient = self.getOrCreatePatient(patientId)
                        patient.addFile(file_path, dcmHeader)
                    except Exception as e:
                        pass
                        print(e)
                        print("Error while reading %s" % file_path)

    def getOrCreatePatient(self, patientId):
        if not (patientId in self.patient):
            self.patient[patientId] = Patient()
        return self.patient[patientId]
    
    def countPatients(self):
        return len(self.patient)
    
    def getPatient(self, patientId):
        if patientId in self.patient:
            return self.patient[patientId]
        else:
            return None
    
    def getPatientIds(self):
        return self.patient.keys()
    
    def doesPatientExist(self, patientId):
        # return self.patient.has_key(patientId)
        return patientId in self.patient
class Patient:
    def __init__(self):
        self.series = dict()
        self.rtstruct = dict()
        self.id = ""

    def addFile(self, filePath, dcmHeader):
        self.id = dcmHeader[0x10,0x20].value
        modality = dcmHeader[0x8,0x60].value
        sopInstanceUid = dcmHeader[0x8,0x18].value
        seriesInstanceUid = dcmHeader[0x20,0xe].value
        
        if not (seriesInstanceUid in self.series):
            self.series[seriesInstanceUid] = Series()
        myCT = self.series[seriesInstanceUid]
        myCT.addFile(dcmHeader, filePath)
    
    def countSeries(self):
        return len(self.series)
    def countRTStructs(self):
        return len(self.rtstruct)
    
    def getInstance(self, seriesInstanceUid, sopInstanceUid):
        if seriesInstanceUid in self.series:
            serie = self.series[seriesInstanceUid]
            if sopInstanceUid in serie.filePath:
                return serie.filePath[sopInstanceUid]
        return None

    def getCTScan(self, seriesInstanceUid):
        if seriesInstanceUid is not None:
            if self.doesSeriesExist(seriesInstanceUid):
                return self.series[seriesInstanceUid]
        return None
    def getRTStruct(self, sopInstanceUid):
        return self.rtstruct[sopInstanceUid]
    
    def getCTScans(self):
        return self.series.keys()
    def getRTStructs(self):
        return self.rtstruct.keys()
    
    def doesSeriesExist(self, seriesInstanceUid):
        # return self.ct.has_key(seriesInstanceUid)
        return seriesInstanceUid in self.series
    def doesRTStructExist(self, sopInstanceUid):
        # return self.rtstruct.has_key(sopInstanceUid)
        return sopInstanceUid in self.rtstruct
    
    def getSeriesForRTStruct(self, rtStruct):
        if rtStruct.getReferencedCTUID() is not None:
            return self.getCTScan(rtStruct.getReferencedCTUID())
        else:
            return None

class Series:
    def __init__(self):
        self.filePath = dict()
        self.uid = None
        self.modality = None
        self.description = None
        self.studyDate = "19700101"
        self.scanId = 999
    def addFile(self, dcmHeader, filePath):
        self.uid = dcmHeader[0x20,0xe].value
        self.modality = dcmHeader[0x8,0x60].value
        
        descTag = [0x8,0x103e]
        if descTag in dcmHeader:
            self.description = dcmHeader[descTag].value
        
        tagValueStudyDate = dcmHeader[0x8,0x20].value
        if tagValueStudyDate is not None:
            if tagValueStudyDate > self.studyDate:
                self.studyDate = tagValueStudyDate
        self.scanId = dcmHeader[0x20, 0x11].value
        self.filePath[dcmHeader[0x8,0x18].value] = filePath
    def getFiles(self):
        return self.filePath

class RTStruct(Series):
    def __init__(self, filePath):
        self.filePath = filePath
    def getHeader(self):
        return pydicom.dcmread(self.filePath)
    def getReferencedCTUID(self):
        dcmHeader = self.getHeader()
        if len(list(dcmHeader[0x3006,0x10])) > 0:
            refFrameOfRef = (dcmHeader[0x3006,0x10])[0]
            if len(list(refFrameOfRef[0x3006, 0x0012])) > 0:
                rtRefStudy = (refFrameOfRef[0x3006, 0x0012])[0]
                if len(list(rtRefStudy[0x3006,0x14])) > 0:
                    rtRefSerie = (rtRefStudy[0x3006,0x14])[0]
                    return rtRefSerie[0x20,0xe].value
        return None
    def getFileLocation(self):
        return self.filePath
