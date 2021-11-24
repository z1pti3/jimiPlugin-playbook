from plugins.playbook.models import playbook

import jimi 

class _playbookSearch(jimi.trigger._trigger):
    playbookName = str()
    sequence = int()
    inComplete = bool()
    excludeIncrementSequence = bool()
    playbookLimit = 5
    excludeMaxAttempts = True

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
                        "doc" : { "$last" : "$$ROOT" }
                    }
                },
                {
                    "$unwind" : "$doc"
                },
                {
                    "$match" : {
                        "$or" : [
                            {
                                "doc.sequence" : self.sequence,
                                "doc.result" : True
                            },
                            {
                                "doc.sequence" :  self.sequence + 1,
                                "doc.result" : False
                            }
                        ] 
                    }
                },
                {
                    "$project" : {
                        
                    }
                },
            ]
            for field in playbook.playbokFields:
                aggregateStatement[5]["$project"][field] = "$doc.{0}".format(field)
            playbooks = playbook._playbook().aggregate(aggregateStatement=aggregateStatement,limit=self.playbookLimit)
        else:
            playbooks = playbook._playbook().query(query={"name" : self.playbookName, "sequence" : self.sequence, "result" : not self.inComplete },limit=self.playbookLimit,fields=playbook.playbokFields)["results"]
        self.result["events"] = playbooks