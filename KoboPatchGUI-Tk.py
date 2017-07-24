#!/usr/bin/env python

# Kobo Patch GUI Copyright (c) 2015 Sherman Perry
#
# This software is provided under the MIT license. Please see LICENSE.txt for details

from __future__ import absolute_import, division, print_function, unicode_literals

from PatchEdit import *

try:
    from tkinter import *
    from tkinter import ttk
    from tkinter.filedialog import askopenfilenames
    from tkinter import messagebox
except ImportError:
    from Tkinter import *
    import ttk
    from tkFileDialog import askopenfilenames
    import tkMessageBox as messagebox

from ToolTip import *
from collections import OrderedDict
import copy


class PatchGUI(Tk):
    """
    Create the main GUI frame, widgets, and methods
    """
    def __init__(self, parent):
        """
        Sets initial GUI variable state only if one or more patch files are selected by the user.
        :param parent:
        :return:
        """
        Tk.__init__(self, parent)
        self.parent = parent
        self.file_dic = OrderedDict()
        self.orig_patch_obj_dic = OrderedDict()
        self.patch_obj_dic = OrderedDict()
        self.cb_dic = OrderedDict()
        self.container = []
        self.init_completed = False
        self.apply_button = None
        self.disable_all_button = None
        self.defaults_button = None

        # Ask user for patch file(s), and generate Patch objects for each patch detected
        fn_list = askopenfilenames(filetypes=[('Patch Files', '*.patch')], parent=self.parent)
        if fn_list:
            fd = {fn: None for fn in fn_list}
            self.file_dic, error = read_patch_files(fd)
            if error:
                messagebox.showerror('Read Error!', error)
                self.init_completed = False
            else:
                for (fn, patch_text) in iterDic(self.file_dic):
                    self.orig_patch_obj_dic[fn] = gen_patch_obj_list(fn, patch_text)
                self.init_completed = True
                self.initialize()
        else:
            self.init_completed = False

    def initialize(self):
        """
        Generate the GUI based on the patch objects present, including tooltips.
        :return:
        """
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        cont_index = 0
        # Create a LabelFrame for each patch file, which contains checkboxes
        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            self.cb_dic[fn] = []
            self.container.append(ttk.LabelFrame(self.parent, text=fn))
            self.container[cont_index].pack(fill='x')

            # Create and add checkboxes to appropriate LabelFrame
            for (cb_index, obj) in enumerate(patch_obj_list):
                # Create checkbox variable and checkbox label for display
                var = StringVar()
                cb_name = ''
                if obj.group:
                    cb_name = obj.name + '\n(' + obj.group + ')'
                else:
                    cb_name = obj.name

                # Create and add checkboxes to the LabelFrame, using the grid geometry manager
                self.cb_dic[fn].append(ttk.Checkbutton(self.container[cont_index], text=cb_name,
                                                              variable=var, onvalue='yes', offvalue='no',
                                                              command=lambda fn=fn, p=cb_index, patch_obj=obj:
                                                              self.toggle_check(fn, p, patch_obj)))
                self.cb_dic[fn][cb_index].var = var
                # Set initial state of checkboxes
                if 'yes' in obj.status:
                    self.cb_dic[fn][cb_index].var.set('yes')
                else:
                    self.cb_dic[fn][cb_index].var.set('no')
                grid_pos = calc_grid_pos(cb_index, cols=3)
                self.cb_dic[fn][cb_index].grid(row=grid_pos[0], column=grid_pos[1], sticky='W')
                self.cb_dic[fn][cb_index].columnconfigure(0, weight=1)
                self.cb_dic[fn][cb_index].columnconfigure(1, weight=1)
                self.cb_dic[fn][cb_index].columnconfigure(2, weight=1)

                # Right clicking checkboxes currently does nothing: self.edit_repl_opts() has an empty implementation
                self.cb_dic[fn][cb_index].bind('<Button-3>', lambda event, fn=fn, p=cb_index, patch_obj=obj:
                                                                    edit_repl_opts(event, fn, p, patch_obj))
                # And finally, some tooltips for help
                tip = ToolTip(self.cb_dic[fn][cb_index], obj.help_text)

            cont_index += 1

        # Some buttons may be useful...
        self.container.append(ttk.Frame(self.parent))
        self.container[-1].pack(pady=5)
        self.apply_button = ttk.Button(self.container[-1], text='Apply Changes', command=self.app_chgs)
        self.disable_all_button = ttk.Button(self.container[-1], text='Disable all', command=self.disable_all_patches)
        self.defaults_button = ttk.Button(self.container[-1], text='Restore Defaults', command=self.restore_defaults)
        self.apply_button.grid(row=0, column=0, padx=5)
        self.disable_all_button.grid(row=0, column=1, padx=5)
        self.defaults_button.grid(row=0, column=2, padx=5)


    def disable_all_patches(self):
        """
        Does what it says on the tin :p
        Deselects all checkboxes and sets each objects status to 'no'
        :return:
        """
        for chk_list in self.cb_dic.values():
            for cb in chk_list:
                cb.var.set('no')

        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            for patch_obj in patch_obj_list:
                patch_obj.status = '`no`'

    def restore_defaults(self):
        """
        Restores the state of the patch objects and checkboxes back to their original state of when the file was loaded
        :return:
        """
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        for (cb_list, patch_obj_list) in zip(self.cb_dic.values(), self.patch_obj_dic.values()):
            for (cb, patch_obj) in zip(cb_list, patch_obj_list):
                if 'yes' in patch_obj.status:
                     cb.var.set('yes')
                else:
                     cb.var.set('no')

    def toggle_check(self, fn, pos, patch_obj):
        """
        Sets the patch object status when a checkbox is clicked
        :param fn:
        :param pos:
        :param patch_obj:
        :return:
        """
        if 'yes' in self.cb_dic[fn][pos].var.get():
            patch_obj.status = '`yes`'
        else:
            patch_obj.status = '`no`'

    def app_chgs(self):
        if messagebox.askyesno('Are you sure?', 'Are you sure you wish to apply changes?'):
            success, error_title, error_msg = apply_changes(self.patch_obj_dic, self.file_dic)
            if not success:
                messagebox.showerror(error_title, error_msg)
            else:
                messagebox.showinfo('Sussess!', 'The files were successfully written.')

    def quit(self):
        self.destroy()

def main():
    app = PatchGUI(None)
    if app.init_completed:
        app.title('Kobo Patch GUI')
        app.mainloop()
    else:
        app.quit()

if __name__ == '__main__':
    main()