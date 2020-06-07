from core import helpers
from core.models import action
from plugins.playbook.models import playbook

class _playbookStart(action._action):
    name = str()
    itemReference = str()
    version = float()

    def run(self,data,persistentData,actionResult):
        name = helpers.evalString(self.name,{"data" : data})
        itemReference = helpers.evalString(self.itemReference,{"data" : data})
       
        actionResult["result"] = False
        actionResult["rc"] = 500
        return actionResult

class _playbookEnd(action._action):

    def run(self,data,persistentData,actionResult):
       
        actionResult["result"] = False
        actionResult["rc"] = 500
        return actionResult