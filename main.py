# -*- coding: utf-8 -*-

"""
Anki Add-on: Speed Focus Mode

Based on "Automatically show answer after X seconds"
(https://ankiweb.net/shared/info/648362761)

The original author of this add-on is unknown, sadly,
but all credit for the original idea goes to them.

Copyright: (c) 2017-2019 Glutanimate <https://glutanimate.com/>
License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>
"""

from __future__ import unicode_literals

import sys
import os

from aqt.qt import *
from aqt import mw
from aqt.reviewer import Reviewer
from aqt.deckconf import DeckConf
from aqt.forms import dconf
from aqt.utils import tooltip

from anki.hooks import addHook, wrap
from anki.sound import play


# Anki 2.1 support
from anki import version as anki_version
anki21 = anki_version.startswith("2.1.")
pycmd = "pycmd" if anki21 else "py.link"


# determine sound file path
sys_encoding = sys.getfilesystemencoding()

if anki21:
    addon_path = os.path.dirname(__file__)
else:
    addon_path = os.path.dirname(__file__).decode(sys_encoding)

alert_path = os.path.join(addon_path, "sounds", "alert.mp3")


#autoalerttimeout originally:  autoAgainTimeout = setTimeout(function () { %s("ease3"); }, ms);
# autoAgainTimeout = setTimeout(function () { document.querySelector("#defease").click(); }, ms);


#// autoAgainTimeout = setTimeout(function () { document.querySelector("#good").click(); }, ms);
#// you can change #good it this line to change the aytomatically pressed button. <- line 70

def append_html(self, _old):
    return _old(self) + """
        <script>
            var autoAnswerTimeout = 0;
            var autoAgainTimeout = 0;
            var autoAlertTimeout = 0;

            var setAutoAnswer = function(ms) {
                clearTimeout(autoAnswerTimeout);
                autoAnswerTimeout = setTimeout(function () { %s('ans') }, ms);
            }
            var setAutoAgain = function(ms) {
                clearTimeout(autoAgainTimeout);
                //autoAgainTimeout = setTimeout(function () { %s("ease1"); }, ms);
                autoAgainTimeout = setTimeout(function () { document.querySelector("#good").click(); }, ms);
            }
            var setAutoAlert = function(ms) {
                clearTimeout(autoAlertTimeout);
                autoAlertTimeout = setTimeout(function () { %s("autoalert"); }, ms);
            }
        </script>
        """ % (pycmd, pycmd, pycmd)


# set timeouts for auto-alert and auto-reveal
def set_answer_timeout(self):
    c = self.mw.col.decks.confForDid(self.card.odid or self.card.did)
    if c.get('autoAnswer', 0) > 0:
        self.bottom.web.eval("setAutoAnswer(%d);" % (c['autoAnswer'] * 1000))
    if c.get('autoAlert', 0) > 0:
        self.bottom.web.eval("setAutoAlert(%d);" % (c['autoAlert'] * 1000))

# set timeout for auto-again
def set_again_timeout(self):
    c = self.mw.col.decks.confForDid(self.card.odid or self.card.did)
    if c.get('autoAgain', 0) > 0:
        self.bottom.web.eval("setAutoAgain(%d);" % (c['autoAgain'] * 1000))



# clear timeouts for auto-alert and auto-reveal, run on answer reveal
def clear_answer_timeout():
    mw.reviewer.bottom.web.eval("""
        if (typeof autoAnswerTimeout !== 'undefined') {
            clearTimeout(autoAnswerTimeout);
        }
        if (typeof autoAlertTimeout !== 'undefined') {
            clearTimeout(autoAlertTimeout);
        }
    """)

# clear timeout for auto-again, run on next card
def clear_again_timeout():
    mw.reviewer.bottom.web.eval("""
        if (typeof autoAgainTimeout !== 'undefined') {
            clearTimeout(autoAgainTimeout);
        }
    """)


def setup_ui(self, Dialog):
    self.maxTaken.setMinimum(3)

    grid = QGridLayout()
    label1 = QLabel(self.tab_5)
    label1.setText(_("Automatically play alert after"))
    label2 = QLabel(self.tab_5)
    label2.setText(_("seconds"))
    self.autoAlert = QSpinBox(self.tab_5)
    self.autoAlert.setMinimum(0)
    self.autoAlert.setMaximum(3600)
    grid.addWidget(label1, 0, 0, 1, 1)
    grid.addWidget(self.autoAlert, 0, 1, 1, 1)
    grid.addWidget(label2, 0, 2, 1, 1)
    self.verticalLayout_6.insertLayout(1, grid)

    grid = QGridLayout()
    label1 = QLabel(self.tab_5)
    label1.setText(_("Automatically show answer after"))
    label2 = QLabel(self.tab_5)
    label2.setText(_("seconds"))
    self.autoAnswer = QSpinBox(self.tab_5)
    self.autoAnswer.setMinimum(0)
    self.autoAnswer.setMaximum(3600)
    grid.addWidget(label1, 0, 0, 1, 1)
    grid.addWidget(self.autoAnswer, 0, 1, 1, 1)
    grid.addWidget(label2, 0, 2, 1, 1)
    self.verticalLayout_6.insertLayout(2, grid)

    grid = QGridLayout()
    label1 = QLabel(self.tab_5)
    label1.setText(_("Automatically rate 'good' after"))
    label2 = QLabel(self.tab_5)
    label2.setText(_("seconds"))
    self.autoAgain = QSpinBox(self.tab_5)
    self.autoAgain.setMinimum(0)
    self.autoAgain.setMaximum(3600)
    grid.addWidget(label1, 0, 0, 1, 1)
    grid.addWidget(self.autoAgain, 0, 1, 1, 1)
    grid.addWidget(label2, 0, 2, 1, 1)
    self.verticalLayout_6.insertLayout(3, grid)


def load_conf(self):
    f = self.form
    c = self.conf
    f.autoAlert.setValue(c.get('autoAlert', 0))
    f.autoAnswer.setValue(c.get('autoAnswer', 0))
    f.autoAgain.setValue(c.get('autoAgain', 0))


def save_conf(self):
    f = self.form
    c = self.conf
    c['autoAlert'] = f.autoAlert.value()
    c['autoAnswer'] = f.autoAnswer.value()
    c['autoAgain'] = f.autoAgain.value()


# Sound playback

def linkHandler(self, url, _old):
    if not url.startswith("autoalert"):
        return _old(self, url)
    if not self.mw.col:
        # collection unloaded, e.g. when called during pre-exit sync
        return
    play(alert_path)
    c = self.mw.col.decks.confForDid(self.card.odid or self.card.did)
    timeout = c.get('autoAlert', 0)
    tooltip("Wake up! You have been looking at <br>"
            "the question for <b>{}</b> seconds!".format(timeout),
            period=1000)


# Hooks

Reviewer._bottomHTML = wrap(Reviewer._bottomHTML, append_html, 'around')
Reviewer._showAnswerButton = wrap(
    Reviewer._showAnswerButton, set_answer_timeout)
Reviewer._showEaseButtons = wrap(Reviewer._showEaseButtons, set_again_timeout)
Reviewer._linkHandler = wrap(Reviewer._linkHandler, linkHandler, "around")
addHook("showAnswer", clear_answer_timeout)
addHook("showQuestion", clear_again_timeout)

dconf.Ui_Dialog.setupUi = wrap(dconf.Ui_Dialog.setupUi, setup_ui)
DeckConf.loadConf = wrap(DeckConf.loadConf, load_conf)
DeckConf.saveConf = wrap(DeckConf.saveConf, save_conf, 'before')

# Pause addition

def pause():
    if  mw.state == 'review':
        clear_again_timeout()
        clear_answer_timeout()
        tooltip('Paused', period=1000)

##// Here you can change the shortcut. "P" wasn't working on my anki, so i changed it to "Shift+P", you can change it back to "P" if you want
mw.form.menuTools.addAction('Pause speed focus mode', pause, 'Shift+P')
