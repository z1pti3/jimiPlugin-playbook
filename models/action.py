import time

from core import helpers, cache
from core.models import action
from plugins.playbook.models import playbook

class _playbookStart(action._action):
    playbookName = str()
    occurrence = str()
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
            playbook._playbook().new(self.acl,playbookName,occurrence,self.version,self.sequence)
            plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts)
            if plays:
                if len(plays) > 1:
                    for p in range(1,len(plays)):
                        plays[p].delete()
                    plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts,forceUpdate=True)
                play = plays[0]
                data["plugin"]["playbook"] = { "match" : match, "name": playbookName, "occurrence": occurrence, "sequence": self.sequence }
                actionResult["result"] = True
                actionResult["rc"] = 201
                return actionResult
        else:
            if len(plays) > 1:
                for p in range(1,len(plays)):
                    plays[p].delete()
                plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,playbookName,occurrence,self.sequence,customCacheTime=delayBetweenAttempts,forceUpdate=True)
            play = plays[0]
            data["plugin"]["playbook"] = { "match" : match, "name": playbookName, "occurrence": occurrence, "sequence": self.sequence }

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


def getPlaybookObject(match,sessionData,playbookName,occurrence,sequence):
    return playbook._playbook().getAsClass(query={"name" : playbookName, "occurrence" : occurrence, "sequence" : sequence })