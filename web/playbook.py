import urllib.parse
from pathlib import Path
from flask import Blueprint, render_template
from flask import current_app as app
from flask import request, send_from_directory
from markupsafe import Markup

import time

import jimi

from web import ui
from core import api
from plugins.playbook.models import playbook

pluginPages = Blueprint('playbookPages', __name__, template_folder="templates")

@pluginPages.app_template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote_plus(s)
    return Markup(s)

@pluginPages.route('/includes/<file>')
def custom_static(file):
    return send_from_directory(str(Path("plugins/playbook/web/includes")), file)

@pluginPages.route("/")
def mainPage():
    foundPlays = playbook._playbook().query(sessionData=api.g.sessionData)["results"]
    playbooks = []
    for play in foundPlays:
        if "name" in play:
            if play["name"] not in playbooks:
                playbooks.append(play["name"])
    return render_template("playbooks.html", content=playbooks)

@pluginPages.route("/<playbookName>/")
def getPlaybookByName(playbookName):
    foundPlays = playbook._playbook().query(sessionData=api.g.sessionData,query={"name" : playbookName})["results"]
    plays = []
    pie = {"complete" : 0, "incomplete" : 0, "running" : 0}
    for play in foundPlays:
        plays.append(play)
        if play["result"]:
            pie["complete"] += 1
        elif play["endTime"] == 0:
            pie["running"] += 1
        else:
            pie["incomplete"] += 1
    return render_template("playbook.html", pie=pie, name=playbookName)

@pluginPages.route("/<playbookName>/playbookResultsTable/<action>/")
def activeEventsTable(playbookName,action):
    foundPlays = playbook._playbook().getAsClass(sessionData=api.g.sessionData,query={"name" : playbookName})
    total = len(foundPlays)
    columns = ["_id","name","sequence","version","occurrence","playbookData","startTime","endTime","attempt","result","resultData","options"]
    table = ui.table(columns,total,total)
    if action == "build":
        return table.getColumns() ,200
    elif action == "poll":
        # Custom table data so it can be vertical
        data = []
        for play in foundPlays:
            data.append([ui.safe(play._id),ui.dictTable(play.name),ui.dictTable(play.sequence),ui.dictTable(play.version),ui.dictTable(play.occurrence),ui.dictTable(play.playbookData),ui.dictTable(play.startTime),ui.dictTable(play.endTime),ui.dictTable(play.attempt),ui.dictTable(play.result),ui.dictTable(play.resultData),'<button class="btn btn-primary theme-panelButton clearPlay" id="'+play._id+'">Delete</button>'])
        table.data = data
        return { "draw" : int(jimi.api.request.args.get('draw')), "recordsTable" : 0, "recordsFiltered" : 0, "recordsTotal" : 0, "data" : data } ,200



@pluginPages.route("/<playbookName>/<occurrenceID>/clear/")
def clearPlaybookOccurrence(playbookName,occurrenceID):
    foundOccurence =  playbook._playbook().query(sessionData=api.g.sessionData,id=occurrenceID)["results"]
    if len(foundOccurence) == 1:
        playbook._playbook().api_delete(id=occurrenceID)
        return {}, 200
    else:
        return (), 404