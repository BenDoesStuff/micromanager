"""Micromanager application entry point."""
from PyQt5 import QtWidgets

from micromanager.controller import TaskController
from micromanager.model import TaskModel
from micromanager.view import TaskView


def main() -> None:
    app = QtWidgets.QApplication([])

    model = TaskModel()
    view = TaskView()
    controller = TaskController(model, view)

    view.show()
    app.exec_()


if __name__ == "__main__":
    main()


