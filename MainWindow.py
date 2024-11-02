from PySide6.QtWidgets import QMainWindow , QVBoxLayout , QHBoxLayout , QWidget , QSplitter , QApplication 
from PySide6.QtCore import Qt , QDir
from AddressBarWidget import AddressBarWidget
from BookmarkTree import BookmarkTree
from DirectoryTree import DirectoryTree
from FileViewerWidget import FileListViewer
from MenuBarWidget import MenuBar
from SearchInputWidget import SearchInputWidget
from SearchResultWidget import SearchResultWidget
from SearchThread import SearchThread
from StatusBarWidget import StatusBarWidget
from catchExecptions import catch_exceptions
import os
import subprocess
import platform
import shutil


class MainWindow(QMainWindow):
    def __init__(self, root_dir = QDir.homePath()):
        super().__init__()
        self.root_dir = root_dir
        self.setWindowTitle("Nameless File Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # History stacks
        self.back_stack = []    
        self.forward_stack = []
        
        # Clipboard
        self.clipboard = QApplication.clipboard()
        self.clipboard_mode = None  
        
        self.setup_ui()
        self.setup_initial_state()
        
        
        
    @catch_exceptions
    def setup_ui(self):
        
        
        # Creating widgets
        self.menu_bar               = MenuBar()
        self.address_bar_widget     = AddressBarWidget()
        self.directory_tree         = DirectoryTree(root_directory=self.root_dir)
        self.bookmark_tree          = BookmarkTree(bookmarks_file="bookmarks.json")
        self.file_viewer            = FileListViewer(root_directory=self.root_dir)
        self.search_input           = SearchInputWidget()
        self.search_result          = SearchResultWidget()
        self.status_bar             = StatusBarWidget()
        
        # Creating layouts 
        main_layout = QVBoxLayout()                     # Main layout for the entire window
        content_layout = QSplitter()                    # Layout for the main content area (trees and file view)
        content_layout.setOrientation(Qt.Horizontal)
        side_pane_layout = QVBoxLayout()                # Layout for the right-side widgets (search input, viewer)
        file_search_layout = QHBoxLayout()              # Layout for the file viewer and search result area
        
        # Adding widgets to layouts
        main_layout.addWidget(self.address_bar_widget)
        
        
        main_layout.addWidget(content_layout)
        content_layout.addWidget(self.directory_tree)
        content_layout.addWidget(self.bookmark_tree)
        content_layout.addWidget(side_pane_layout)  
        
        
        side_pane_layout.addWidget(self.search_input)
        side_pane_layout.addWidget(file_search_layout)
        
        
        file_search_layout.addWidget(self.file_viewer)
        file_search_layout.addWidget(self.search_result)
        
        # Setting the main layout
        self_central_widget = QWidget()
        self_central_widget.setLayout(main_layout)
        
        # Setting up the main window
        self.setCentralWidget(self_central_widget)
        self.setMenuBar(self.menu_bar)
        self.setStatusBar(self.status_bar)
        
        # Connecting signals
        
        # Address widget signals
        self.address_bar_widget.go_back_signal.connect(lambda:self.goBack())
        self.address_bar_widget.go_forward_signal.connect(lambda:self.goForward())
        self.address_bar_widget.run_search.connect(lambda: self.triggerInputSearch())
        self.address_bar_widget.to_icon_mode.connect(lambda: self.file_viewer.setIconView())
        self.address_bar_widget.to_list_mode.connect(lambda: self.file_viewer.setListView())
        self.address_bar_widget.address_path_changed.connect(lambda path: self.setRootIndex(path))

        # Bookmark widget signals
        self.bookmark_tree.open_in_cur_window.connect(lambda bookmark_path : self.setRootIndex(bookmark_path))
        self.bookmark_tree.open_in_new_window.connect(lambda bookmark_path : self.openInNewWindow(bookmark_path))


        # Directory tree signals
        self.directory_tree.dir_double_clicked.connect(lambda path : self.setRootIndex(path))


        # File viewer signals
        self.file_viewer.open_file.connect(lambda file_path : self.openFile(file_path))
        self.file_viewer.open_folder.connect(lambda path : self.setRootIndex(path))
        self.file_viewer.open_in_new_window.connect(lambda path : self.openInNewWindow(path))
        self.file_viewer.copy_file_signal.connect(lambda path : self.copyFile(path))
        self.file_viewer.cut_file_signal.connect(lambda path : self.cutFile(path))
        self.file_viewer.copy_folder_signal.connect(lambda path : self.copyFolder(path))
        self.file_viewer.cut_folder_signal.connect(lambda path : self.cutFolder(path))
        self.file_viewer.add_bookmark_path.connect(lambda name,path : self.bookmark_tree.addBookmark(name,path))
        self.file_viewer.paste_signal.connect(lambda target_directory : self.paste(target_directory))
        
        
        # Menu bar signals
        self.menu_bar.open_new_window.connect(lambda : self.openInNewWindow())
        self.menu_bar.refresh_view.connect(lambda : self.refreshView())
        self.menu_bar.to_icon_mode.connect(lambda : self.file_viewer.setIconView())
        self.menu_bar.to_list_mode.connect(lambda : self.file_viewer.setListView())
        self.menu_bar.change_directory.connect(lambda path : self.setRootIndex(path))
        self.menu_bar.run_search_widget.connect(lambda : self.triggerInputSearch())
        self.menu_bar.add_current_dir_bookmark_signal.connect(lambda : self.addCurrentDirBookmark())
        self.menu_bar.toggle_bookmark.connect(lambda : self.toogleLeftSidebar())
        self.menu_bar.create_new_file.connect(lambda : self.file_viewer.createFile())
        self.menu_bar.create_new_folder.connect(lambda : self.file_viewer.createFolder())
        self.menu_bar.open_dir_properties.connect(lambda : self.file_viewer.currDirProperties())
        
        
        # Search signals
        self.search_input.search_conditions_signal.connect(lambda conditions_dict: self.runSearchThread(conditions_dict))
        self.search_result.path_double_clicked.connect(lambda path : self.showInFileViewer(path))
        
        # Status bar signals
        self.status_bar.icon_size.connect(lambda size : self.file_viewer.setIconSize(size))
        self.status_bar.hide_left_sidebar.connect(lambda : self.hideLeftSidebar())
        self.status_bar.toggle_left_sidebar.connect(lambda : self.toogleLeftSidebar())
        
    
    @catch_exceptions
    def setup_initial_state(self):
        self.search_input.isVisible(False)
        self.search_result.isVisible(False)
        self.bookmark_tree.isVisible(False)
        
    # Implementing the goBack and goForward methods  
    @catch_exceptions
    def goForward(self):
        if self.forward_stack:
            # Save current path to back stack before going forward
            current_path = self.file_viewer.getCurrentDirectoryPath()
            if not self.back_stack or self.back_stack[-1] != current_path:
                self.back_stack.append(current_path)

            # Navigate to the new path
            new_path = self.forward_stack.pop()
            self.setRootIndex(new_path)
            
    
    
    @catch_exceptions
    def goBack(self):
        if self.back_stack:
            # Save current path to forward stack before going back
            current_path = self.file_viewer.getCurrentDirectoryPath()
            if not self.forward_stack or self.forward_stack[-1] != current_path:
                self.forward_stack.append(current_path)

            # Navigate to the new path
            new_path = self.back_stack.pop()
            self.setRootIndex(new_path)
    

    @catch_exceptions
    def setRootIndex(self, path: str):
        """Sets the root index to the specified path and manages history stacks."""
        
        # Store the current path in the back stack if it's a new navigation
        current_path = self.file_viewer.getCurrentDirectoryPath()
        if current_path and (not self.back_stack or self.back_stack[-1] != current_path):
            self.back_stack.append(current_path)
            
        # Clear forward stack if this navigation is from a new source
        if not self.forward_stack or self.forward_stack[-1] != path:
            self.forward_stack.clear()

        # Set the new root index in both the file viewer and directory tree
        self.file_viewer.setRootIndex(path)
        self.directory_tree.setNewRootIndex(path)
        
    @catch_exceptions
    def triggerInputSearch(self):
        self.search_input.setVisible(True)
        self.search_result.setVisible(False)
        self.file_viewer.setVisible(True)

    @catch_exceptions
    def openInNewWindow(self, path : str = QDir.homePath()):
        """Function to create and show a new MainWindow."""
        new_window = MainWindow(root_dir=path)
    
    
    @catch_exceptions
    def openFile(self , file_path : str):
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            elif platform.system() == "Linux":  # Linux
                subprocess.run(["xdg-open", file_path])
            else:
                raise NotImplementedError("Unsupported operating system.")
        except Exception as e:
            print(f"Error opening file: {e}")
    
    
    @catch_exceptions
    def copyFile(self, path:str):
        """Copies the file path to the clipboard."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        self.clipboard.setText(path)
        self.clipboard_mode = "copy"
    
    
    @catch_exceptions
    def cutFile(self , path:str):
        """Cuts the file path to the clipboard."""
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        self.clipboard.setText(path)
        self.clipboard_mode = "cut"
    
    
    @catch_exceptions
    def copyFolder(self , path:str):
        """Copies the folder path to the clipboard."""
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder not found: {path}")
        
        self.clipboard.setText(path)
        self.clipboard_mode = "copy"
    
    @catch_exceptions
    def cutFolder(self,path:str):
        """Cuts the folder path to the clipboard."""
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder not found: {path}")
        self.clipboard.setText(path)
        self.clipboard_mode = "cut" 
        
    @catch_exceptions
    def paste(self, target_directory: str):
            """Pastes the file or folder from the clipboard into the target directory."""
            source_path = self.clipboard.text()
            
            if not source_path or not os.path.exists(source_path):
                raise FileNotFoundError("No file or folder in clipboard to paste")
                

            # Define destination path
            destination_path = os.path.join(target_directory, os.path.basename(source_path))

            
            if self.clipboard_mode == "copy":
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, destination_path)
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
            elif self.clipboard_mode == "cut":
                shutil.move(source_path, destination_path)
                self.clipboard.clear()  # Clear clipboard after moving

                
    
    @catch_exceptions
    def getCurrentDirectoryPath(self):
        return self.file_viewer.getCurrentDirectoryPath()
    
    
    @catch_exceptions
    def refreshView(self):
        self.directory_tree.refreshView()
        self.file_viewer.refreshView()
    
    
    @catch_exceptions
    def toogleLeftSidebar(self):
        
        if not (self.bookmark_tree.isVisible() or self.directory_tree.isVisible()):
            self.bookmark_tree.isVisible(False)
            self.directory_tree.isVisible(True)
        
        self.bookmark_tree.isVisible(not self.bookmark_tree.isVisible())
        self.directory_tree.isVisible(not self.directory_tree.isVisible())
            
            
    @catch_exceptions
    def hideLeftSidebar(self):
        self.bookmark_tree.isVisible(False)
        self.directory_tree.isVisible(False)
    
    def toggleRightSidebar(self):
        self.search_input.isVisible(not self.search_input.isVisible())
        self.search_result.isVisible(not self.search_result.isVisible())
        self.file_viewer.isVisible(not self.file_viewer.isVisible())
    
    @catch_exceptions
    def addCurrentDirBookmark(self):
        path = self.file_viewer.getCurrentDirectoryPath()
        name = QDir(path).dirName()
        
        self.bookmark_tree.addBookmark(name , path)
        
    def runSearchThread(self , conditions_dict : dict):
        search_text = conditions_dict['search_text']
        case_sensitive = conditions_dict['case_sensitive']
        recursive_search = conditions_dict['recursive_search']
        full_match_search = conditions_dict['full_match_search']
        
        search_thread = SearchThread(search_text , case_sensitive , recursive_search , full_match_search , self.getCurrentDirectoryPath())

        search_thread.searchFiles()
        search_thread.list_of_file_items.connect(lambda items : self.search_result.setResults(items))
        
        self.toggleSearchResults()
        
    def toggleSearchResults(self):
        self.search_result.setVisible(True)
        self.file_viewer.setVisible(False)
    
    def showInFileViewer(self , path:str):
        self.search_result.setVisible(False)
        self.search_input.setVisible(False)
        self.file_viewer.setVisible(True)
        self.setRootIndex(path)
        
    