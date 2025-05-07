import pydicom

class LinkedTagList():
    def __init__(self):
        self.nextTagList = None
        self.tag = None
        self.itemIndex = None
        self.errorMessage = None
        self.sourceVal = None
        self.targetVal = None
    
    def buildTagListRecursive(self, tagList=None, stringList=""):
        stringListNew = stringList
        if tagList is None:
            tagList = self

        if tagList.tag is not None:
            stringListNew += str(tagList.tag)
        
        if tagList.itemIndex is not None:
            stringListNew += "[" + str(tagList.itemIndex) + "]: "
        
        if tagList.nextTagList is not None:
            stringListNew = self.buildTagListRecursive(tagList.nextTagList, stringListNew)
        
        return stringListNew
    
    def getLastItem(self, curItem=None):
        if curItem is None:
            curItem = self
        
        if curItem.nextTagList is not None:
            return self.getLastItem(curItem.nextTagList)
        else:
            return curItem

    def listContainsError(self):
        lastItem = self.getLastItem()
        return lastItem.errorMessage is not None


class DicomCompare():
    def __init__(self, onlyErrors=True):
        self.__diffTags = list()
        self.__onlyErrors = onlyErrors
    
    def compareFiles(self, filePathSource, filePathTarget):
        headerSource = pydicom.dcmread(filePathSource)
        headerTarget = pydicom.dcmread(filePathTarget)
        return self.compareHeaders(headerSource, headerTarget)
    
    def compareHeaders(self, headerSource, headerTarget):
        self.__compareHeaderRecursive(headerSource, headerTarget)
        return self.__diffTags
    
    def __compareHeaderRecursive(self, headerSource, headerTarget, tagListItem = None, levelZero=True):
        for item in headerSource:
            try:
                if levelZero:
                    tagListItem = LinkedTagList()
                    self.__diffTags.append(tagListItem)
                tagListItem.tag = item.tag

                ## Check if tag exists in target
                if not item.tag in headerTarget:
                    tagListItem.errorMessage = "Tag does not exist in target"
                    tagListItem.sourceVal = item.value
                    continue

                itemTarget = headerTarget[item.tag]

                if item.VR != "SQ":
                    ## Check value and VR
                    if item.value!=itemTarget.value:
                        tagListItem.errorMessage = "Value mismatch"
                        tagListItem.sourceVal = item.value
                        tagListItem.targetVal = itemTarget.value

                if item.VR=="SQ":
                    for i, subSet in enumerate(item.value):
                        tagListItem.itemIndex = i
                        newItem = LinkedTagList()
                        tagListItem.nextTagList = newItem
                        self.__compareHeaderRecursive(subSet, itemTarget.value[i], newItem, levelZero=False)
            except NotImplementedError as err:
                if levelZero:
                    tagListItem = LinkedTagList()
                    self.__diffTags.append(tagListItem)
                tagListItem.tag = item.tag

                tagListItem.errorMessage = str(err)
                tagListItem.sourceVal = ""
                tagListItem.targetVal = ""
        
        if self.__onlyErrors:
            self.__subsetErrorOnly()
    
    def getAllComparisons(self):
        return self.__diffTags
    
    def __subsetErrorOnly(self):
        newDiffTags = list()

        for item in self.__diffTags:
            if item.listContainsError():
                newDiffTags.append(item)
        
        self.__diffTags = newDiffTags