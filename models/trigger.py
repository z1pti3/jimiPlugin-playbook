from plugins.playbook.models import playbook

from core.models import trigger

from core import helpers    

class _playbookSearch(trigger._trigger):
    playbookName = str()
    sequence = int()
    inComplete = bool()
    excludeIncrementSequence = bool()
    playbookLimit = 5
    excludeMaxAttempts = True

    def check(self):
        playbooks = playbook._playbook().query(query={"name" : self.playbookName, "sequence" : self.sequence, "result" : not self.inComplete },limit=self.playbookLimit)["results"]
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
        self.result["events"] = results