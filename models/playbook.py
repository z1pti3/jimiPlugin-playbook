import time
from core import db, helpers, logging

# Initialize
dbCollectionName = "playbook"

class _playbook(db._document):
    name = str()
    host = str()
    version = float()
    result = dict()

    _dbCollection = db.db[dbCollectionName]

    def new(self, domain, acl):
        self.name = domain
        self.domain = domain
        self.createdDate = int(time.time())
        self.acl = acl
        return super(_playbook, self).new()

    def updateRecord(self, domain, ip="", mx=False, when="", fuzzer=""):
        self.history.append( { "lastUpdate" : self.lastUpdateTime, "endDate" : int(time.time()), "domain" : self.domain, "ip" : self.ip, "mx" : self.mx, "when" : self.when } )
        self.update(["history"])
        self.domain = domain
        self.ip = ip
        self.mx = mx
        self.when = when
        self.fuzzer = fuzzer
        self.update(["domain","ip","mx","when","fuzzer"])

