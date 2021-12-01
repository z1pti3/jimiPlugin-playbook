import time

from plugins.playbook.models import playbook

import jimi 

class _playbookSearch(jimi.trigger._trigger):
    playbookName = str()
    sequence = int()
    incomplete = False
    excludeIncrementSequence = True
    playbookLimit = 5
    maxAttempts = int()
    delayBetweenAttempts = int()

    def check(self):
        if self.excludeIncrementSequence:
            aggregateStatement = [
                {
                    "$match" : {
                        "name" : self.playbookName,
                        "sequence" : { "$gte" : self.sequence },
                        "sequence" : { "$lte" : self.sequence + 1 },
                    }
                },
                {
                    "$sort" : { "sequence" : 1 }
                },
                {
                    "$group" : {
                        "_id" : "$occurrence",
                        "last_sequence" : { "$last" : "$$ROOT" },
                        "first_sequence" : { "$first" : "$$ROOT" }
                    }
                },
                {
                    "$unwind" : "$last_sequence"
                },
                {
                    "$match" : {
                        "$and" : [
                            {
                                "$or" : [
                                    {
                                        "last_sequence.sequence" : self.sequence,
                                        "last_sequence.result" : True
                                    },
                                    {
                                        "last_sequence.sequence" :  self.sequence + 1,
                                        "last_sequence.result" : False
                                    }
                                ] 
                            }
                        ]
                    }
                },
                {
                    "$unwind" : "$first_sequence"
                },
                {
                    "$project" : {
                        
                    }
                },
            ]
            for field in playbook.playbokFields:
                aggregateStatement[6]["$project"][field] = "$first_sequence.{0}".format(field)
            if self.maxAttempts:
                aggregateStatement[4]["$match"]["$and"][0]["$or"][1]["last_sequence.attempt"] = { "$lt" : self.maxAttempts }
            else:
                aggregateStatement[4]["$match"]["$and"][0]["$or"][1]["last_sequence.attempt"] = { "$lt" : 1 }
            if self.delayBetweenAttempts != 0:
                aggregateStatement[4]["$match"]["$and"][0]["$or"][1]["last_sequence.startTime"] = { "$lt" : time.time() - self.delayBetweenAttempts }
            else:
                aggregateStatement[4]["$match"]["$and"][0]["$or"][1]["last_sequence.startTime"] = { "$lt" : time.time() - 300 }
            playbooks = playbook._playbook().aggregate(aggregateStatement=aggregateStatement,limit=self.playbookLimit)
        else:
            playbooks = playbook._playbook().query(query={"name" : self.playbookName, "sequence" : self.sequence, "result" : not self.incomplete },limit=self.playbookLimit,fields=playbook.playbokFields)["results"]
        self.result["events"] = playbooks
