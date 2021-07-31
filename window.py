from typing import Callable, List, Tuple, TYPE_CHECKING, Optional
from pathlib import Path

import aqt
import aqt.addons
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip, showText, saveGeom, restoreGeom

from .errors import InvalidConfigValueError

if TYPE_CHECKING:
    from .manager import ConfigManager


class ConfigWindow(QDialog):
    def __init__(self, conf: "ConfigManager") -> None:
        QDialog.__init__(self, mw, Qt.Window)  # type: ignore
        self.conf = conf
        self.mgr = mw.addonManager
        self.setWindowTitle(f"Config for {conf.addon_name}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.widget_updates: List[Callable[[], None]] = []
        self._on_save_hook: List[Callable[[], None]] = []
        self.setup()
        restoreGeom(self, f"addonconfig-{conf.addon_name}")

    def setup(self) -> None:
        self.outer_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        main_layout = self.main_layout
        self.outer_layout.addLayout(main_layout)
        self.setLayout(self.outer_layout)

        self.main_tab = QTabWidget()
        main_tab = self.main_tab
        main_tab.setFocusPolicy(Qt.StrongFocus)
        main_layout.addWidget(main_tab)
        self.setup_buttons()

    def setup_buttons(self) -> None:
        btn_box = QHBoxLayout()

        advanced_btn = QPushButton("Advanced")
        advanced_btn.clicked.connect(self.on_advanced)
        btn_box.addWidget(advanced_btn)

        reset_btn = QPushButton("Restore Defaults")
        reset_btn.clicked.connect(self.on_reset)
        btn_box.addWidget(reset_btn)

        btn_box.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.on_cancel)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.setShortcut("Ctrl+Return")
        save_btn.clicked.connect(self.on_save)
        btn_box.addWidget(save_btn)

        self.outer_layout.addLayout(btn_box)

    def update_widgets(self) -> None:
        try:
            for widget_update in self.widget_updates:
                widget_update()
        except InvalidConfigValueError as e:
            advanced = self.advanced_window()
            dial, bbox = showText(
                "Invalid Config. Please fix the following issue in the advanced config editor. \n\n"
                + str(e),
                title="Invalid Config",
                parent=advanced,
                run=False,
            )
            button = QPushButton("Quit Config")
            bbox.addButton(button, QDialogButtonBox.DestructiveRole)
            bbox.button(QDialogButtonBox.Close).setDefault(True)

            def quit() -> None:
                dial.close()
                advanced.close()
                self.widget_updates = []
                self.close()

            button.clicked.connect(quit)
            dial.show()
            advanced.exec_()
            self.conf.load()
            self.update_widgets()

    def on_open(self) -> None:
        self.update_widgets()

    def on_save(self) -> None:
        for hook in self._on_save_hook:
            hook()
        self.conf.save()
        self.close()

    def on_cancel(self) -> None:
        self.close()

    def on_reset(self) -> None:
        self.conf.load_defaults()
        self.update_widgets()
        tooltip("Press save to save changes")

    def on_advanced(self) -> None:
        self.advanced_window().exec_()
        self.conf.load()
        self.update_widgets()

    def advanced_window(self) -> aqt.addons.ConfigEditor:
        return aqt.addons.ConfigEditor(
            self, self.conf.addon_dir, self.conf._config  # type: ignore
        )

    def closeEvent(self, evt: QCloseEvent) -> None:
        # Discard the contents when clicked cancel,
        # and also in case the window was clicked without clicking any of the buttons
        self.conf.load()
        saveGeom(self, f"addonconfig-{self.conf.addon_name}")
        evt.accept()

    # Add Widgets

    def add_tab(self, name: str) -> "ConfigLayout":
        tab = QWidget(self)
        tab.conf = self.conf  # type: ignore
        tab.config_window = self  # type: ignore
        tab.widget_updates = self.widget_updates  # type: ignore
        layout = ConfigLayout(tab, QBoxLayout.TopToBottom)
        tab.setLayout(layout)
        self.main_tab.addTab(tab, name)
        return layout

    def execute_on_save(self, hook: Callable[[], None]) -> None:
        self._on_save_hook.append(hook)

    def set_footer(
        self,
        text: str,
        html: bool = False,
        size: int = 0,
        multiline: bool = False,
        tooltip: Optional[str] = None,
    ) -> QLabel:
        footer = QLabel(text)
        if html:
            footer.setTextFormat(Qt.RichText)
            footer.setOpenExternalLinks(True)
        else:
            footer.setTextFormat(Qt.PlainText)
        if size:
            font = QFont()
            font.setPixelSize(size)
            footer.setFont(font)
        if multiline:
            footer.setWordWrap(True)
        if tooltip is not None:
            footer.setToolTip(tooltip)

        self.main_layout.addWidget(footer)
        return footer


class ConfigLayout(QBoxLayout):
    def __init__(self, parent: QObject, direction: QBoxLayout.Direction):
        QBoxLayout.__init__(self, direction)
        self.conf = parent.conf
        self.config_window = parent.config_window
        self.widget_updates = parent.widget_updates

    def text(
        self,
        text: str,
        bold: bool = False,
        html: bool = False,
        size: int = 0,
        multiline: bool = False,
        tooltip: Optional[str] = None,
    ) -> QLabel:
        label_widget = QLabel(text)
        label_widget.setTextInteractionFlags(Qt.TextBrowserInteraction)
        if html:
            label_widget.setTextFormat(Qt.RichText)
            label_widget.setOpenExternalLinks(True)
        else:
            label_widget.setTextFormat(Qt.PlainText)
        if bold or size:
            font = QFont()
            if bold:
                font.setBold(True)
            if size:
                font.setPixelSize(size)
            label_widget.setFont(font)
        if multiline:
            label_widget.setWordWrap(True)
        if tooltip is not None:
            label_widget.setToolTip(tooltip)

        self.addWidget(label_widget)
        return label_widget

    # Config Input Widgets

    def checkbox(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QCheckBox:
        "For boolean config"
        checkbox = QCheckBox()
        if description is not None:
            checkbox.setText(description)
        if tooltip is not None:
            checkbox.setToolTip(tooltip)

        def update() -> None:
            value = self.conf.get(key)
            if not isinstance(value, bool):
                raise InvalidConfigValueError(key, "boolean", value)
            checkbox.setChecked(value)

        self.widget_updates.append(update)

        checkbox.stateChanged.connect(
            lambda s: self.conf.set(key, s == Qt.Checked))
        self.addWidget(checkbox)
        return checkbox

    def dropdown(
        self,
        key: str,
        labels: list,
        values: list,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> QComboBox:
        combobox = QComboBox()
        combobox.insertItems(0, labels)
        if tooltip is not None:
            combobox.setToolTip(tooltip)

        def update() -> None:
            conf = self.conf
            try:
                val = conf.get(key)
                index = values.index(val)
            except ValueError:
                raise InvalidConfigValueError(
                    key, "any value in list " + str(values), val
                )
            combobox.setCurrentIndex(index)

        self.widget_updates.append(update)

        combobox.currentIndexChanged.connect(
            lambda idx: self.conf.set(key, values[idx])
        )

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(combobox)
            row.stretch()
        else:
            self.addWidget(combobox)

        return combobox

    def text_input(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QLineEdit:
        "For string config"
        line_edit = QLineEdit()
        if tooltip is not None:
            line_edit.setToolTip(tooltip)

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "string", val)
            line_edit.setText(val)
            line_edit.setCursorPosition(0)

        self.widget_updates.append(update)

        line_edit.textChanged.connect(lambda text: self.conf.set(key, text))

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(line_edit)
        else:
            self.addWidget(line_edit)
        return line_edit

    def number_input(
        self,
        key: str,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
        minimum: int = 0,
        maximum: int = 99,
        step: int = 1,
        decimal: bool = False,
        precision: int = 2,
    ) -> QAbstractSpinBox:
        "For integer config"
        spin_box: QAbstractSpinBox
        if decimal:
            spin_box = QDoubleSpinBox()
            spin_box.setDecimals(precision)
        else:
            spin_box = QSpinBox()
        if tooltip is not None:
            spin_box.setToolTip(tooltip)
        spin_box.setMinimum(minimum)
        spin_box.setMaximum(maximum)
        spin_box.setSingleStep(step)

        def update() -> None:
            val = self.conf.get(key)
            if not decimal and not isinstance(val, int):
                raise InvalidConfigValueError(key, "integer number", val)
            if decimal and not isinstance(val, (int, float)):
                raise InvalidConfigValueError(key, "number", val)
            if minimum is not None and val < minimum:
                raise InvalidConfigValueError(
                    key, f"integer number greater or equal to {minimum}", val
                )
            if maximum is not None and val > maximum:
                raise InvalidConfigValueError(
                    key, f"integer number lesser or equal to {maximum}", val
                )
            spin_box.setValue(val)

        self.widget_updates.append(update)

        spin_box.valueChanged.connect(lambda val: self.conf.set(key, val))

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(spin_box)
            row.stretch()
        else:
            self.addWidget(spin_box)
        return spin_box

    def color_input(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QPushButton:
        "For hex color config"
        button = QPushButton()
        button.setFixedWidth(25)
        button.setFixedHeight(25)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        if tooltip is not None:
            button.setToolTip(tooltip)

        color_dialog = QColorDialog(self.config_window)

        def set_color(rgb: str) -> None:
            button.setStyleSheet(
                'QPushButton{ background-color: "%s"; border: none; border-radius: 3px}'
                % rgb
            )
            color = QColor()
            color.setNamedColor(rgb)
            if not color.isValid():
                raise InvalidConfigValueError(key, "rgb hex color string", rgb)
            color_dialog.setCurrentColor(color)

        def update() -> None:
            value = self.conf.get(key)
            set_color(value)

        def save(color: QColor) -> None:
            rgb = color.name(QColor.HexRgb)
            self.conf.set(key, rgb)
            set_color(rgb)

        self.widget_updates.append(update)
        color_dialog.colorSelected.connect(lambda color: save(color))
        button.clicked.connect(lambda _: color_dialog.exec_())

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(button)
            row.stretch()
        else:
            self.addWidget(button)

        return button

    def path_input(
        self,
        key: str,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
        get_directory: bool = False,
        filter: str = "Any files (*)",
    ) -> Tuple[QLineEdit, QPushButton]:
        "For path string config"

        row = self.hlayout()
        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        row.addWidget(line_edit)
        button = QPushButton("Browse")
        row.addWidget(button)
        if tooltip is not None:
            line_edit.setToolTip(tooltip)

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "string file path", val)
            line_edit.setText(val)

        def get_path() -> None:
            val = self.conf.get(key)
            parent_dir = str(Path(val).parent)

            if get_directory:
                path = QFileDialog.getExistingDirectory(
                    self.config_window, directory=parent_dir
                )
            else:
                path = QFileDialog.getOpenFileName(
                    self.config_window, directory=parent_dir, filter=filter
                )[0]
            if path:  # is None if cancelled
                self.conf.set(key, path)
                update()

        self.widget_updates.append(update)
        button.clicked.connect(get_path)

        return (line_edit, button)

    # Layout widgets

    def space(self, space: int = 1) -> None:
        self.addSpacing(space)

    def stretch(self, factor: int = 0) -> None:
        self.addStretch(factor)

    def hlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.LeftToRight)
        self.addLayout(layout)
        return layout

    def vlayout(self) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.TopToBottom)
        self.addLayout(layout)
        return layout

    def scroll_layout(
        self, horizontal: bool = True, vertical: bool = True
    ) -> "ConfigLayout":
        layout = ConfigLayout(self, QBoxLayout.TopToBottom)
        inner_widget = QWidget()
        inner_widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner_widget)
        scroll.setSizePolicy(
            QSizePolicy.Expanding if horizontal else QSizePolicy.Minimum,
            QSizePolicy.Expanding if vertical else QSizePolicy.Minimum,
        )
        self.addWidget(scroll)
        return layout
