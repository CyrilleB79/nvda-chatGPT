import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site-packages'))
from .asker import askChatGPT, createAskMeaningPrompt
import markdown2
from .asker import startThreadOfRequesting
from .promptOption import EnumPromptOption
from .myLog import mylog
from .promptOption import EnumPromptOption
from .dialogs import TextBox
import gui
import wx
import config
from scriptHandler import script
import globalPluginHandler
from revChatGPT.V3 import Chatbot
import treeInterceptorHandler
import ui
import textInfos
import api
import threading
from openai.error import RateLimitError, AuthenticationError
from openai.error import ServiceUnavailableError
import queueHandler

module = "askChatGPT"


def initConfiguration():
    confspec = {
        "apiKey": "string( default='')",
        "outputLanguageIndex": "integer( default=1, min=0, max=8)",
    }
    config.conf.spec[module] = confspec


def getConfig(key):
    value = config.conf[module][key]
    return value


def setConfig(key, value):
    config.conf[module][key] = value


initConfiguration()


class OptionsPanel(gui.SettingsPanel):
    title = _("askChatGPT")
    languages = [
        _("Chinese"),
        _("English"),
        _("Italian"),
        _("Japanese"),
        _("Korean"),
        _("Portuguese"),
        _("Spanish"),
        _("Turkish"),
    ]

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

        self.apiKey = sHelper.addLabeledControl(
            _("chatGPT api key:"), wx.TextCtrl)
        self.apiKey.Value = getConfig("apiKey")

        label = _("Output language of a meaning of wordsf :")
        self.outputLanguage = sHelper.addLabeledControl(
            label, wx.Choice, choices=self.languages)
        self.outputLanguage.Selection = getConfig(
            "outputLanguageIndex")

        label = _("Open text box, when nothing is selected.")

    def onSave(self):
        setConfig("apiKey", self.apiKey.Value)
        setConfig("outputLanguageIndex", self.outputLanguage.Selection)


# this way, it can get selected text from anywhere


def get_selected_text():
    obj = api.getFocusObject()
    treeInterceptor = obj.treeInterceptor
    if isinstance(treeInterceptor, treeInterceptorHandler.DocumentTreeInterceptor):
        obj = treeInterceptor

    try:
        info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
    except (RuntimeError, NotImplementedError):
        return ""

    return info.text.strip()


def isSelectedTextEmpty(selectedText):
    if len(selectedText) == 0:

        return True
    else:
        return False


def isApiKeyEmpty():

    apiKey = getConfig("apiKey")
    if len(apiKey) == 0:
        ui.message("Set an api key first.")
        return True

    return False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(
            OptionsPanel)

    def terminate(self):
        super(GlobalPlugin, self).terminate()
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
            OptionsPanel)

    @script(
        category=_("Ask chatGPT"),
        description=_("Ask the meaning of a word to chatGPT"),
        gestures=["kb:NVDA+shift+w"]
    )
    def script_askMeaningOfWord(self, gesture):
        if isApiKeyEmpty():
            return
        selectedText = get_selected_text()

        if isSelectedTextEmpty(selectedText):
            gui.mainFrame.prePopup()
            textBoxInstance = TextBox(EnumPromptOption.ASKMEANINGOF)
            textBoxInstance.Show()
            # Raise put focus on the window, when it is already open, but lost focus.
            textBoxInstance.Raise()
            gui.mainFrame.postPopup()
            return

        startThreadOfRequesting(EnumPromptOption.ASKMEANINGOF, selectedText)

    @script(
        category=_("Ask chatGPT"),
        description=_("Ask the sentence to chatGPT"),
        gestures=["kb:NVDA+shift+l"]
    )
    def script_askSentence(self, gesture):
        if isApiKeyEmpty():
            return

        gui.mainFrame.prePopup()
        textBoxInstance = TextBox(EnumPromptOption.ASKSENTENCE)
        textBoxInstance.Show()
        textBoxInstance.Raise()
        gui.mainFrame.postPopup()
