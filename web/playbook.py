from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time

from plugins.playbook.models import playbook

pluginPages = Blueprint('playbookPages', __name__, template_folder="templates")

@pluginPages.route("/playbook/")
def mainPage():
    foundPlays = playbook._playbook().query()["results"]
    plays = []
    for play in foundPlays:
        plays.append(play)
    return render_template("playbook.html", plays=plays)

