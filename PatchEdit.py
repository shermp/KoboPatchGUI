import re
import io, os, sys

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

class Patch:
    """
    Create an object that contains information about each individual patch
    """
    def __init__(self, name, status, group, patch_file):
        self.name = name
        self.status = status
        self.help_text = ''
        self.group = group
        self.patch_file = patch_file
        self.patch_replacements = []

    def get_patch_replacements(self, data):
        """
        Generate a list of possible strings for replacement. Using the data generated here has not yet been
        implemented, and may never be implemented.
        :param data:
        :return:
        """
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
        """
        From the text in the patch file, search for appropriate text to be used for help on what the patch does.
        :param text:
        :return:
        """
        search_str = r'<Patch>(\npatch_name = ' + re.escape(self.name) + r'.+?)</Patch>'
        search_str = search_str.replace('\\`', '`')

        re_match_help_txt = re.search(search_str, text, flags=re.DOTALL | re.UNICODE)
        help_t = re_match_help_txt.group(1)
        self.help_text = help_t


def gen_patch_obj_list(fn, patch_text):
    """
    From the text in the patch files, generate patch objects and store them in a list
    :param fn:
    :param patch_text:
    :return:
    """
    patch_obj_list = []
    search_pattern = r'<Patch>.+?patch_name = (`[^`]+`).+?patch_enable = (`[^`]+`).+?</Patch>'
    re_find_attrib = re.compile(search_pattern, flags=re.DOTALL | re.UNICODE)
    attrib_match_list = re_find_attrib.finditer(patch_text)

    for match in attrib_match_list:
        mut_ex_group = ''
        group_pattern = r'patch_group = (`[^`]+`)'
        group_match = re.search(group_pattern, match.group(0), flags=re.DOTALL | re.UNICODE)
        if group_match:
            mut_ex_group = group_match.group(1)
        patch_obj = Patch(name=match.group(1), status=match.group(2), group=mut_ex_group, patch_file=fn)
        patch_obj.get_help_text(patch_text)
        patch_obj_list.append(patch_obj)

    return patch_obj_list

def read_patch_files(fn_dic):
    """
    Read the patch files into a dictionary
    :param fn_dic:
    :return:
    """
    error_msg = None
    for fn in fn_dic:
        try:
            with io.open(os.path.normpath(fn), 'r', encoding='utf8') as patch_file:
                fn_dic[fn] = ''
                for line in patch_file:
                    fn_dic[fn] += line
        except EnvironmentError:
            error_msg = 'There was a problem reading the file.\n\nCheck that you have permission to read the file.'

    return fn_dic, error_msg

def apply_changes(patch_obj_dic, file_dic):
    """
    If all checks are passed, write the changes to the patch file. Note that the original file is overwritten
    :return:
    """
    success = False
    error_title = None
    error_msg = None
    # Checks that mutually exclusive options have not been set together. If they have, alert the user,
    # and abort before writing to file(s)
    for (fn, patch_obj_list) in iterDic(patch_obj_dic):
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
                error_title = 'Mutually Exlusive Options Detected!'
                error_msg = 'The following options cannot be enabled together: \n' + name_str + \
                            fn + ' was not written.'
                success = False
                return success, error_title, error_msg

    # If checks passed, prepare and then write data to file(s)
    for (fn, patch_obj_list) in iterDic(patch_obj_dic):
        for obj in patch_obj_list:
            file_dic = prep_for_writing(fn, obj, file_dic)

        r_p_f_success, error_title, error_msg = write_patch_files(fn, file_dic)
        if not r_p_f_success:
            success = False
        else:
            success = True

    return success, error_title, error_msg


def prep_for_writing(patch_fn, patch_object, file_dic):
    """
    Using regex, search and replace the patch enabled/disabled status in the patch text.
    :param patch_fn:
    :param patch_object:
    :return:
    """
    search_pattern = r'(patch_name = ' + re.escape(patch_object.name) + r'.+?patch_enable = )' + \
                     r'`.+?`'
    search_pattern = search_pattern.replace('\\`', '`')
    search_replace = r'\1' + patch_object.status
    s = re.sub(search_pattern, search_replace, file_dic[patch_fn], flags=re.DOTALL | re.UNICODE)
    file_dic[patch_fn] = s
    return file_dic


def write_patch_files(fn, file_dic):
    """
    Write the changes to file(s)
    :param fn:
    :return:
    """
    succsess = False
    error_title = None
    error_msg = None
    try:
        with io.open(os.path.normpath(fn), 'w', encoding='utf8') as patch_file:
            patch_file.write(file_dic[fn])
            succsess = True
        return succsess, error_title, error_msg
    except EnvironmentError:
        error_title = 'File Error!'
        error_msg = 'There was a problem writing to the following file:\n\n' + \
                    fn + '\n\n' \
                    'Check that the file isn\'t in use by another program, and that you have write ' \
                    'permissions to the file and folder'
        return succsess, error_title, error_msg

def calc_grid_pos(pos, cols):
    """
    A little function to calculate the grid position of checkboxes
    :param pos:
    :param cols:
    :return:
    """
    calc_row = pos // cols
    calc_col = pos % cols

    return calc_row, calc_col

def edit_repl_opts(event, ext_pos, pos, patch_obj):
    pass