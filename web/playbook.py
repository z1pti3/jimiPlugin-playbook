import urllib.parse
from pathlib import Path
from flask import Blueprint, render_template
from flask import current_app as app
from flask import request, send_from_directory
from markupsafe import Markup

import time

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

@pluginPages.route('/playbook/includes/<file>')
def custom_static(file):
    return send_from_directory(str(Path("plugins/playbook/web/includes")), file)

@pluginPages.route("/playbook/")
def mainPage():
    foundPlays = playbook._playbook().query(sessionData=api.g.sessionData)["results"]
    playbooks = []
    for play in foundPlays:
        if play["name"] not in playbooks:
            playbooks.append(play["name"])
    return render_template("playbooks.html", content=playbooks)


@pluginPages.route("/playbook/<playbookName>/")
def getPlaybookByName(playbookName):
    foundPlays = playbook._playbook().query(sessionData=api.g.sessionData,query={"name" : playbookName})["results"]
    plays = []
    pie = {"complete" : 0, "incomplete" : 0}
    for play in foundPlays:
        plays.append(play)
        if play["result"]:
            pie["complete"] += 1
        else:
            pie["incomplete"] += 1
    return render_template("playbook.html", content=plays, pie=pie, name=playbookName)


@pluginPages.route("/playbook/<occurrenceID>/clear/")
def clearPlaybookOccurrence(occurrenceID):
    foundOccurence =  playbook._playbook().query(sessionData=api.g.sessionData,id=occurrenceID)["results"]
    if len(foundOccurence) == 1:
        playbook._playbook().api_delete(id=occurrenceID)
        return {}, 200
    else:
        return (), 404