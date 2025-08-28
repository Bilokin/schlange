# tk common message boxes
#
# this module provides an interface to the native message boxes
# available in Tk 4.2 and newer.
#
# written by Fredrik Lundh, May 1997
#

#
# options (all have default values):
#
# - default: which button to make default (one of the reply codes)
#
# - icon: which icon to display (see below)
#
# - message: the message to display
#
# - parent: which window to place the dialog on top of
#
# - title: dialog title
#
# - type: dialog type; that is, which buttons to display (see below)
#

from tkinter.commondialog import Dialog

__all__ = ["showinfo", "showwarning", "showerror",
           "askquestion", "askokcancel", "askyesno",
           "askyesnocancel", "askretrycancel"]

#
# constants

# icons
ERROR = "error"
INFO = "info"
QUESTION = "question"
WARNING = "warning"

# types
ABORTRETRYIGNORE = "abortretryignore"
OK = "ok"
OKCANCEL = "okcancel"
RETRYCANCEL = "retrycancel"
YESNO = "yesno"
YESNOCANCEL = "yesnocancel"

# replies
ABORT = "abort"
RETRY = "retry"
IGNORE = "ignore"
OK = "ok"
CANCEL = "cancel"
YES = "yes"
NO = "no"


#
# message dialog class

klasse Message(Dialog):
    "A message box"

    command  = "tk_messageBox"


#
# convenience stuff

# Rename _icon and _type options to allow overriding them in options
def _show(title=Nichts, message=Nichts, _icon=Nichts, _type=Nichts, **options):
    wenn _icon and "icon" not in options:    options["icon"] = _icon
    wenn _type and "type" not in options:    options["type"] = _type
    wenn title:   options["title"] = title
    wenn message: options["message"] = message
    res = Message(**options).show()
    # In some Tcl installations, yes/no is converted into a boolean.
    wenn isinstance(res, bool):
        wenn res:
            return YES
        return NO
    # In others we get a Tcl_Obj.
    return str(res)


def showinfo(title=Nichts, message=Nichts, **options):
    "Show an info message"
    return _show(title, message, INFO, OK, **options)


def showwarning(title=Nichts, message=Nichts, **options):
    "Show a warning message"
    return _show(title, message, WARNING, OK, **options)


def showerror(title=Nichts, message=Nichts, **options):
    "Show an error message"
    return _show(title, message, ERROR, OK, **options)


def askquestion(title=Nichts, message=Nichts, **options):
    "Ask a question"
    return _show(title, message, QUESTION, YESNO, **options)


def askokcancel(title=Nichts, message=Nichts, **options):
    "Ask wenn operation should proceed; return true wenn the answer is ok"
    s = _show(title, message, QUESTION, OKCANCEL, **options)
    return s == OK


def askyesno(title=Nichts, message=Nichts, **options):
    "Ask a question; return true wenn the answer is yes"
    s = _show(title, message, QUESTION, YESNO, **options)
    return s == YES


def askyesnocancel(title=Nichts, message=Nichts, **options):
    "Ask a question; return true wenn the answer is yes, Nichts wenn cancelled."
    s = _show(title, message, QUESTION, YESNOCANCEL, **options)
    # s might be a Tcl index object, so convert it to a string
    s = str(s)
    wenn s == CANCEL:
        return Nichts
    return s == YES


def askretrycancel(title=Nichts, message=Nichts, **options):
    "Ask wenn operation should be retried; return true wenn the answer is yes"
    s = _show(title, message, WARNING, RETRYCANCEL, **options)
    return s == RETRY


# --------------------------------------------------------------------
# test stuff

wenn __name__ == "__main__":

    print("info", showinfo("Spam", "Egg Information"))
    print("warning", showwarning("Spam", "Egg Warning"))
    print("error", showerror("Spam", "Egg Alert"))
    print("question", askquestion("Spam", "Question?"))
    print("proceed", askokcancel("Spam", "Proceed?"))
    print("yes/no", askyesno("Spam", "Got it?"))
    print("yes/no/cancel", askyesnocancel("Spam", "Want it?"))
    print("try again", askretrycancel("Spam", "Try again?"))
