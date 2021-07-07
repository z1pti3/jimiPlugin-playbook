import time
from core import db, audit

# Initialize
dbCollectionName = "playbook"

class _playbook(db._document):
    name = str()
    occurrence = str()
    playbookData = dict()
    version = float()
    resultData = dict()
    result = bool()
    startTime = int()
    endTime = int()
    attempt = int()
    sequence = int()
    
    _dbCollection = db.db[dbCollectionName]

    def new(self, acl, name, occurrence, playbookData, version, sequence):
        self.acl = acl
        self.name = name
        self.occurrence = occurrence
        self.playbookData = playbookData
        self.version = version
        self.sequence = sequence
        self.startTime = int(time.time())
        return super(_playbook, self).new()

    def endPlay(self, result=False, resultData={}):
        if self.result == True:
            return
        self.result = result
        self.resultData = resultData
        self.endTime = int(time.time())
        self.update(["result","resultData","endTime"])

    def replay(self,keepHistory=False):
        if self.result == True:
            return
        if keepHistory:
            audit._audit().add("playbook","history",{ "startTime" : self.startTime, "endTime" : self.endTime, "result" : self.result, "resultData" : self.resultData, "version" : self.version, "attempt" : self.attempt })
        self.startTime = int(time.time())
        self.endTime = 0
        self.resultData = {}
        self.result = False
        self.attempt += 1
        self.update(["startTime","endTime","resultData","result","attempt"])

    def newPlay(self, version, keepHistory=False):
        if keepHistory:
            audit._audit().add("playbook","history",{ "startTime" : self.startTime, "endTime" : self.endTime, "result" : self.result, "resultData" : self.resultData, "version" : self.version, "attempt" : self.attempt })
        self.version = version
        self.startTime = int(time.time())
        self.endTime = 0
        self.resultData = {}
        self.result = False
        self.attempt = 0
        self.update(["version","startTime","endTime","resultData","result","attempt"])

