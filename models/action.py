import time

from core import helpers, cache
from core.models import action
from plugins.playbook.models import playbook

import jimi

class _playbookStart(action._action):
    playbookName = str()
    occurrence = str()
    playbookData = dict()
    version = float()
    alwaysRun = bool()
    maxAttempts = int()
    keepHistory = bool()
    delayBetweenAttempts = int()
    sequence = int()

    def __init__(self):
        cache.globalCache.newCache("playbookCache")

    def run(self,data,persistentData,actionResult):
        playbookName = helpers.evalString(self.playbookName,{"data" : data})
        occurrence = helpers.evalString(self.occurrence,{"data" : data})
        playbookData = helpers.evalDict(self.playbookData,{ "data" : data })

        delayBetweenAttempts = 300
        if self.delayBetweenAttempts != 0 :
            delayBetweenAttempts = self.delayBetweenAttempts

        if self.sequence > 0:
            match = "{0}-{1}-{2}".format(playbookName,occurrence,self.sequence-1)
            plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence-1,customCacheTime=delayBetweenAttempts)
            if plays:
                play = plays[0]
                if not play.result:
                    actionResult["result"] = False
                    actionResult["msg"] = "Previous sequence not completed successfully"
                    actionResult["rc"] = 403
                    return actionResult
            else:
                actionResult["result"] = False
                actionResult["msg"] = "No previous sequence attempted"
                actionResult["rc"] = 404
                return actionResult

        # Build a UID match for future reference
        match = "{0}-{1}-{2}".format(playbookName,occurrence,self.sequence)

        plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts)
        if not plays:
            playbook._playbook().new(self.acl,playbookName,occurrence,playbookData,self.version,self.sequence)
            plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts)
            if plays:
                if len(plays) > 1:
                    for p in range(1,len(plays)):
                        plays[p].delete()
                    plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts,forceUpdate=True)
                play = plays[0]
                data["plugin"]["playbook"] = { "match" : match, "name": playbookName, "occurrence": occurrence, "playbookData" : play.playbookData, "sequence": self.sequence, "version" : self.version }
                actionResult["result"] = True
                actionResult["rc"] = 201
                return actionResult
        else:
            if len(plays) > 1:
                for p in range(1,len(plays)):
                    plays[p].delete()
                plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts,forceUpdate=True)
            play = plays[0]
            data["plugin"]["playbook"] = { "match" : match, "name": playbookName, "occurrence": occurrence, "playbookData" : play.playbookData, "sequence": self.sequence, "version" : self.version }

            if play.startTime + delayBetweenAttempts > time.time():
                actionResult["result"] = False
                actionResult["msg"] = "Delay time between attempts not met"
                actionResult["rc"] = 300
                return actionResult

            if ((play.version < self.version) or (self.alwaysRun)):
                play.newPlay(self.version,self.keepHistory)
                actionResult["result"] = True
                actionResult["msg"] = "Complete"
                actionResult["rc"] = 205
                return actionResult
            elif ((play.result == False) and (play.attempt < self.maxAttempts)):
                play.replay(self.keepHistory)
                actionResult["result"] = True
                actionResult["msg"] = "Complete on additional attempt"
                actionResult["rc"] = 302
                return actionResult

            elif ((play.result == False) and (play.attempt >= self.maxAttempts)):
                play.replay(self.keepHistory)
                actionResult["result"] = True
                actionResult["msg"] = "No attempts remaining"
                actionResult["rc"] = 305
                return actionResult

            actionResult["result"] = False
            actionResult["msg"] = "Nothing to do"
            actionResult["rc"] = 304
            return actionResult
       
        actionResult["result"] = False
        actionResult["msg"] = "Unknown"
        actionResult["rc"] = 500
        return actionResult

class _playbookEnd(action._action):
    result = bool()
    resultData = dict()

    def run(self,data,persistentData,actionResult):
        resultData = helpers.evalDict(self.resultData,{"data" : data})
        if "playbook" in data["plugin"]:
            match = data["plugin"]["playbook"]["match"]
            playbookName = data["plugin"]["playbook"]["name"]
            occurrence = data["plugin"]["playbook"]["occurrence"]
            sequence = data["plugin"]["playbook"]["sequence"]
            plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,sequence,extendCacheTime=True)
            if plays:
                play = plays[0]
                play.endPlay(self.result,resultData)
                actionResult["result"] = True
                actionResult["msg"] = "Playbook Complete Success"
                actionResult["rc"] = 0
                return actionResult
        actionResult["result"] = False
        actionResult["msg"] = "Playbook Complete Failure"
        actionResult["rc"] = 404
        return actionResult

class _playbookGet(action._action):
    occurrence = str()
    playbookName = str()

    def run(self,data,persistentData,actionResult):
        occurrence = helpers.evalString(self.occurrence,{"data" : data})
        playbookName = helpers.evalString(self.playbookName,{"data" : data})

        playbookResult = playbook._playbook().query(query={"name" : playbookName, "occurrence" : occurrence })["results"]
        if len(playbookResult) > 0:
            actionResult["result"] = True
            actionResult["msg"] = "Play found"
            actionResult["playbook"] = playbookResult[0]
            actionResult["rc"] = 0
            return actionResult
        actionResult["result"] = False
        actionResult["msg"] = "Play not found"
        actionResult["rc"] = 404
        return actionResult

class _playbookAdd(action._action):
    occurrence = str()
    playbookName = str()
    playbookData = dict()

    def doAction(self,data):
        occurrence = helpers.evalString(self.occurrence,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        playbookName = helpers.evalString(self.playbookName,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        playbookData = helpers.evalDict(self.playbookData,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})

        playbookResult = playbook._playbook().query(query={"name" : playbookName, "occurrence" : occurrence })["results"]
        if len(playbookResult) == 0:
            playbook._playbook().new(self.acl,playbookName,occurrence,playbookData,-1,0)
            return { "result" : True, "rc" : 0, "msg" : "Added new playbook entry"}
        return { "result" : False, "rc" : 1, "msg" : "Existing playbook entry found, playbook={0}, occurrence={1}".format(playbookName,occurrence)}

class _playbookUpdateData(action._action):
    occurrence = str()
    playbookName = str()
    playbookData = dict()

    def doAction(self,data):
        occurrence = helpers.evalString(self.occurrence,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        playbookName = helpers.evalString(self.playbookName,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        playbookData = helpers.evalDict(self.playbookData,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})

        playbookResult = playbook._playbook().getAsClass(query={"name" : playbookName, "occurrence" : occurrence })
        if len(playbookResult) > 0:
            playbookResult = playbookResult[0]
            playbookResult.playbookData = playbookData
            playbookResult.update(["playbookData"])
            return { "result" : True, "rc" : 0, "msg" : "playbookData update "}
        return { "result" : False, "rc" : 1, "msg" : "No existing playbook entry found, playbook={0}, occurrence={1}".format(playbookName,occurrence)}

class _playbookStartUpdate(action._action):
    action_id = str()
    version = str()
    maxAttempts = str()
    delayBetweenAttempts = str()
    sequence = str()

    def doAction(self,data):
        action_id = helpers.evalString(self.action_id,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        version = helpers.evalString(self.version,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        maxAttempts = helpers.evalString(self.maxAttempts,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        delayBetweenAttempts = helpers.evalString(self.delayBetweenAttempts,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})
        sequence = helpers.evalString(self.sequence,{"data" : data["flowData"],"eventData" : data["eventData"],"conductData" : data["conductData"],"persistentData" : data["persistentData"]})

        playbookAction = _playbookStart().getAsClass(id=jimi.db.ObjectId(action_id))
        if len(playbookAction) == 1:
            playbookAction = playbookAction[0]
            fields = []
            if version:
                playbookAction.version = float(version)
                fields.append("version")
            if maxAttempts:
                playbookAction.maxAttempts = int(maxAttempts)
                fields.append("maxAttempts")
            if delayBetweenAttempts:
                playbookAction.delayBetweenAttempts = int(delayBetweenAttempts)
                fields.append("delayBetweenAttempts")
            if sequence:
                playbookAction.sequence = int(sequence)
                fields.append("sequence")
            playbookAction.update([fields])
            return { "result" : True, "rc" : 0, "msg" : "playbookStart action updated, action_id={0}".format(action_id)}
        else:
            return { "result" : False, "rc" : 255, "msg" : "No playbookStart action found, action_id={0}".format(action_id)}

class _playbookSearchAction(action._action):
    playbookName = str()
    sequence = int()
    incomplete = bool()
    excludeIncrementSequence = bool()
    playbookLimit = 5

    def run(self,data,persistentData,actionResult):
        playbookName = helpers.evalString(self.playbookName,{"data" : data})

        playbooks = playbook._playbook().query(query={"name" : self.playbookName, "sequence" : self.sequence, "result" : not self.incomplete },limit=self.playbookLimit)["results"]
        incrementOccurrences = []
        if self.excludeIncrementSequence:
            playbooks2 = playbook._playbook().query(query={"name" : self.playbookName, "sequence" : self.sequence + 1, "result" : True }, limit=self.playbookLimit)["results"]
            incrementOccurrences = [ x["occurrence"] for x in playbooks2 ]
        results = []
        for playbookItem in playbooks:
            result = {}
            if playbookItem["occurrence"] not in incrementOccurrences:
                for key ,value in playbookItem.items():
                    if key not in helpers.systemProperties:
                        result[key] = value
                results.append(result)
        if len(results) > 0:
            actionResult["result"] = True
            actionResult["msg"] = "Occurrences found"
            actionResult["playbook"] = results
            actionResult["rc"] = 0
            return actionResult
        actionResult["result"] = False
        actionResult["msg"] = "No occurrences not found"
        actionResult["rc"] = 404
        return actionResult

def getPlaybookObject(match,sessionData,playbookName,occurrence,sequence):
    return playbook._playbook().getAsClass(query={"name" : playbookName, "occurrence" : occurrence, "sequence" : sequence })

