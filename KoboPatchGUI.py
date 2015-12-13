from __future__ import absolute_import, division, print_function, unicode_literals
try:
    #from tkinter import *
    from tkinter import ttk
    from tkinter.filedialog import askopenfilenames
except (ImportError):
    import ttk
    from tkFileDialog import askopenfilenames

from ToolTip import *
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
        for (pos, line) in enumerate(data):
            if 'patch_name = '+self.name in line:
                start = pos
                break
        for line in data[start:]:
            if '</Patch>' in line:
                break
            m = find.search(line)
            if m:
                self.patch_replacements.append(m.group())

    def get_help_text(self, text):
        search_str = r'<Patch>(.+?patch_name = ' + re.escape(self.name) + r'.+?)</Patch>'
        re_match_help_txt = re.compile(search_str, re.DOTALL)
        s = re_match_help_txt.search(text)
        self.help_text = s.group(1)

class PatchGUI(Tk):
    def __init__(self, parent):
        Tk.__init__(self, parent)
        self.parent = parent
        self.file_dic = {}
        self.orig_patch_obj_dic = {}
        self.patch_obj_dic = {}
        self.cb_list = []
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
        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            self.cb_list.append([])
            ext_pos = -1
            self.container.append(ttk.LabelFrame(self.parent, text=fn))
            self.container[ext_pos].pack(fill='x')

            for (pos, obj) in enumerate(patch_obj_list):
                var = StringVar()
                cb_name = ''
                if obj.group:
                    cb_name = obj.name + '\n(' + obj.group + ')'
                else:
                    cb_name = obj.name
                self.cb_list[ext_pos].append(ttk.Checkbutton(self.container[ext_pos], text=cb_name,
                                                         variable=var, onvalue='yes', offvalue='no',
                                                         command=lambda ep=ext_pos, p=pos, patch_obj=obj:
                                                         self.toggle_check(ep, p, patch_obj)))
                self.cb_list[ext_pos][pos].var = var
                if 'yes' in obj.status:
                    self.cb_list[ext_pos][pos].var.set('yes')
                else:
                    self.cb_list[ext_pos][pos].var.set('no')
                grid_pos = self.calc_grid_pos(pos, cols=3)
                self.cb_list[ext_pos][pos].grid(row=grid_pos[0], column=grid_pos[1], sticky='W')
                self.cb_list[ext_pos][pos].columnconfigure(0, weight=1)
                self.cb_list[ext_pos][pos].columnconfigure(1, weight=1)
                self.cb_list[ext_pos][pos].columnconfigure(2, weight=1)

                self.cb_list[ext_pos][pos].bind('<Button-3>', lambda event, ep=ext_pos, p=pos, patch_obj=obj:
                                                        self.edit_repl_opts(event, ep, p, patch_obj))

                tip = ToolTip(self.cb_list[ext_pos][pos], obj.help_text)

        self.container.append(ttk.Frame(self.parent))
        self.container[-1].pack(pady=5)
        self.apply_button = ttk.Button(self.container[-1], text='Apply Changes', command=self.apply_changes)
        self.disable_all_button = ttk.Button(self.container[-1], text='Disable all', command=self.disable_all_patches)
        self.defaults_button = ttk.Button(self.container[-1], text='Restore Defaults', command=self.restore_defaults)
        self.apply_button.grid(row=0, column=0, padx=5)
        self.disable_all_button.grid(row=0, column=1, padx=5)
        self.defaults_button.grid(row=0, column=2, padx=5)


    def disable_all_patches(self):
        for chk_list in self.cb_list:
            for cb in chk_list:
                cb.var.set('no')

        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            for patch_obj in patch_obj_list:
                patch_obj.status = '`no`'

    def restore_defaults(self):
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        for (cb_list, patch_obj_list) in zip(self.cb_list, self.patch_obj_dic.values()):
            for (cb, patch_obj) in zip(cb_list, patch_obj_list):
                if 'yes' in patch_obj.status:
                     cb.var.set('yes')
                else:
                     cb.var.set('no')

    def edit_repl_opts(self, event, ext_pos, pos, patch_obj):
        pass

    def toggle_check(self, ext_pos, pos, patch_obj):
        if 'yes' in self.cb_list[ext_pos][pos].var.get():
            patch_obj.status = '`yes`'
        else:
            patch_obj.status = '`no`'

    def apply_changes(self):
        pass


    def calc_grid_pos(self, pos, cols):
        calc_row = pos // cols
        calc_col = pos % cols

        return calc_row, calc_col


    def read_patch_files(self, fn_dic):
        for fn in fn_dic:
            with io.open(os.path.normpath(fn), 'r', encoding='utf8') as patch_file:
                #fn_dic[fn] = patch_file.readlines()
                fn_dic[fn] = ''
                for line in patch_file:
                    fn_dic[fn] += line
        return fn_dic

    def gen_patch_obj_list(self, fn, patch_text):
        patch_obj_list = []
        re_find_attrib = re.compile(r'patch_name = (`.+?`).+?patch_enable = (`.+?`)(.+?patch_group = (`.+?`))?', re.DOTALL)
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