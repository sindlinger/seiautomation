from __future__ import annotations

from typing import Callable, Dict

from PySide6 import QtCore, QtGui, QtWidgets

from .config import Settings
from .tasks import download_zip_lote, preencher_anotacoes_ok, exportar_relacao_csv


class Worker(QtCore.QThread):
    log_signal = QtCore.Signal(str)
    finished_signal = QtCore.Signal(bool, str)

    def __init__(
        self, tasks: Dict[str, Callable[[Callable[[str], None]], None]], parent: QtCore.QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._tasks = tasks

    def run(self) -> None:  # noqa: D401
        try:
            for name, task in self._tasks.items():
                self.log_signal.emit(f"Iniciando: {name}")
                task(lambda msg, prefix=name: self.log_signal.emit(f"{prefix}: {msg}"))
                self.log_signal.emit(f"Concluído: {name}")
            self.finished_signal.emit(True, "Todas as tarefas foram concluídas.")
        except Exception as exc:  # noqa: BLE001
            self.finished_signal.emit(False, f"Erro: {exc}")


class MainWindow(QtWidgets.QWidget):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.setWindowTitle("SEIAutomation")
        self.resize(420, 320)

        self.checkbox_download = QtWidgets.QCheckBox("Baixar processos do bloco (ZIP)")
        self.checkbox_anotacoes = QtWidgets.QCheckBox('Preencher anotações com "OK"')
        self.checkbox_export = QtWidgets.QCheckBox("Exportar relação do bloco (CSV)")
        self.checkbox_headless = QtWidgets.QCheckBox("Executar em modo headless (sem janela)")
        self.checkbox_headless.setChecked(True)
        self.checkbox_auto_credentials = QtWidgets.QCheckBox("Preencher credenciais automaticamente")
        self.checkbox_auto_credentials.setChecked(True)
        if not self.settings.is_admin:
            self.checkbox_auto_credentials.setEnabled(False)
            self.checkbox_auto_credentials.setToolTip("Disponível apenas para administradores.")
        self.checkbox_dev_mode = QtWidgets.QCheckBox("Modo desenvolvedor (usar servidor fake)")
        self.checkbox_dev_mode.setChecked(self.settings.dev_mode)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)

        self.run_button = QtWidgets.QPushButton("Executar tarefas selecionadas")
        self.run_button.clicked.connect(self._start_tasks)
        self.close_button = QtWidgets.QPushButton("Fechar")
        self.close_button.clicked.connect(self.close)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.close_button)

        bloco_layout = QtWidgets.QHBoxLayout()
        bloco_label = QtWidgets.QLabel("ID do bloco:")
        self.bloco_input = QtWidgets.QLineEdit(str(self.settings.bloco_id))
        self.bloco_input.setMaximumWidth(120)
        self.bloco_input.setValidator(QtGui.QIntValidator(1, 999999))
        bloco_layout.addWidget(bloco_label)
        bloco_layout.addWidget(self.bloco_input)
        bloco_layout.addStretch()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(bloco_layout)
        layout.addWidget(self.checkbox_download)
        layout.addWidget(self.checkbox_anotacoes)
        layout.addWidget(self.checkbox_export)
        layout.addWidget(self.checkbox_headless)
        layout.addWidget(self.checkbox_auto_credentials)
        layout.addWidget(self.checkbox_dev_mode)
        layout.addWidget(self.log)
        layout.addLayout(button_layout)

        self.worker: Worker | None = None
        self._setup_tray_icon()

    def _setup_tray_icon(self) -> None:
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray = QtWidgets.QSystemTrayIcon(icon, self)
        self.tray.setToolTip("SEIAutomation")

        menu = QtWidgets.QMenu()
        action_show = menu.addAction("Abrir janela")
        action_show.triggered.connect(self.showNormal)
        action_quit = menu.addAction("Sair")
        action_quit.triggered.connect(QtWidgets.QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _append_log(self, message: str) -> None:
        self.log.appendPlainText(message)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _start_tasks(self) -> None:
        tasks_to_run: Dict[str, Callable[[Callable[[str], None]], None]] = {}
        headless = self.checkbox_headless.isChecked()
        auto_credentials = self.checkbox_auto_credentials.isChecked() and self.settings.is_admin
        dev_mode = self.checkbox_dev_mode.isChecked()
        bloco_id = self._resolve_bloco_id()
        if bloco_id is None:
            return
        runtime_settings = self.settings.with_dev_mode(dev_mode)

        if self.checkbox_download.isChecked():
            tasks_to_run["Download de ZIPs"] = lambda progress, cfg=runtime_settings: download_zip_lote(
                cfg,
                headless=headless,
                progress=progress,
                auto_credentials=auto_credentials,
                bloco_id=bloco_id,
            )
        if self.checkbox_anotacoes.isChecked():
            tasks_to_run["Atualização de anotações"] = lambda progress, cfg=runtime_settings: preencher_anotacoes_ok(
                cfg,
                headless=headless,
                progress=progress,
                auto_credentials=auto_credentials,
                bloco_id=bloco_id,
            )
        if self.checkbox_export.isChecked():
            tasks_to_run["Exportar relação"] = lambda progress, cfg=runtime_settings: exportar_relacao_csv(
                cfg,
                headless=headless,
                progress=progress,
                bloco_id=bloco_id,
                auto_credentials=auto_credentials,
            )

        if not tasks_to_run:
            QtWidgets.QMessageBox.information(self, "SEIAutomation", "Selecione ao menos uma tarefa.")
            return

        self.run_button.setEnabled(False)
        self.worker = Worker(tasks_to_run)
        self.worker.log_signal.connect(self._append_log)
        self.worker.finished_signal.connect(self._on_tasks_finished)
        if dev_mode:
            self._append_log("Modo desenvolvedor ativo: utilizando servidor fake.")
        self.worker.start()

    def _on_tasks_finished(self, success: bool, message: str) -> None:
        self.run_button.setEnabled(True)
        self._append_log(message)
        icon = QtWidgets.QMessageBox.Information if success else QtWidgets.QMessageBox.Warning
        QtWidgets.QMessageBox(icon, "SEIAutomation", message, QtWidgets.QMessageBox.Ok, self).exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802,D401
        self.hide()
        self.tray.showMessage("SEIAutomation", "Executando em segundo plano. Clique no ícone para reabrir.")
        event.ignore()

    def _resolve_bloco_id(self) -> int | None:
        text = self.bloco_input.text().strip()
        if not text:
            QtWidgets.QMessageBox.warning(self, "SEIAutomation", "Informe o ID do bloco.")
            return None
        try:
            bloco_id = int(text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "SEIAutomation", "ID do bloco inválido.")
            return None
        return bloco_id


def run_gui(settings: Settings | None = None) -> None:
    import sys

    if settings is None:
        settings = Settings.load()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())
