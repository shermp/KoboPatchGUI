import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PatchEdit import *
from collections import OrderedDict
import copy

class PatchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_dic = OrderedDict()
        self.orig_patch_obj_dic = OrderedDict()
        self.patch_obj_dic = OrderedDict()
        self.cb_dic = OrderedDict()
        self.vBox_list = []
        self.init_completed = False
        self.apply_button = None
        self.disable_all_button = None
        self.defaults_button = None

        fn_list, file_type = QFileDialog.getOpenFileNames(caption='Open File', filter='Kobo Patch (*.patch)')
        if fn_list:
            fd = {fn: None for fn in fn_list}
            self.file_dic, error = read_patch_files(fd)
            if error:
                QMessageBox.critical(None, 'Read Error!', error)
                self.init_completed = False
            else:
                for (fn, patch_text) in iterDic(self.file_dic):
                    self.orig_patch_obj_dic[fn] = gen_patch_obj_list(fn, patch_text)
                self.init_completed = True
                self.initialize()
        else:
            self.init_completed = False

    def initialize(self):
        self.patch_obj_dic = copy.deepcopy(self.orig_patch_obj_dic)
        cont_index = 0
        vBox = QVBoxLayout(self)
        for (fn, patch_obj_list) in iterDic(self.patch_obj_dic):
            self.cb_dic[fn] = []
            gb = QGroupBox(fn)
            cb_grid = QGridLayout(self)
            # Create and add checkboxes to appropriate LabelFrame
            for (cb_index, obj) in enumerate(patch_obj_list):
                # Create checkbox variable and checkbox label for display
                cb_name = ''
                if obj.group:
                    cb_name = obj.name + '\n(' + obj.group + ')'
                else:
                    cb_name = obj.name

                # Create and add checkboxes to the LabelFrame, using the grid geometry manager
                self.cb_dic[fn].append(QCheckBox(cb_name))
                # Set initial state of checkboxes
                if 'yes' in obj.status:
                    self.cb_dic[fn][cb_index].setCheckState(Qt.Checked)
                else:
                    self.cb_dic[fn][cb_index].setCheckState(Qt.Unchecked)

                self.cb_dic[fn][cb_index].setToolTip(obj.help_text)
                grid_pos = calc_grid_pos(cb_index, cols=3)

                cb_grid.addWidget(self.cb_dic[fn][cb_index], grid_pos[0], grid_pos[1])

            gb.setLayout(cb_grid)
            vBox.addWidget(gb)

            cont_index += 1

        self.apply_button = QPushButton('Apply Changes')
        self.disable_all_button = QPushButton("Disable All")
        self.defaults_button = QPushButton('Restore Settings')

        button_box = QHBoxLayout()
        button_box.addWidget(self.apply_button)
        button_box.addWidget(self.disable_all_button)
        button_box.addWidget(self.defaults_button)
        vBox.addLayout(button_box)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(vBox)
        self.setWindowTitle('Kobo Patch GUI')
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pg = PatchGUI()
    sys.exit(app.exec_())
