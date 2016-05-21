import re

try:
    from Tkinter import *  # noqa
    from tkMessageBox import showinfo, showerror
except:
    from tkinter import *  # noqa
    from tkinter.messagebox import showinfo, showerror

import mudclientproto as mcp
from mcpgui.wizard import Wizard
from mcpgui.notebook import NoteBook


class McpFuzzballNotifyPkg(mcp.McpPackage):
    def __init__(self):
        mcp.McpPackage.__init__(self, 'org-fuzzball-notify', '1.0', '1.1')

    def process_message(self, msg):
        if self.connection.is_server:
            self.process_message_server(msg)
        else:
            self.process_message_client(msg)

    def process_message_client(self, msg):
        pass

    def process_message_server(self, msg):
        if msg.name == 'org-fuzzball-notify-info':
            topic = msg['topic']
            text = msg['text']
            showinfo(topic, text)
        elif msg.name == 'org-fuzzball-notify-warning':
            topic = msg['topic']
            text = msg['text']
            showwarning(topic, text)
        elif msg.name == 'org-fuzzball-notify-error':
            topic = msg['topic']
            text = msg['text']
            showerror(topic, text)


class McpFuzzballGuiPkg(mcp.McpPackage):
    def __init__(self):
        self.dlogs = {}
        mcp.McpPackage.__init__(self, 'org-fuzzball-gui', '1.0', '1.3')
        self.client_handlers = {
            'org-fuzzball-gui-dlog-create':    self.dlog_create,
            'org-fuzzball-gui-dlog-show':      self.dlog_show,
            'org-fuzzball-gui-dlog-close':     self.dlog_close,

            'org-fuzzball-gui-error':          self.error,

            'org-fuzzball-gui-ctrl-command':   self.ctrl_command,
            'org-fuzzball-gui-ctrl-value':     self.ctrl_value,

            'org-fuzzball-gui-ctrl-frame':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-datum':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-hrule':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-vrule':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-text':      self.ctrl_create,
            'org-fuzzball-gui-ctrl-image':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-button':    self.ctrl_create,
            'org-fuzzball-gui-ctrl-checkbox':  self.ctrl_create,
            'org-fuzzball-gui-ctrl-radio':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-edit':      self.ctrl_create,
            'org-fuzzball-gui-ctrl-password':  self.ctrl_create,
            'org-fuzzball-gui-ctrl-spinner':   self.ctrl_create,
            'org-fuzzball-gui-ctrl-scale':     self.ctrl_create,
            'org-fuzzball-gui-ctrl-combobox':  self.ctrl_create,
            'org-fuzzball-gui-ctrl-multiedit': self.ctrl_create,
            'org-fuzzball-gui-ctrl-listbox':   self.ctrl_create,
            'org-fuzzball-gui-ctrl-notebook':  self.ctrl_create,
            'org-fuzzball-gui-ctrl-tree':      self.ctrl_create,
            'org-fuzzball-gui-ctrl-menu':      self.ctrl_create,
        }

    def process_message(self, msg):
        if self.connection.is_server:
            return
        if msg.name not in self.client_handlers:
            return
        hndlr = self.client_handlers[msg.name]
        hndlr(msg)

    def _verify_existing_dlog(self, dlogid):
        if dlogid in self.dlogs:
            return True
        self.send_error(
            dlogid, '', 'ENODLOG',
            "No dialog exists with that dialog id."
        )
        return False

    def _get_dlog(self, msg):
        dlogid = msg.get('dlogid', '')
        if not self._verify_existing_dlog(dlogid):
            return None
        return self.dlogs[dlogid]

    def dlog_create(self, msg):
        dlogid = msg.get('dlogid', '')
        if not re.match(r'^[A-Z0-9_]+$', dlogid, re.I):
            self.send_error(
                dlogid, '', 'EBADDLOGID',
                "The given dialog id contains illegal characters."
            )
            return
        self.dlogs[dlogid] = McpGuiDialog(self, msg)

    def dlog_show(self, msg):
        dlog = self._get_dlog(msg)
        if not dlog:
            return
        dlog.deiconify()

    def dlog_close(self, msg):
        dlog = self._get_dlog(msg)
        if not dlog:
            return
        dlog.destroy()
        del self.dlogs[dlog.dlogid]

    def error(self, msg):
        dlogid = msg.get('dlogid', '')
        ctrlid = msg.get('ctrlid', '')
        errcode = msg.get('errcode', '')
        errtext = msg.get('errtext', '')
        showerror(
            "MCP GUI Error",
            (
                "Dialog ID: %s\n"
                "Control ID: %s\n"
                "ErrorCode: %s\n"
                "%s"
            ) % (
                dlogid,
                ctrlid,
                errcode,
                errtext
            ),
        )

    def ctrl_command(self, msg):
        dlog = self._get_dlog(msg)
        if not dlog:
            return
        dlog.ctrl_command(msg)

    def ctrl_value(self, msg):
        dlog = self._get_dlog(msg)
        if not dlog:
            return
        dlog.ctrl_value(msg)

    def ctrl_create(self, msg):
        dlog = self._get_dlog(msg)
        if not dlog:
            return
        pfx = 'org-fuzzball-gui-ctrl-'
        ctrl_type = msg.name[len(pfx):]
        if ctrl_type not in self.control_classes:
            return
        dlog.ctrl_create(ctrl_type, msg)

    def send_event(self, dlogid, ctrlid, event, dismissed, data=''):
        msg = McpMessage(
            'org-fuzzball-gui-ctrl-event',
            dlogid=dlogid,
            id=ctrlid,
            dismissed=dismissed,
            event=event,
            data=data,
        )
        self.connection.send_message(msg)

    def send_error(self, dlogid, ctrlid, errcode, errtext):
        msg = McpMessage(
            'org-fuzzball-gui-error',
            dlogid=dlogid,
            id=ctrlid,
            errcode=errcode,
            errtext=errtext,
        )
        self.connection.send_message(msg)


class McpGuiControl(object):
    def __init__(self, typ, dlog, pane, msg):
        self.ctrl_type = typ
        self.dlog = dlog
        self.ctrlid = msg.get('id')
        self.value = msg.get('value', '')
        self.valname = msg.get('valname', self.ctrlid)
        self.row = msg.get('row', -1, int)
        self.column = msg.get('column', -1, int)
        self.newline = msg.get('newline', True, bool)
        self.colskip = msg.get('colskip', 0, int)
        self.colspan = msg.get('colspan', 1, int)
        self.rowspan = msg.get('rowspan', 1, int)
        self.sticky = msg.get('sticky', 'w', str).lower()
        self.sticky = ''.join(set(self.sticky) & set("nsew"))
        self.minwidth = msg.get('minwidth', 0, int)
        self.minheight = msg.get('minheight', 0, int)
        self.hweight = msg.get('hweight', 0, int)
        self.vweight = msg.get('vweight', 0, int)
        self.leftpad = msg.get('leftpad', 10, int)
        self.toppad = msg.get('toppad', 10, int)
        self.sort = msg.get('sorted', False, bool)
        self.pane = pane
        self.ctrl = None

    def send_event(self, event, dismissed, data=''):
        self.dlog.send_event(self.ctrlid, event, dismissed, data)

    def send_error(self, errcode, errtext):
        self.dlog.send_error(self.ctrlid, errcode, errtext)

    def set_value(self, val):
        self.value = val

    def get_value(self):
        return self.value

    def command(self, msg):
        self.send_error(
            'ECTRLCMDNOTSUPP',
            "The given control-command is not recognized."
        )


class McpGuiCtrlFrame(McpGuiControl):
    def __init__(self, dlog, pane, msg):
        self.visible = msg.get('visible', False, bool)
        self.collapsible = msg.get('collapsible', False, bool)
        self.collapsed = msg.get('collapsed', False, bool)
        opts = {
            k: v for k, v in msg.items()
            if v and k in ['text', 'relief', 'width', 'height']
        }
        if self.visible:
            opts['borderwidth'] = 2
        else:
            opts['borderwidth'] = 0
            opts['relief'] = FLAT
            if 'text' in opts:
                del opts['text']
        if 'text' in opts:
            self.ctrl = LabelFrame(pane, **opts)
        else:
            self.ctrl = Frame(pane, **opts)
        self.holder = Frame(self.ctrl, borderwidth=0)
        if not self.collapsible or not self.collapsed:
            self.holder.pack(side=TOP, fill=BOTH, expand=1)
        if self.collapsible:
            self.bind('<1>', self._toggle)
        dlog.panes[self.ctrlid] = self.holder
        McpGuiControl.__init__('datum', self, dlog, pane, msg)

    def _toggle(self):
        self.collapsed = not self.collapsed
        if not self.collapsible:
            self.collapsed = False
        if self.collapsed:
            for child in self.winfo_children():
                child.forget()
        else:
            self.holder.pack(side=TOP, fill=BOTH, expand=1)

    def config(self, **kwargs):
        pass


class McpGuiCtrlDatum(McpGuiControl):
    def __init__(self, dlog, pane, msg):
        McpGuiControl.__init__('datum', self, dlog, pane, msg)


class McpGuiCtrlHRule(McpGuiControl):
    def __init__(self, dlog, pane, msg):
        self.ctrl = Frame(
            pane.ctrl,
            height=msg.get('height', 2),
        )
        self.sticky = ''.join(set(self.sticky+'ew'))
        McpGuiControl.__init__('hrule', self, dlog, pane, msg)


class McpGuiCtrlVRule(McpGuiControl):
    def __init__(self, dlog, pane, msg):
        self.ctrl = Frame(
            self.pane.ctrl,
            width=msg.get('width', 2),
        )
        self.sticky = ''.join(set(self.sticky+'ns'))
        McpGuiControl.__init__('vrule', self, dlog, pane, msg)


class McpGuiCtrlText(McpGuiControl):
    pass


class McpGuiCtrlImage(McpGuiControl):
    pass


class McpGuiCtrlButton(McpGuiControl):
    pass


class McpGuiCtrlCheckBox(McpGuiControl):
    pass


class McpGuiCtrlRadio(McpGuiControl):
    pass


class McpGuiCtrlEdit(McpGuiControl):
    pass


class McpGuiCtrlPassWord(McpGuiControl):
    pass


class McpGuiCtrlSpinner(McpGuiControl):
    pass


class McpGuiCtrlScale(McpGuiControl):
    pass


class McpGuiCtrlComboBox(McpGuiControl):
    pass


class McpGuiCtrlMultiEdit(McpGuiControl):
    pass


class McpGuiCtrlListBox(McpGuiControl):
    pass


class McpGuiCtrlNoteBook(McpGuiControl):
    pass


class McpGuiCtrlTree(McpGuiControl):
    pass


class McpGuiCtrlMenu(McpGuiControl):
    pass


class McpGuiDialog(TopLevel):
    def __init__(self, pkg, msg):
        self.pkg = pkg
        self.currpane = self
        self.dlogid = msg.get('dlogid')
        self.title = msg.get('title')
        self.dlogtype = msg.get('type')
        self.resize = msg.get('resizable', '').lower()
        self.minwidth = int(msg.get('minwidth', '30'))
        self.minheight = int(msg.get('minheight', '30'))
        self.width = int(msg.get('width', '300'))
        self.height = int(msg.get('height', '200'))
        self.maxwidth = int(msg.get('maxwidth', '0'))
        self.maxheight = int(msg.get('maxheight', '0'))
        if not self.maxwidth:
            self.maxwidth = self.winfo_screenwidth()
        if not self.maxheight:
            self.maxheight = self.winfo_screenheight()
        Toplevel.__init__(self, **kwargs)
        self.controls = {}

        if self.title:
            self.title(self.title)
        self.withdraw()
        xresize = 1 if resize in ["x", "xy", "both"] else 0
        yresize = 1 if resize in ["y", "xy", "both"] else 0
        self.resizable(width=xresize, height=yresize)
        self.minsize(width=self.minwidth, height=self.minheight)
        self.maxsize(width=self.maxwidth, height=self.maxheight)
        self.protocol('WM_DELETE_WINDOW', self._delete_window)
        self.control_classes = {
            'frame':     McpGuiCtrlFrame,
            'datum':     McpGuiCtrlDatum,
            'hrule':     McpGuiCtrlHRule,
            'vrule':     McpGuiCtrlVRule,
            'text':      McpGuiCtrlText,
            'image':     McpGuiCtrlImage,
            'button':    McpGuiCtrlButton,
            'checkbox':  McpGuiCtrlCheckBox,
            'radio':     McpGuiCtrlRadio,
            'edit':      McpGuiCtrlEdit,
            'password':  McpGuiCtrlPassWord,
            'spinner':   McpGuiCtrlSpinner,
            'scale':     McpGuiCtrlScale,
            'combobox':  McpGuiCtrlComboBox,
            'multiedit': McpGuiCtrlMultiEdit,
            'listbox':   McpGuiCtrlListBox,
            'notebook':  McpGuiCtrlNoteBook,
            'tree':      McpGuiCtrlTree,
            'menu':      McpGuiCtrlMenu,
        }

    def send_event(self, ctrlid, event, dismissed, data=''):
        self.pkg.send_event(self.dlogid, ctrlid, event, dismissed, data)

    def send_error(self, ctrlid, errcode, errtext):
        self.pkg.send_error(self.dlogid, ctrlid, errcode, errtext)

    def setup_tabbed_dlog(self, msg):
        panes = msg.get('panes', [])
        names = msg.get('names', [])
        self.ctrl_create(
            'notebook', dict(
                panes=panes,
                names=names,
                height=self.height,
                width=self.width
            )
        )
        self.ctrl_create(
            'frame', dict(
                id='__bframe',
                text='',
                sticky='wen',
                toppad=3
            )
        )
        self.ctrl_create(
            'frame', dict(
                id='__bfiller',
                pane='__bframe',
                newline=0,
                hweight=1
            )
        )
        self.ctrl_create(
            'button', dict(
                id='_ok',
                width=8,
                text='Okay',
                dismiss=1,
                newline=0
            )
        )
        self.ctrl_create(
            'button', dict(
                id='_cancel',
                width=8,
                text='Cancel',
                dismiss=1,
                newline=0
            )
        )
        self.ctrl_create(
            'button', dict(
                id='_apply',
                width=8,
                text='Apply',
                dismiss=0,
                newline=0
            )
        )

    def setup_helper_dlog(self, msg):
        wiz = Wizard(
            width=msg.get('width', 640, int),
            height=msg.get('height', 480, int),
            finishcommand=self._helper_finish,
            cancelcommand=self._helper_cancel,
        )
        for name, pane in zip(msg.get('names', []), msg.get('panes', [])):
            self.panes[name] = wiz.add_pane(pane, name)

    def _helper_finish(self, event=None):
        self.send_event('_finish', 'buttonpress', 1)

    def _helper_cancel(self, event=None):
        self.send_event('_cancel', 'buttonpress', 1)

    def _verify_existing_ctrl(self, ctrlid):
        if ctrlid in self.controls:
            return True
        self.send_error(
            self.dlogid, ctrlid, 'ENOCONTROL',
            "No control named '%s' exists in the given dialog." % ctrlid
        )
        return False

    def _get_ctrl(self, msg):
        ctrlid = msg.get('id', '')
        if not self._verify_existing_ctrl(dlogid):
            return None
        return self.controls[ctrlid]

    def _delete_window(self, *args):
        self.send_event('_closed', 'buttonpress', 1)

    def destroy_dlog(self):
        self.destroy()

    def ctrl_command(self, msg):
        ctrl = self._get_ctrl(msg)
        if not ctrl:
            return
        return ctrl.command(msg)

    def ctrl_value(self, msg):
        ctrl = self._get_ctrl(msg)
        if not ctrl:
            return
        return ctrl.set_value(msg.get('value', ''))

    def ctrl_create(self, ctrl_type, msg):
        ctrl_class = self.control_classes[ctrl_type]
        ctrlid = msg.get('id', '')
        if not re.match(r'^[A-Z0-9_]+$', ctrlid, re.I):
            self.send_error(
                dlogid, ctrlid, 'EBADCTRLID',
                "The given control id contains illegal characters."
            )
            return
        pane = msg.get('pane')
        if pane:
            if pane not in self.controls:
                self.send_error(
                    ctrlid, 'EPANEINVALID',
                    "The given dialog doesn't contain a pane by that id."
                )
                return
            pane = self.controls[pane]
            self.currpane = pane
        else:
            pane = self.currpane
        self.controls[ctrlid] = ctrl_class(self, pane, msg)


# vim: expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap
