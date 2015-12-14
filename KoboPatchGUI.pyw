#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
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
import io
import os
import sys
import re
import copy

def iterDic(dic):
    """
    Return a python 2/3 compatible iterable
    :param dic:
    :param pythonTwo:
    :return:
    """
    if sys.version_info.major == 2:
        return dic.viewitems()
    else:
        return dic.items()

class KoboPatch:
    def __init__(self, name, status, group, patch_file):
        self.name = name
        self.status = status
        self.help_text = ''
        self.group = group
        self.patch_file = patch_file
        self.patch_replacements = []

    def get_patch_replacements(self, data):
        start = 0
        find = re.compile(r'^#{0,1}replace_.+?$')
        for (index, line) in enumerate(data):
            if 'patch_name = '+self.name in line:
                start = index
                break
        for line in data[start:]:
            if '</Patch>' in line:
                break
            m = find.search(line)
            if m:
                self.patch_replacements.append(m.group())

    def get_help_text(self, text):
        search_str = r'<Patch>(\npatch_name = ' + re.escape(self.name) + r'.+?)</Patch>'
        search_str = search_str.replace('\\`', '`')

        re_match_help_txt = re.search(search_str, text, flags=re.DOTALL | re.UNICODE)
        help_t = re_match_help_txt.group(1)
        self.help_text = help_t


class PatchGUI(Tk):
    def __init__(self, parent):
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

        fn_list = askopenfilenames(filetypes=[('Patch Files', '*.patch')], parent=self.parent)
        if fn_list:
            fd = {fn: None for fn in fn_list}
            self.file_dic = self.read_patch_files(fd)
            for (fn, patch_text) in iterDic(self.file_dic):
                self.orig_patch_obj_dic[fn] = self.gen_patch_obj_list(fn, patch_text)
            self.init_completed = True
            self.initialize()
        else:
            self.init_completed = False

    def initialize(self):
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        cont_index = 0
        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            self.cb_dic[fn] = []
            self.container.append(ttk.LabelFrame(self.parent, text=fn))
            self.container[cont_index].pack(fill='x')

            for (cb_index, obj) in enumerate(patch_obj_list):
                var = StringVar()
                cb_name = ''
                if obj.group:
                    cb_name = obj.name + '\n(' + obj.group + ')'
                else:
                    cb_name = obj.name
                self.cb_dic[fn].append(ttk.Checkbutton(self.container[cont_index], text=cb_name,
                                                              variable=var, onvalue='yes', offvalue='no',
                                                              command=lambda fn=fn, p=cb_index, patch_obj=obj:
                                                              self.toggle_check(fn, p, patch_obj)))
                self.cb_dic[fn][cb_index].var = var
                if 'yes' in obj.status:
                    self.cb_dic[fn][cb_index].var.set('yes')
                else:
                    self.cb_dic[fn][cb_index].var.set('no')
                grid_pos = self.calc_grid_pos(cb_index, cols=3)
                self.cb_dic[fn][cb_index].grid(row=grid_pos[0], column=grid_pos[1], sticky='W')
                self.cb_dic[fn][cb_index].columnconfigure(0, weight=1)
                self.cb_dic[fn][cb_index].columnconfigure(1, weight=1)
                self.cb_dic[fn][cb_index].columnconfigure(2, weight=1)

                self.cb_dic[fn][cb_index].bind('<Button-3>', lambda event, fn=fn, p=cb_index, patch_obj=obj:
                                                        self.edit_repl_opts(event, fn, p, patch_obj))

                tip = ToolTip(self.cb_dic[fn][cb_index], obj.help_text)

            cont_index += 1

        self.container.append(ttk.Frame(self.parent))
        self.container[-1].pack(pady=5)
        self.apply_button = ttk.Button(self.container[-1], text='Apply Changes', command=self.apply_changes)
        self.disable_all_button = ttk.Button(self.container[-1], text='Disable all', command=self.disable_all_patches)
        self.defaults_button = ttk.Button(self.container[-1], text='Restore Defaults', command=self.restore_defaults)
        self.apply_button.grid(row=0, column=0, padx=5)
        self.disable_all_button.grid(row=0, column=1, padx=5)
        self.defaults_button.grid(row=0, column=2, padx=5)


    def disable_all_patches(self):
        for chk_list in self.cb_dic.values():
            for cb in chk_list:
                cb.var.set('no')

        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            for patch_obj in patch_obj_list:
                patch_obj.status = '`no`'

    def restore_defaults(self):
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        for (cb_list, patch_obj_list) in zip(self.cb_dic.values(), self.patch_obj_dic.values()):
            for (cb, patch_obj) in zip(cb_list, patch_obj_list):
                if 'yes' in patch_obj.status:
                     cb.var.set('yes')
                else:
                     cb.var.set('no')

    def edit_repl_opts(self, event, ext_pos, pos, patch_obj):
        pass

    def toggle_check(self, fn, pos, patch_obj):
        if 'yes' in self.cb_dic[fn][pos].var.get():
            patch_obj.status = '`yes`'
        else:
            patch_obj.status = '`no`'

    def apply_changes(self):
        if messagebox.askyesno('Are you sure?', 'Do you wish to write the changes to file?\n\nNote this will '
                                                 'overwrite the exiting patch file(s)'):
            for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
                mut_exl_dic = {}
                for obj in patch_obj_list:
                    if obj.group and 'yes' in obj.status:
                        if obj.group not in mut_exl_dic:
                            mut_exl_dic[obj.group] = []
                            mut_exl_dic[obj.group].append(obj.name)
                        else:
                            mut_exl_dic[obj.group].append(obj.name)

                for (group, names) in iterDic(mut_exl_dic):
                    if len(names) > 1:
                        name_str = '\n'
                        for name in names:
                            name_str += '    ' + name + '\n'
                        messagebox.showerror('Mutually Exlusive Options Detected!',
                                             'The following options cannot be enabled together: \n' + name_str)
                        return

                for obj in patch_obj_list:
                    self.prep_for_writing(fn, obj)

                    self.write_patch_files(fn)

    def prep_for_writing(self, patch_fn, patch_object):
        search_pattern = r'(patch_name = ' + re.escape(patch_object.name) + r'.+?patch_enable = )' + \
                         r'`.+?`'
        search_pattern = search_pattern.replace('\\`', '`')
        search_replace = r'\1' + patch_object.status
        s = re.sub(search_pattern, search_replace, self.file_dic[patch_fn], flags=re.DOTALL | re.UNICODE)
        self.file_dic[patch_fn] = s
        print(self.file_dic[patch_fn])

    def calc_grid_pos(self, pos, cols):
        calc_row = pos // cols
        calc_col = pos % cols

        return calc_row, calc_col

    def write_patch_files(self, fn):
        try:
            with io.open(os.path.normpath(fn), 'w', encoding='utf8') as patch_file:
                patch_file.write(self.file_dic[fn])
        except EnvironmentError:
            messagebox.showerror('File Error!', 'There was a problem writing to the file.\n\nCheck that the file '
                                                'isn\'t in use by another program, and that you have write '
                                                'permissions to the file and folder')

    def read_patch_files(self, fn_dic):
        for fn in fn_dic:
            try:
                with io.open(os.path.normpath(fn), 'r', encoding='utf8') as patch_file:
                    fn_dic[fn] = ''
                    for line in patch_file:
                        fn_dic[fn] += line
            except EnvironmentError:
                messagebox.showerror('Read Error', 'There was a problem reading the file.\n\nCheck that you have '
                                                   'permission to read the file.')
        return fn_dic

    def gen_patch_obj_list(self, fn, patch_text):
        patch_obj_list = []
        search_pattern = r'patch_name = (`.+?`).+?patch_enable = (`.+?`)(.+?patch_group = (`.+?`))?'
        re_find_attrib = re.compile(search_pattern, flags=re.DOTALL | re.UNICODE)
        attrib_match_list = re_find_attrib.finditer(patch_text)

        for match in attrib_match_list:
            mut_ex_group = ''
            if match.group(4):
                mut_ex_group = match.group(4)

            patch_obj = KoboPatch(name=match.group(1), status=match.group(2), group=mut_ex_group, patch_file=fn)
            patch_obj.get_help_text(patch_text)
            patch_obj_list.append(patch_obj)

        return patch_obj_list

def quit(root):
    root.destroy()

def main():
    app = PatchGUI(None)
    if app.init_completed:
        app.title('Kobo Patch GUI')
        app.mainloop()
    else:
        app.quit()

if __name__ == '__main__':
    main()