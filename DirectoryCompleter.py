from PySide6.QtWidgets import QCompleter, QLineEdit
from PySide6.QtCore import Qt, QDir , QStringListModel  ,QFileInfo
from catchExecptions import catch_exceptions

class DirectoryCompleter:
    
    @catch_exceptions
    def __init__(self, line_edit: QLineEdit, parent=None):
        self.completer = QCompleter(parent)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)

        self.line_edit = line_edit
        self.line_edit.setCompleter(self.completer)
        self.line_edit.textChanged.connect(self.updateCompleter)

        
    @catch_exceptions
    def updateCompleter(self , updatedString:str):
        # Get the current text from the QLineEdit
        current_text = updatedString

        # Determine the directory path to complete
        if current_text:
            directory = QFileInfo(current_text).absolutePath()
            directory = QDir(directory)
            prefix = QFileInfo(current_text).fileName()

            # List all items in the directory
            items = directory.entryList(QDir.Dirs | QDir.NoDotAndDotDot)
                        
            # Filter items based on the prefix
            filtered_items = [item for item in items if item.startswith(prefix)]

            # Create full paths
            full_paths = [directory.filePath(item) for item in filtered_items]

            # Set the model for the completer
            self.completer.setModel(QStringListModel(full_paths))


    @catch_exceptions
    def setDefaultPath(self, path: str):
        self.default_path = QDir.toNativeSeparators(QDir(path).absolutePath())


    @catch_exceptions
    def setCompletionMode(self, mode: QCompleter.CompletionMode):
        self.completer.setCompletionMode(mode)


    @catch_exceptions
    def setFilterMode(self, mode: Qt.MatchFlag):
        self.completer.setFilterMode(mode)


    @catch_exceptions
    def setCaseSensitivity(self, sensitive: bool):
        self.completer.setCaseSensitivity(Qt.CaseSensitive if sensitive else Qt.CaseInsensitive)
