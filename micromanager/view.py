from __future__ import annotations

from typing import Callable, List

from PyQt5 import QtCore, QtGui, QtWidgets


class TaskView(QtWidgets.QMainWindow):
    """Main window displaying and managing UI widgets."""

    submit_task = QtCore.pyqtSignal(str)
    mark_done = QtCore.pyqtSignal()
    toggle_history = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Micromanager")
        self.resize(500, 300)

        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)

        # Input for the large task
        self.task_input = QtWidgets.QLineEdit()
        self.task_input.setPlaceholderText("Enter a large task...")
        self.layout.addWidget(self.task_input)

        self.submit_button = QtWidgets.QPushButton("Break Down Task")
        self.layout.addWidget(self.submit_button)

        # Current step display
        self.step_label = QtWidgets.QLabel("")
        self.step_label.setWordWrap(True)
        self.step_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.step_label, 1)

        self.mark_button = QtWidgets.QPushButton("Mark as Done")
        self.layout.addWidget(self.mark_button)

        self.progress = QtWidgets.QProgressBar()
        self.layout.addWidget(self.progress)

        self.history_button = QtWidgets.QPushButton("Show History")
        self.layout.addWidget(self.history_button)

        # History list hidden by default
        self.history_list = QtWidgets.QListWidget()
        self.history_list.hide()
        self.layout.addWidget(self.history_list)

        self.dark_mode_action = QtWidgets.QAction("Dark Mode", self)
        self.dark_mode_action.setCheckable(True)
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.dark_mode_action)

        # Connect signals
        self.submit_button.clicked.connect(self._on_submit)
        self.mark_button.clicked.connect(lambda: self.mark_done.emit())
        self.history_button.clicked.connect(lambda: self.toggle_history.emit())
        self.dark_mode_action.toggled.connect(self.set_dark_mode)

    def _on_submit(self) -> None:
        text = self.task_input.text().strip()
        if text:
            self.submit_task.emit(text)

    def set_dark_mode(self, enabled: bool) -> None:
        """Toggle a simple dark mode palette."""
        palette = QtGui.QPalette()
        if enabled:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        self.setPalette(palette)

    def update_step(self, step: str) -> None:
        self.step_label.setText(step)

    def update_progress(self, completed: int, total: int) -> None:
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(completed)

    def update_history(self, steps: List[str], current_index: int) -> None:
        self.history_list.clear()
        for i, step in enumerate(steps):
            item = QtWidgets.QListWidgetItem(step)
            if i < current_index:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            self.history_list.addItem(item)

    def toggle_history_view(self) -> None:
        visible = not self.history_list.isVisible()
        self.history_list.setVisible(visible)
        self.history_button.setText("Hide History" if visible else "Show History")


