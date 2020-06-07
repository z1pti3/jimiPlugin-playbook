from core import helpers, cache
from core.models import action
from plugins.playbook.models import playbook

class _playbookStart(action._action):
    name = str()
    occurrence = str()
    version = float()
    alwaysRun = bool()

    def __init__(self):
        cache.globalCache.newCache("playbookCache")

    def run(self,data,persistentData,actionResult):
        name = helpers.evalString(self.name,{"data" : data})
        occurrence = helpers.evalString(self.occurrence,{"data" : data})
        # Build a UID match for future reference
        match = "{0}-{1}-{2}".format(self.id,name,occurrence)

        plays = cache.globalCache.get("playbookCache",match,getPlaybookObject,name,occurrence,extendCacheTime=True)
        if not plays:
            playID = playbook._playbook().new(name,occurrence,self.version).inserted_id
            play = playbook._playbook().getAsClass(id=playID)[0]
            data["plugin"]["playbook"] = play
            actionResult["result"] = True
            actionResult["rc"] = 201
            return actionResult
        else:
            play = plays[0]
            data["plugin"]["playbook"] = play
            if ((play.version < self.version) or (self.alwaysRun)):
                play.newPlay(self.version)
                actionResult["result"] = True
                actionResult["rc"] = 205
                return actionResult
            elif ((play.result == False) and (play.attempt < self.maxAttempts)):
                play.replay()
                actionResult["result"] = True
                actionResult["rc"] = 302
                return actionResult

            actionResult["result"] = False
            actionResult["rc"] = 304
            return actionResult
       
        actionResult["result"] = False
        actionResult["rc"] = 500
        return actionResult

class _playbookEnd(action._action):
    result = bool()
    resultData = str()

    def run(self,data,persistentData,actionResult):
        resultData = helpers.evalString(self.resultData,{"data" : data})

        if "playbook" in data["plugin"]:
            play = data["plugin"]["playbook"]
            play.endPlay(self.result,resultData)
            actionResult["result"] = True
            actionResult["rc"] = 0
            return actionResult
        else:
            actionResult["result"] = False
            actionResult["rc"] = 404
            return actionResult


def getPlaybookObject(match,sessionData,name,occurrence):
    return playbook._playbook().getAsClass(query={"name" : name, "occurrence" : occurrence })