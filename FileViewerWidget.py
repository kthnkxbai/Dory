from PySide6.QtWidgets import  (QListView , QFileSystemModel ,QMenu ,
                                QMessageBox , QDialog , QLabel , QVBoxLayout,
                                QPushButton,QFormLayout)

from PySide6.QtCore import QDir , Signal , Qt , QFile , QSize
from PySide6.QtGui import QAction
from catchExecptions import catch_exceptions
import os
import random
import time
import sys
import subprocess
import platform


class FileListViewer(QListView):
    #Signals
    open_file           = Signal(str)
    open_folder         = Signal(str)
    open_in_new_window  = Signal(str)
    add_bookmark_path   = Signal((str,str))
    copy_file_signal    = Signal(str)
    cut_file_signal     = Signal(str)
    copy_folder_signal  = Signal(str)
    cut_folder_signal   = Signal(str)
    paste_signal        = Signal(str)
    
    
    @catch_exceptions
    def __init__(self, root_directory = QDir.homePath()) -> None:
        super().__init__()
        
        
        # Setting up the directory model
        self.directory_model = QFileSystemModel()
        self.directory_model.setRootPath(root_directory)
        self.directory_model.setFilter(QDir.Files | QDir.NoDotAndDotDot | QDir.AllDirs)
        
        # Setting up the file list view
        self.setModel(self.directory_model)
        self.setRootIndex(self.directory_model.index(root_directory))
        
        
        # Defining connections
        self.doubleClicked.connect(self.onDoubleClicked)
        
    # Defining the slots
    @catch_exceptions
    def onDoubleClicked(self, index):
        if not index.isValid():
            print("Invalid index in FileListWidget")
            return
        path = self.directory_model.filePath(index)
        if self.directory_model.isDir(index):
            self.open_folder.emit(path)
        else:
            self.open_file.emit(path)
                   
    @catch_exceptions
    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        menu = QMenu(self)
        
        if index.isValid():
            if self.directory_model.isDir(index):
                # Context Menu for a folder
                open_folder_action = QAction("Open", self)
                open_folder_new_window_action = QAction("Open in New Window", self)
                cut_folder_action = QAction("Cut", self)
                copy_folder_action = QAction("Copy", self)
                bookmark_action = QAction("Bookmark", self)
                delete_folder_action = QAction("Delete", self)             # Implimentation done in class
                rename_folder_action = QAction("Rename", self)             # Implimentation done in class
                properties_folder_action = QAction("Properties", self)     # Implimentation done in class
                
                menu.addActions([open_folder_action, open_folder_new_window_action, 
                                 cut_folder_action, copy_folder_action, bookmark_action, 
                                 delete_folder_action, rename_folder_action, properties_folder_action])
                
                open_folder_action.triggered.connect(lambda: self.open_folder.emit(self.directory_model.filePath(index)))
                open_folder_new_window_action.triggered.connect(lambda: self.open_in_new_window.emit(self.directory_model.filePath(index)))
                bookmark_action.triggered.connect(lambda: self.add_bookmark_path.emit((self.directory_model.filePath(index), self.directory_model.fileName(index))))
                cut_folder_action.triggered.connect(lambda: self.cut_folder_signal.emit(self.directory_model.filePath(index)))
                copy_folder_action.triggered.connect(lambda: self.copy_folder_signal.emit(self.directory_model.filePath(index)))
                delete_folder_action.triggered.connect(lambda: self.directory_model.rmdir(index))
                rename_folder_action.triggered.connect(lambda: self.renameFolder(index))
                properties_folder_action.triggered.connect(lambda: self.propertiesFolder(index))
            
            else:
                
                open_file_action = QAction("Open file", self)
                cut_file_action = QAction("Cut", self)
                copy_file_action = QAction("Copy", self)
                rename_file_action = QAction("Rename", self)
                delete_file_action = QAction("Delete", self)
                properties_file_action = QAction("Properties", self)
                
                menu.addActions([open_file_action, cut_file_action, copy_file_action, 
                                 rename_file_action, delete_file_action,
                                 properties_file_action])
        
                open_file_action.triggered.connect(lambda: self.open_file.emit(self.directory_model.filePath(index)))
                cut_file_action.triggered.connect(lambda: self.cut_file_signal.emit(self.directory_model.filePath(index)))
                copy_file_action.triggered.connect(lambda: self.copy_file_signal.emit(self.directory_model.filePath(index)))
                rename_file_action.triggered.connect(lambda: self.renameFile(index))
                delete_file_action.triggered.connect(lambda: self.directory_model.remove(index))
                properties_file_action.triggered.connect(lambda: self.propertiesFile(index))
        else:
            
            # Context Menu for the empty space
            paste_action = QAction("Paste", self)
            create_file_action = QAction("Create File", self)
            create_folder_action = QAction("Create Folder", self)
            open_in_terminal_action = QAction("Open in Terminal", self)
            show_hidden_files_action = QAction("Show Hidden Files", self , checkable = True)
            curr_dir_properties_action = QAction("Properties", self)
            
            menu.addActions([paste_action, create_file_action, create_folder_action, 
                             open_in_terminal_action, show_hidden_files_action, 
                             curr_dir_properties_action])
            
            paste_action.triggered.connect(self.paste)
            create_file_action.triggered.connect(lambda: self.createFile())
            create_folder_action.triggered.connect(lambda: self.createFolder())
            open_in_terminal_action.triggered.connect(lambda: self.openInTerminal())
            show_hidden_files_action.triggered.connect(lambda: self.showHiddenFiles())
            curr_dir_properties_action.triggered.connect(lambda: self.currDirProperties())
            
        # Show the context menu at the cursor position
        menu.exec(event.globalPos())
                 
    @catch_exceptions
    def updateRootIndex(self, directory : str):
        """Sets the new root index of the file list viewer""" 
         
        newRootIndex = self.directory_model.index(directory)
        if not newRootIndex.isValid():
            print('The new root index is not valid')
            return
        
        self.setRootIndex(newRootIndex)
                  
    @catch_exceptions
    def refreshView(self):
        self.directory_model.setRootPath(self.directory_model.rootPath())

    @catch_exceptions
    def setIconView(self):
        self.setViewMode(QListView.IconMode)
        self.setGridSize(QSize(70,70))
        self.setResizeMode(QListView.Adjust)
        self.setFlow(QListView.LeftToRight)
        
    @catch_exceptions
    def setListView(self):
        self.setViewMode(QListView.ListMode)
        self.setGridSize(QSize())
        self.setResizeMode(QListView.Adjust)
        self.setWordWrap(True)
        self.refreshView()
          
    @catch_exceptions
    def changeIconSize(self,size:int):
        """Change icon size in QListView if in IconMode."""
        if self.viewMode() == QListView.IconMode :
            self.setIconSize(QSize(size,size))
                
    @catch_exceptions
    def getCurrentDirectoryPath(self):
        return self.directory_model.filePath(self.rootIndex())
    
    
    @catch_exceptions
    def hideSelf(self):
        self.hide()
    
    
    @catch_exceptions
    def showSelf(self):
        self.show()
        
    
    # File operations
    @catch_exceptions
    def createFile(self):
        current_dir = self.getCurrentDirectoryPath()
        random_file_name = 'new_file' + str(random.randint(1,1000)) + '.txt'
        full_path = os.path.join(current_dir, random_file_name)
        
        try:
            with open(full_path, 'w') as new_file:
                new_file.write('')
                            
            # Refresh the icon view to show the new file
            self.refreshView()
            
        except PermissionError:
                QMessageBox.critical(self, "Error", f"Permission denied: Unable to create file '{full_path}'.")
        except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {str(e)}")

        file_index = self.directory_model.index(full_path)
        self.renameFile(file_index)
                    
                    
    @catch_exceptions
    def renameFile(self,index):
        ''' Puts the selected file in rename mode '''
        if index.isValid():
            self.edit(index)
            self.directory_model.dataChanged.connect(self.onFileRenamed)
        else:
            print('Invalid index in renameFile')
        
        
    @catch_exceptions
    def onFileRenamed(self, topLeft, bottomRight):
        
        """Handles the file rename operation."""
        
        index = topLeft
        if index.isValid():
            old_path = self.directory_model.filePath(index)
            new_name = self.directory_model.fileName(index)
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            # Check if the rename was successful (if the path has changed)
            if old_path != new_path and not QFile(new_path).exists():
                if not os.rename(old_path, new_path):
                    QMessageBox.critical(self, "Error", "Failed to rename the file.")
            else:
                # Revert the change if the name is not valid
                self.directory_model.setData(index, os.path.basename(old_path), Qt.EditRole)  # Reset to old name
         
                QMessageBox.warning(self, "Warning", "Invalid file name or name already exists.")
    
    @catch_exceptions
    def propertiesFile(self,index):
        if not index.isValid():
            return
        
        file_path = self.directory_model.filePath(index)
        
        # Retrieve properties
        properties = {
            "File Name": self.directory_model.fileName(index),
            "Size": f"{os.path.getsize(file_path)} bytes",
            "Date Modified": time.ctime(os.path.getmtime(file_path)),
            "Type": self.directory_model.type(index)
        }
        
        dialog = PropertiesDialog("File Properties", properties)
        dialog.exec()
    
    # Folder operations
    @catch_exceptions
    def createFolder(self):
        current_dir = self.getCurrentDirectoryPath()
        random_folder_name = 'new_folder' + str(random.randint(1,1000))
        full_path = os.path.join(current_dir, random_folder_name)
        
        try:
            os.makedirs(full_path)
            self.refreshView()
        except PermissionError:
            QMessageBox.critical(self, "Error", f"Permission denied: Unable to create folder '{full_path}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create folder: {str(e)}")
        
    
    @catch_exceptions
    def renameFolder(self,index):
        ''' Puts the selected folder in rename mode '''
        if index.isValid():
            self.edit(index)  # Enable inline editing for the folder
        else:
            print('Invalid index in renameFolder')


    @catch_exceptions
    def onFolderRenamed(self, topLeft, bottomRight):
        """Handles the folder rename operation."""
        index = topLeft
        if index.isValid():
            old_path = self.directory_model.filePath(index)
            new_name = self.directory_model.fileName(index)
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            # Check if the rename was successful (if the path has changed)
            if old_path != new_path and not QFile(new_path).exists():
                if not os.rename(old_path, new_path):
                    QMessageBox.critical(self, "Error", "Failed to rename the folder.")
            else:
                # Revert the change if the name is not valid
                self.directory_model.setData(index, os.path.basename(old_path), Qt.EditRole)
    
    @catch_exceptions
    def propertiesFolder(self,index):
        if not index.isValid():
            return
        
        folder_path = self.directory_model.filePath(index)
        
        # Retrieve properties
        try:
 
            properties = {
                "Folder Name": self.directory_model.fileName(index),
                "Number of Files": str(len(os.listdir(folder_path))),
                "Date Modified": time.ctime(os.path.getmtime(folder_path)),
                "Type": "Folder"
            }
            
            dialog = PropertiesDialog("Folder Properties", properties)
            dialog.exec()\
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve folder properties: {str(e)}")

    # widgets operations
    
    @catch_exceptions
    def paste(self):
        self.paste_signal.emit(self.getCurrentDirectoryPath())
    
    @catch_exceptions
    def openInTerminal(self):
        current_dir = self.getCurrentDirectoryPath()  # Get the current directory path
        if not current_dir:
            print("No valid current directory to open in terminal.")
            return

        try:
            if platform.system() == "Windows":  # Windows
                # Use 'start' to open the command prompt in the specified directory
                subprocess.Popen(f'start cmd /K "cd {current_dir}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                # Use 'open' with 'Terminal' to open the terminal in the specified directory
                subprocess.Popen(['open', '-a', 'Terminal', current_dir])
            elif platform.system() == "Linux":  # Linux
                # Use 'xdg-terminal' or 'gnome-terminal' or any terminal available
                subprocess.Popen(['gnome-terminal', '--working-directory', current_dir])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open terminal: {str(e)}")


    @catch_exceptions
    def showHiddenFiles(self):
        """Toggles the visibility of hidden files in the file list."""
        # Update the state
        self.showing_hidden_files = not self.showing_hidden_files
        
        # Set the filter to include/exclude hidden files based on the state
        if self.showing_hidden_files:
            self.directory_model.setFilter(QDir.Files | QDir.NoDotAndDotDot | QDir.AllDirs)
        else:
            self.directory_model.setFilter(QDir.Files | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden)
        
        # Refresh the view to reflect the changes
        self.refreshView()

    @catch_exceptions
    def updateRootIndex(self, directory: str):
        """Sets the new root index of the file list viewer."""
        new_root_index = self.directory_model.index(directory)
        if not new_root_index.isValid():
            print("The new root index is not valid.")
            return

        self.setRootIndex(new_root_index)
    
    @catch_exceptions
    def currDirProperties(self):
        index = self.currentIndex()
        if not index.isValid():
            return
        
        folder_path = self.directory_model.filePath(index)
        
        # Retrieve properties
        try:
            properties = {
                "Folder Name": self.directory_model.fileName(index),
                "Number of Files": str(len(os.listdir(folder_path))),
                "Date Modified": time.ctime(os.path.getmtime(folder_path)),
                "Type": "Folder"
            }
            
            dialog = PropertiesDialog("Folder Properties", properties)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve folder properties: {str(e)}")

    
    
    
class PropertiesDialog(QDialog):
    @catch_exceptions
    def __init__(self, title, properties):
        super().__init__()
        self.setWindowTitle(title)
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        for key, value in properties.items():
            form_layout.addRow(QLabel(key), QLabel(value))

        layout.addLayout(form_layout)

        button = QPushButton("Close")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)