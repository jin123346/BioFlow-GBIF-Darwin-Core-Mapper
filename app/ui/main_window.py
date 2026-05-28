from pathlib import Path
import json

import pandas as pd

from PySide6.QtCore import QSettings, Qt
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.app_info import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    AUTHOR_EMAIL,
    AUTHOR_GITHUB,
    AUTHOR_NAME,
    COPYRIGHT_TEXT,
)
from app.config.country_code import ISO_COUNTRY_CODES
from app.config.auto_mapping import (
    CUSTOM_AUTO_MAPPING_PATH,
    get_default_auto_mapping_rules,
    load_auto_mapping_rules,
    reset_auto_mapping_rules,
    save_auto_mapping_rules,
)
from app.config.dwc_fields import (
    ALL_DWC_FIELDS,
    get_default_dwc_fields,
    get_dwc_field,
    get_optional_dwc_fields,
)
from app.services.excel_service import ExcelService
from app.services.mapping_service import MappingService, auto_match_column
from app.ui.paste_table_widget import PasteTableWidget
from app.utils.paths import LOGO_PATH, OUTPUT_DIR


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {APP_SUBTITLE}")
        self.resize(1280, 820)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))

        self.raw_df = None
        self.source_df = None
        self.result_df = None
        self.current_file_path = None
        self.current_sheet_name = None
        self.selected_header_row = None
        self.settings = QSettings(AUTHOR_NAME, APP_NAME)
        self.active_field_keys = [field["key"] for field in get_default_dwc_fields()]
        self.combo_boxes = {}
        self.manual_inputs = {}

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(14, 10, 14, 10)
        control_layout.setSpacing(8)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.btn_upload = QPushButton("파일 업로드")
        self.btn_upload.setProperty("role", "primary")
        self.btn_upload.clicked.connect(self.load_excel)

        self.btn_apply_header = QPushButton("선택 행을 헤더로 적용")
        self.btn_apply_header.setProperty("role", "secondary")
        self.btn_apply_header.clicked.connect(self.apply_selected_header)
        self.btn_apply_header.setEnabled(False)

        self.btn_add_field = QPushButton("컬럼 추가")
        self.btn_add_field.setProperty("role", "secondary")
        self.btn_add_field.clicked.connect(self.add_optional_field)
        self.btn_add_field.setEnabled(False)

        self.btn_source_coordinate_preview = QPushButton("원본 좌표 확인")
        self.btn_source_coordinate_preview.setProperty("role", "secondary")
        self.btn_source_coordinate_preview.clicked.connect(self.preview_source_coordinates_on_map)
        self.btn_source_coordinate_preview.setEnabled(False)

        self.btn_preview_result = QPushButton("결과 확인")
        self.btn_preview_result.setProperty("role", "primary")
        self.btn_preview_result.clicked.connect(self.preview_mapped_result)
        self.btn_preview_result.setEnabled(False)

        self.btn_coordinate_preview = QPushButton("좌표 확인")
        self.btn_coordinate_preview.setProperty("role", "secondary")
        self.btn_coordinate_preview.clicked.connect(self.preview_coordinates_on_map)
        self.btn_coordinate_preview.setEnabled(False)

        self.btn_export = QPushButton("매핑 결과 엑셀 저장")
        self.btn_export.setProperty("role", "success")
        self.btn_export.clicked.connect(self.export_mapped_excel)
        self.btn_export.setEnabled(False)

        self.btn_about = QPushButton("정보")
        self.btn_about.setProperty("role", "secondary")
        self.btn_about.clicked.connect(self.show_about)

        self.lbl_file = QLabel("업로드된 파일 없음")
        self.lbl_file.setObjectName("metaValue")

        self.lbl_sheet = QLabel("선택된 시트 없음")
        self.lbl_sheet.setObjectName("metaValue")

        self.lbl_header = QLabel("선택된 헤더 행: 없음")
        self.lbl_header.setObjectName("metaValueAccent")

        button_layout.addWidget(self.btn_upload)
        button_layout.addWidget(self.btn_apply_header)
        button_layout.addWidget(self.btn_add_field)
        button_layout.addWidget(self.btn_source_coordinate_preview)
        button_layout.addWidget(self.btn_preview_result)
        button_layout.addWidget(self.btn_coordinate_preview)
        button_layout.addWidget(self.btn_export)
        button_layout.addWidget(self.btn_about)
        button_layout.addStretch()

        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        status_layout.addWidget(self._build_meta_block("파일", self.lbl_file))
        status_layout.addWidget(self._build_meta_block("시트", self.lbl_sheet))
        status_layout.addWidget(self._build_meta_block("헤더 상태", self.lbl_header))
        status_layout.addStretch()

        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        logo_label = QLabel()
        logo_label.setObjectName("appLogo")
        logo_label.setFixedSize(74, 54)
        logo_label.setAlignment(Qt.AlignCenter)
        if LOGO_PATH.exists():
            logo_pixmap = QPixmap(str(LOGO_PATH))
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    logo_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        logo_label.setVisible(LOGO_PATH.exists())

        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(2)

        app_title = QLabel(APP_NAME)
        app_title.setObjectName("appTitle")

        app_subtitle = QLabel(APP_SUBTITLE)
        app_subtitle.setObjectName("appSubtitle")

        title_text_layout.addWidget(app_title)
        title_text_layout.addWidget(app_subtitle)
        title_layout.addWidget(logo_label)
        title_layout.addLayout(title_text_layout)
        title_layout.addSpacing(18)
        title_layout.addLayout(button_layout)
        title_layout.addStretch()

        control_layout.addLayout(title_layout)
        control_layout.addLayout(status_layout)
        root_layout.addWidget(control_panel)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(
            self._build_section_header(
                "원본 엑셀 미리보기",
                "행을 클릭해서 실제 헤더로 사용할 줄을 고르세요.",
            )
        )

        self.preview_position_label = QLabel("현재 선택 위치: 없음")
        self.preview_position_label.setObjectName("metaValueAccent")
        left_layout.addWidget(self.preview_position_label)

        self.preview_table = QTableWidget()
        self.preview_table.cellClicked.connect(self.select_header_row)
        self._configure_table(self.preview_table)
        self.preview_table.verticalHeader().setVisible(True)
        self.preview_table.verticalHeader().setDefaultSectionSize(28)
        left_layout.addWidget(self.preview_table)

        right_panel = QWidget()
        right_panel.setMinimumWidth(620)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        workspace_splitter = QSplitter(Qt.Vertical)
        workspace_splitter.setChildrenCollapsible(False)

        mapping_panel = QWidget()
        mapping_panel_layout = QVBoxLayout(mapping_panel)
        mapping_panel_layout.setContentsMargins(0, 0, 0, 0)
        mapping_panel_layout.setSpacing(10)
        mapping_panel_layout.addWidget(
            self._build_section_header(
                "GBIF 필드 매핑",
                "기본 필드를 먼저 보여주고, 필요하면 컬럼 추가로 더 넣을 수 있습니다.",
            )
        )

        self.mapping_summary = QLabel("현재 0개 필드")
        self.mapping_summary.setObjectName("metaValue")
        mapping_panel_layout.addWidget(self.mapping_summary)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.mapping_container = QWidget()
        self.mapping_layout = QVBoxLayout(self.mapping_container)
        self.mapping_layout.setContentsMargins(0, 0, 0, 0)
        self.mapping_layout.setSpacing(10)
        self.mapping_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.mapping_container)
        mapping_panel_layout.addWidget(self.scroll_area)

        result_panel = QWidget()
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(10)
        result_layout.addWidget(
            self._build_section_header(
                "변환 결과 미리보기",
                "추가한 GBIF 필드도 결과 테이블과 저장 엑셀에 함께 포함됩니다.",
            )
        )

        self.result_table = PasteTableWidget()
        self.result_table.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed
        )
        self._configure_table(self.result_table)
        self.result_table.verticalHeader().setVisible(True)
        self.result_table.verticalHeader().setDefaultSectionSize(30)
        result_layout.addWidget(self.result_table)

        self.missing_summary_card = QFrame()
        self.missing_summary_card.setProperty("class", "sectionCard")
        self.missing_summary_card.setMinimumHeight(92)
        self.missing_summary_card.setMaximumHeight(110)
        missing_layout = QVBoxLayout(self.missing_summary_card)
        missing_layout.setContentsMargins(16, 14, 16, 14)
        missing_layout.setSpacing(6)

        self.missing_summary_title = QLabel("빈칸 점검")
        self.missing_summary_title.setProperty("class", "sectionTitle")

        self.missing_summary_label = QLabel("결과 확인 후 빈칸 요약이 여기에 표시됩니다.")
        self.missing_summary_label.setWordWrap(True)
        self.missing_summary_label.setProperty("class", "sectionDescription")
        self.missing_summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.missing_summary_scroll = QScrollArea()
        self.missing_summary_scroll.setWidgetResizable(True)
        self.missing_summary_scroll.setFrameShape(QFrame.NoFrame)
        self.missing_summary_scroll.setMinimumHeight(44)
        self.missing_summary_scroll.setMaximumHeight(54)

        self.missing_summary_content = QWidget()
        self.missing_summary_content_layout = QVBoxLayout(self.missing_summary_content)
        self.missing_summary_content_layout.setContentsMargins(0, 0, 0, 0)
        self.missing_summary_content_layout.setSpacing(4)
        self.missing_summary_content_layout.addWidget(self.missing_summary_label)
        self.missing_summary_scroll.setWidget(self.missing_summary_content)

        missing_layout.addWidget(self.missing_summary_title)
        missing_layout.addWidget(self.missing_summary_scroll)
        result_layout.addWidget(self.missing_summary_card)

        workspace_splitter.addWidget(mapping_panel)
        workspace_splitter.addWidget(result_panel)
        workspace_splitter.setStretchFactor(0, 5)
        workspace_splitter.setStretchFactor(1, 5)
        workspace_splitter.setSizes([360, 360])

        self.main_tabs = QTabWidget()

        mapping_tab = QWidget()
        mapping_tab_layout = QVBoxLayout(mapping_tab)
        mapping_tab_layout.setContentsMargins(0, 0, 0, 0)
        mapping_tab_layout.addWidget(workspace_splitter)

        self.main_tabs.addTab(mapping_tab, "매핑 작업")
        self.main_tabs.addTab(self._build_auto_mapping_settings_tab(), "자동 매핑 설정")

        right_layout.addWidget(self.main_tabs)

        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 4)
        content_splitter.setStretchFactor(1, 9)
        content_splitter.setSizes([330, 900])

        root_layout.addWidget(content_splitter)
        root_layout.setStretchFactor(content_splitter, 1)

        footer_label = QLabel(f"{APP_NAME} v{APP_VERSION} · {COPYRIGHT_TEXT}")
        footer_label.setObjectName("footerCredit")
        footer_label.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(footer_label)

        self.setStyleSheet(
            """
            QMainWindow {
                background: #eef3f7;
            }
            QWidget {
                color: #1e293b;
                font-family: "Segoe UI", "Malgun Gothic", sans-serif;
                font-size: 12px;
            }
            QFrame#controlPanel {
                background: #fbfdff;
                border: 1px solid #d6e0ea;
                border-radius: 12px;
            }
            QLabel#appTitle {
                color: #102a43;
                font-size: 19px;
                font-weight: 800;
            }
            QLabel#appSubtitle {
                color: #52667a;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#footerCredit {
                color: #8a9aab;
                font-size: 10px;
                font-weight: 600;
                padding: 0px;
            }
            QWidget[class="metaBlock"] {
                background: #f5f8fb;
                border: 1px solid #e0e7ef;
                border-radius: 8px;
            }
            QFrame[class="sectionCard"] {
                background: #fbfdff;
                border: 1px solid #d8e2ec;
                border-radius: 10px;
            }
            QLabel[class="sectionTitle"] {
                font-size: 15px;
                font-weight: 700;
                color: #132f4c;
            }
            QLabel[class="sectionDescription"] {
                color: #64758a;
                font-size: 12px;
            }
            QLabel[class="metaLabel"] {
                color: #718096;
                font-size: 10px;
                font-weight: 700;
            }
            QLabel#metaValue {
                color: #26384c;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#metaValueAccent {
                color: #0f766e;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton {
                background: #ffffff;
                color: #244158;
                border: 1px solid #cdd8e4;
                border-radius: 8px;
                padding: 7px 13px;
                font-weight: 700;
                min-height: 18px;
            }
            QPushButton[role="primary"] {
                background: #123a55;
                color: #ffffff;
                border: none;
            }
            QPushButton[role="success"] {
                background: #0f766e;
                color: #ffffff;
                border: none;
            }
            QPushButton[role="secondary"] {
                background: #ffffff;
                color: #244158;
                border: 1px solid #c9d6e2;
            }
            QPushButton[role="link"] {
                background: transparent;
                color: #0f766e;
                border: none;
                border-radius: 4px;
                padding: 2px 0px;
                font-weight: 700;
                text-align: left;
                min-height: 16px;
            }
            QPushButton:disabled {
                background: #e3e9f0;
                color: #93a3b5;
                border: 1px solid #d5dee8;
            }
            QPushButton:hover:!disabled {
                background: #eaf2f8;
                border: 1px solid #b6cadb;
            }
            QPushButton[role="primary"]:hover:!disabled {
                background: #174a6d;
                border: none;
            }
            QPushButton[role="success"]:hover:!disabled {
                background: #0d9488;
                border: none;
            }
            QScrollArea, QTableWidget {
                background: #fbfdff;
                border: 1px solid #d7e1ec;
                border-radius: 10px;
            }
            QTableWidget {
                alternate-background-color: #f6f9fc;
                gridline-color: #e2e8f0;
                selection-background-color: #dff3ef;
                selection-color: #102a43;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #edf2f7;
            }
            QTableWidget::item:selected {
                background: #dff3ef;
                color: #102a43;
            }
            QHeaderView::section {
                background: #edf4f8;
                color: #28445d;
                border: none;
                border-right: 1px solid #d7e1ec;
                border-bottom: 1px solid #d7e1ec;
                padding: 9px;
                font-weight: 700;
            }
            QFrame[frameShape="6"] {
                background: #fbfdff;
                border: 1px solid #dde6ef;
                border-radius: 10px;
            }
            QFrame[class="mappingCard"] {
                background: #ffffff;
                border: 1px solid #dbe5ee;
                border-radius: 8px;
            }
            QLabel[class="fieldName"] {
                color: #172b4d;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel[class="fieldDescription"] {
                color: #64748b;
                font-size: 11px;
            }
            QComboBox, QLineEdit {
                border: 1px solid #cbd8e5;
                border-radius: 8px;
                padding: 8px 10px;
                background: #ffffff;
                color: #20364d;
                min-height: 20px;
            }
            QComboBox:hover, QLineEdit:hover {
                border: 1px solid #95adbf;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 1px solid #0f766e;
                background: #fbfffe;
            }
            QComboBox[autoMatched="true"] {
                background: #ecfdf5;
                border: 1px solid #8bd4bd;
                color: #0f5132;
            }
            QSplitter::handle {
                background: #dde7ef;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background: #b9cad8;
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #e5edf4;
                color: #52667a;
                border: 1px solid #ccd8e3;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #fbfdff;
                color: #123a55;
            }
            QScrollBar:vertical {
                background: #f2f6fa;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #b9c7d5;
                border-radius: 6px;
                min-height: 26px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #f2f6fa;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #b9c7d5;
                border-radius: 6px;
                min-width: 26px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            """
        )

        self._update_mapping_summary()

    def _build_meta_block(self, title: str, value_label: QLabel) -> QWidget:
        wrapper = QWidget()
        wrapper.setProperty("class", "metaBlock")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(9, 4, 9, 4)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setProperty("class", "metaLabel")
        value_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        return wrapper

    def _build_section_header(self, title: str, description: str) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "sectionCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setProperty("class", "sectionTitle")

        desc_label = QLabel(description)
        desc_label.setProperty("class", "sectionDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        return frame

    def _build_auto_mapping_settings_tab(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(
            self._build_section_header(
                "자동 매핑 설정",
                "원본 파일의 컬럼명이 아래 후보 이름을 포함하면 해당 GBIF 필드로 자동 선택됩니다. 여러 이름은 쉼표로 구분하세요.",
            )
        )

        self.auto_mapping_path_label = QLabel(f"설정 파일: {CUSTOM_AUTO_MAPPING_PATH}")
        self.auto_mapping_path_label.setObjectName("metaValue")
        self.auto_mapping_path_label.setWordWrap(True)
        layout.addWidget(self.auto_mapping_path_label)

        self.auto_mapping_table = QTableWidget()
        self.auto_mapping_table.setColumnCount(2)
        self.auto_mapping_table.setHorizontalHeaderLabels(
            ["GBIF 필드", "후보 컬럼명"]
        )
        self.auto_mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.auto_mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.auto_mapping_table.verticalHeader().setVisible(False)
        self.auto_mapping_table.setAlternatingRowColors(True)
        layout.addWidget(self.auto_mapping_table)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.btn_reload_auto_mapping = QPushButton("다시 불러오기")
        self.btn_reload_auto_mapping.setProperty("role", "secondary")
        self.btn_reload_auto_mapping.clicked.connect(self.load_auto_mapping_settings)

        self.btn_reset_auto_mapping = QPushButton("기본값으로 초기화")
        self.btn_reset_auto_mapping.setProperty("role", "secondary")
        self.btn_reset_auto_mapping.clicked.connect(self.reset_auto_mapping_settings)

        self.btn_save_auto_mapping = QPushButton("자동 매핑 설정 저장")
        self.btn_save_auto_mapping.setProperty("role", "primary")
        self.btn_save_auto_mapping.clicked.connect(self.save_auto_mapping_settings)

        button_layout.addWidget(self.btn_reload_auto_mapping)
        button_layout.addWidget(self.btn_reset_auto_mapping)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_save_auto_mapping)
        layout.addLayout(button_layout)

        self.load_auto_mapping_settings()
        return panel

    def load_auto_mapping_settings(self):
        try:
            rules = load_auto_mapping_rules()
        except Exception as e:
            QMessageBox.warning(
                self,
                "자동 매핑 설정",
                f"자동 매핑 설정을 불러오지 못했습니다.\n기본값으로 표시합니다.\n\n{e}",
            )
            rules = get_default_auto_mapping_rules()

        self.auto_mapping_table.setRowCount(len(ALL_DWC_FIELDS))

        for row, field in enumerate(ALL_DWC_FIELDS):
            key_item = QTableWidgetItem(field["key"])
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.auto_mapping_table.setItem(row, 0, key_item)

            keywords = ", ".join(rules.get(field["key"], []))
            self.auto_mapping_table.setItem(row, 1, QTableWidgetItem(keywords))

        self.auto_mapping_table.resizeRowsToContents()

    def _rules_from_auto_mapping_table(self) -> dict[str, list[str]]:
        rules = {}
        for row in range(self.auto_mapping_table.rowCount()):
            key_item = self.auto_mapping_table.item(row, 0)
            value_item = self.auto_mapping_table.item(row, 1)
            if key_item is None:
                continue

            key = key_item.text().strip()
            value = value_item.text() if value_item is not None else ""
            rules[key] = [keyword.strip() for keyword in value.split(",") if keyword.strip()]

        return rules

    def save_auto_mapping_settings(self):
        try:
            save_auto_mapping_rules(self._rules_from_auto_mapping_table())

            if self.source_df is not None:
                self.build_mapping_ui(self.source_df.columns.tolist())
                self.btn_coordinate_preview.setEnabled(False)
                self.btn_export.setEnabled(False)

            QMessageBox.information(
                self,
                "저장 완료",
                f"자동 매핑 설정을 저장했습니다.\n\n{CUSTOM_AUTO_MAPPING_PATH}",
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"자동 매핑 설정 저장 중 오류가 발생했습니다.\n\n{e}")

    def reset_auto_mapping_settings(self):
        reply = QMessageBox.question(
            self,
            "기본값으로 초기화",
            "로컬 자동 매핑 설정을 삭제하고 기본값으로 되돌릴까요?",
        )
        if reply != QMessageBox.Yes:
            return

        try:
            reset_auto_mapping_rules()
            self.load_auto_mapping_settings()

            if self.source_df is not None:
                self.build_mapping_ui(self.source_df.columns.tolist())
                self.btn_coordinate_preview.setEnabled(False)
                self.btn_export.setEnabled(False)

            QMessageBox.information(self, "초기화 완료", "자동 매핑 설정을 기본값으로 되돌렸습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"자동 매핑 설정 초기화 중 오류가 발생했습니다.\n\n{e}")

    def _configure_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectItems)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setWordWrap(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setMinimumSectionSize(110)
        table.setShowGrid(False)

    def _get_active_fields(self) -> list[dict]:
        return [get_dwc_field(key) for key in self.active_field_keys]

    def _update_mapping_summary(self):
        self.mapping_summary.setText(f"현재 {len(self.active_field_keys)}개 필드")

    def show_about(self):
        lines = [
            f"<h3>{APP_NAME}</h3>",
            f"<p>Version {APP_VERSION} · {APP_SUBTITLE}</p>",
            f"<p><b>Made by {AUTHOR_NAME}</b></p>",
            f"<p>{COPYRIGHT_TEXT}</p>",
        ]

        if AUTHOR_EMAIL:
            lines.append(
                f'<p>email: '
                f'<a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a></p>'
            )
        else:
            lines.append("<p>문의사항은 이메일로 문의해주세요.</p>")

        if AUTHOR_GITHUB:
            lines.append(f'<p>GitHub: <a href="{AUTHOR_GITHUB}">{AUTHOR_GITHUB}</a></p>')
        
        lines.append( f'<p>문의사항은 이메일로 문의해주세요!')

        message = QMessageBox(self)
        message.setWindowTitle("정보")
        message.setTextFormat(Qt.RichText)
        message.setText("\n".join(lines))
        message.exec()

    def _snapshot_mapping_state(self) -> tuple[dict, dict]:
        combo_state = {}
        manual_state = {}

        for key, combo in self.combo_boxes.items():
            try:
                combo_state[key] = combo.currentText()
            except RuntimeError:
                continue

        for key, widget in self.manual_inputs.items():
            try:
                manual_state[key] = widget.text()
            except RuntimeError:
                continue

        return combo_state, manual_state

    def _restore_mapping_state(self, combo_state: dict, manual_state: dict):
        for key, value in combo_state.items():
            combo = self.combo_boxes.get(key)
            if combo and value:
                index = combo.findText(value)
                if index >= 0:
                    combo.setCurrentIndex(index)
                else:
                    combo.setCurrentText(value)

        for key, value in manual_state.items():
            line_edit = self.manual_inputs.get(key)
            if line_edit is not None:
                line_edit.setText(value)

    def _reset_active_fields(self):
        self.active_field_keys = [field["key"] for field in get_default_dwc_fields()]
        self._update_mapping_summary()

    def _get_last_open_dir(self) -> str:
        last_dir = self.settings.value("file_dialog/last_open_dir", "", str)
        if last_dir and Path(last_dir).is_dir():
            return last_dir
        return ""

    def _remember_open_dir(self, file_path: str) -> None:
        parent_dir = Path(file_path).expanduser().parent
        if parent_dir.is_dir():
            self.settings.setValue("file_dialog/last_open_dir", str(parent_dir))

    def _get_last_save_dir(self) -> str:
        last_dir = self.settings.value("file_dialog/last_save_dir", "", str)
        if last_dir and Path(last_dir).is_dir():
            return last_dir
        return str(OUTPUT_DIR)

    def _remember_save_dir(self, file_path: str) -> None:
        parent_dir = Path(file_path).expanduser().parent
        if parent_dir.is_dir():
            self.settings.setValue("file_dialog/last_save_dir", str(parent_dir))

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "파일 선택",
            self._get_last_open_dir(),
            "Excel/CSV Files (*.xlsx *.xls *.csv)",
        )
        if not file_path:
            return
        self._remember_open_dir(file_path)

        try:
            sheet_names = ExcelService.get_sheet_names(file_path)
            if not sheet_names:
                raise ValueError("시트가 없는 엑셀 파일입니다.")

            selected_sheet, ok = QInputDialog.getItem(
                self,
                "시트 선택",
                "불러올 시트를 선택하세요:",
                sheet_names,
                0,
                False,
            )
            if not ok or not selected_sheet:
                return

            raw_df = ExcelService.read_excel_raw(file_path, sheet_name=selected_sheet)
            # 파일 초기화
            self._set_loaded_file_state(file_path,selected_sheet,raw_df)

            # UI 초기화(라벨 갱신)
            self._update_loaded_file_labels(self,file_path, sheet_name=selected_sheet)
        
                
            self.show_preview_raw(self.raw_df)
            self.clear_mapping_ui()
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self.reset_missing_summary_panel()
            
            # 버튼 상태 초기화
            self._set_file_loaded_buttons_enabled(self)


        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일을 불러오지 못했습니다.\n\n{e}")
            
    
    # 파일을 새로 불러올 때마다 관련 상태를 초기화하는 메서드
    def _set_loaded_file_state(self, file_path, sheet_name, raw_df):
        self.raw_df = raw_df
        self.current_file_path = file_path
        self.current_sheet_name = sheet_name
        self.source_df = None
        self.result_df = None
        self.selected_header_row = None
        self._reset_active_fields()
    
    
    def _update_loaded_file_labels(self, file_path, sheet_name):
        self.lbl_file.setText(f"파일: {Path(file_path).name}")
        self.lbl_sheet.setText(sheet_name)
        self.lbl_header.setText("선택된 헤더 행: 없음")
        self.preview_position_label.setText("현재 선택 위치: 없음")
        
    
    def _set_file_loaded_buttons_enabled(self):
        self.btn_apply_header.setEnabled(True)
        self.btn_add_field.setEnabled(False)
        self.btn_source_coordinate_preview.setEnabled(False)
        self.btn_preview_result.setEnabled(False)
        self.btn_coordinate_preview.setEnabled(False)
        self.btn_export.setEnabled(False)
    
    def show_preview_raw(self, df):
        preview_df = df

        self.preview_table.clear()
        self.preview_table.setRowCount(len(preview_df))
        self.preview_table.setColumnCount(len(preview_df.columns))
        self.preview_table.setHorizontalHeaderLabels(
            [f"Column {i + 1}" for i in range(len(preview_df.columns))]
        )

        for row_idx in range(len(preview_df)):
            for col_idx in range(len(preview_df.columns)):
                value = preview_df.iloc[row_idx, col_idx]
                self.preview_table.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem("" if value is None else str(value)),
                )

        self.preview_table.resizeColumnsToContents()
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def show_preview_with_header(self, df):
        preview_df = df

        self.preview_table.clear()
        self.preview_table.setRowCount(len(preview_df))
        self.preview_table.setColumnCount(len(preview_df.columns))
        self.preview_table.setHorizontalHeaderLabels([str(col) for col in preview_df.columns.tolist()])

        for row_idx in range(len(preview_df)):
            for col_idx, _ in enumerate(preview_df.columns):
                value = preview_df.iloc[row_idx, col_idx]
                self.preview_table.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem("" if value is None else str(value)),
                )

        self.preview_table.resizeColumnsToContents()
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def select_header_row(self, row, col):
        if self.raw_df is None:
            return

        self.selected_header_row = row
        self.lbl_header.setText(f"선택된 헤더 행: {row + 1}행")
        self.preview_position_label.setText(
            f"현재 선택 위치: {row + 1}행, {col + 1}열"
        )
        self.highlight_selected_row(row)

    def highlight_selected_row(self, row):
        for r in range(self.preview_table.rowCount()):
            for c in range(self.preview_table.columnCount()):
                item = self.preview_table.item(r, c)
                if item:
                    item.setBackground(QColor("#fff4bf") if r == row else QColor("#ffffff"))

    def apply_selected_header(self):
        if self.current_file_path is None or self.raw_df is None:
            QMessageBox.warning(self, "경고", "먼저 엑셀 파일을 업로드해주세요.")
            return

        if self.selected_header_row is None:
            QMessageBox.warning(self, "경고", "헤더로 사용할 행을 먼저 클릭하세요.")
            return

        try:
            self.source_df = ExcelService.read_excel_with_header(
                self.current_file_path,
                header_row=self.selected_header_row,
                sheet_name=self.current_sheet_name,
            )

            cleaned_columns = []
            for idx, col in enumerate(self.source_df.columns):
                col_text = str(col).strip()
                if not col_text or col_text.lower().startswith("unnamed:"):
                    col_text = f"Column_{idx + 1}"
                cleaned_columns.append(col_text)

            self.source_df.columns = cleaned_columns
            self.show_preview_with_header(self.source_df)
            self.preview_position_label.setText(
                f"현재 선택 위치: {self.selected_header_row + 1}행 (헤더 적용됨, 열 선택은 마지막 클릭 기준)"
            )
            self.build_mapping_ui(self.source_df.columns.tolist())
            self.btn_add_field.setEnabled(True)
            self.btn_source_coordinate_preview.setEnabled(True)
            self.btn_preview_result.setEnabled(True)
            self.btn_coordinate_preview.setEnabled(False)
            self.btn_export.setEnabled(False)

            QMessageBox.information(
                self,
                "완료",
                f"{self.selected_header_row + 1}행을 헤더로 적용했습니다.",
            )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"헤더 적용 중 오류가 발생했습니다.\n\n{e}")

    def add_optional_field(self):
        if self.source_df is None:
            QMessageBox.warning(self, "경고", "헤더를 먼저 적용해주세요.")
            return

        optional_fields = get_optional_dwc_fields(self.active_field_keys)
        if not optional_fields:
            QMessageBox.information(self, "안내", "추가할 수 있는 GBIF 컬럼이 더 없습니다.")
            return

        display_items = [
            f'{field["label"]} - {field["description"]}'
            for field in optional_fields
        ]
        field_by_display = {
            f'{field["label"]} - {field["description"]}': field
            for field in optional_fields
        }

        selected_display, ok = QInputDialog.getItem(
            self,
            "컬럼 추가",
            "추가할 GBIF 컬럼을 선택하세요:",
            display_items,
            0,
            False,
        )
        if not ok or not selected_display:
            return

        selected_field = field_by_display[selected_display]
        self.active_field_keys.append(selected_field["key"])

        combo_state, manual_state = self._snapshot_mapping_state()
        self.build_mapping_ui(self.source_df.columns.tolist(), combo_state, manual_state)
        self.btn_coordinate_preview.setEnabled(False)
        self.btn_export.setEnabled(False)

    def build_mapping_ui(
        self,
        source_columns: list[str],
        combo_state: dict | None = None,
        manual_state: dict | None = None,
    ):
        self.clear_mapping_ui()

        for field in self._get_active_fields():
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setProperty("class", "mappingCard")

            row_layout = QHBoxLayout(frame)
            row_layout.setContentsMargins(16, 13, 16, 13)
            row_layout.setSpacing(16)

            label_layout = QVBoxLayout()
            label_layout.setSpacing(4)

            lbl_name = QLabel(field["label"])
            lbl_name.setProperty("class", "fieldName")

            lbl_desc = QLabel(field["description"])
            lbl_desc.setWordWrap(True)
            lbl_desc.setProperty("class", "fieldDescription")

            label_layout.addWidget(lbl_name)
            label_layout.addWidget(lbl_desc)

            if field["key"] == "basisOfRecord":
                combo = QComboBox()
                combo.setMinimumWidth(300)
                combo.addItems(
                    [
                        "",
                        "HumanObservation",
                        "MachineObservation",
                        "PreservedSpecimen",
                        "LivingSpecimen",
                        "MaterialSample",
                    ]
                )
                row_layout.addLayout(label_layout, stretch=3)
                row_layout.addWidget(combo, stretch=2)
                self.combo_boxes[field["key"]] = combo

            elif field["key"] == "collectionCode":
                sub_layout = QVBoxLayout()
                sub_layout.setSpacing(8)

                combo = QComboBox()
                combo.setMinimumWidth(300)
                combo.addItem("")
                combo.addItems([str(col) for col in source_columns])

                line_edit = QLineEdit()
                line_edit.setPlaceholderText("또는 직접 입력 (예: PL)")

                sub_layout.addWidget(combo)
                sub_layout.addWidget(line_edit)
                row_layout.addLayout(label_layout, stretch=3)
                row_layout.addLayout(sub_layout, stretch=2)

                self.combo_boxes[field["key"]] = combo
                self.manual_inputs[field["key"]] = line_edit

            elif field["key"] == "countryCode":
                sub_layout = QVBoxLayout()
                sub_layout.setSpacing(8)

                combo = QComboBox()
                combo.setMinimumWidth(300)
                combo.addItems(ISO_COUNTRY_CODES)
                combo.setToolTip("ISO 3166-1 alpha-2 국가 코드")

                line_edit = QLineEdit()
                line_edit.setPlaceholderText("또는 직접 입력 (예: KR)")
                line_edit.setToolTip("직접 입력값이 있으면 그 값을 우선 사용합니다.")

                sub_layout.addWidget(combo)
                sub_layout.addWidget(line_edit)
                row_layout.addLayout(label_layout, stretch=3)
                row_layout.addLayout(sub_layout, stretch=2)

                self.combo_boxes[field["key"]] = combo
                self.manual_inputs[field["key"]] = line_edit

            else:
                combo = QComboBox()
                combo.setMinimumWidth(300)
                combo.addItem("")
                combo.addItems([str(col) for col in source_columns])

                matched_col = auto_match_column(field["key"], source_columns)
                if matched_col:
                    combo.setCurrentText(matched_col)
                    combo.setProperty("autoMatched", True)

                row_layout.addLayout(label_layout, stretch=3)
                row_layout.addWidget(combo, stretch=2)
                self.combo_boxes[field["key"]] = combo

            self.mapping_layout.addWidget(frame)

        if combo_state or manual_state:
            self._restore_mapping_state(combo_state or {}, manual_state or {})

        self._update_mapping_summary()

    def clear_mapping_ui(self):
        while self.mapping_layout.count():
            item = self.mapping_layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            layout = item.layout()
            if layout is not None:
                self._clear_layout(layout)

        self.combo_boxes.clear()
        self.manual_inputs.clear()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def get_selected_mapping(self) -> dict:
        combo_map = {}

        for dwc_key, combo in self.combo_boxes.items():
            if combo is None:
                continue

            try:
                combo_map[dwc_key] = combo.currentText()
            except RuntimeError:
                continue

        return MappingService.build_mapping(combo_map)

    def export_mapped_excel(self):
        if self.result_df is None:
            QMessageBox.warning(self, "경고", "먼저 '결과 확인'으로 변환 결과를 생성하세요.")
            return

        try:
            final_df = self.get_result_df_from_table()
            if final_df is None:
                QMessageBox.warning(self, "경고", "저장할 결과가 없습니다.")
                return

            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "저장할 파일 경로 선택",
                str(Path(self._get_last_save_dir()) / "dwc_mapped_output.xlsx"),
                "Excel Files (*.xlsx)",
            )

            if not output_path:
                return

            ExcelService.save_excel(final_df, output_path)
            self._remember_save_dir(output_path)
            QMessageBox.information(self, "완료", f"엑셀 파일이 저장되었습니다.\n\n{output_path}")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 저장 중 오류가 발생했습니다.\n\n{e}")

    def _select_coordinate_column(self, title: str, prompt: str, preferred_key: str) -> str | None:
        if self.source_df is None:
            return None

        columns = [str(column) for column in self.source_df.columns.tolist()]
        if not columns:
            return None

        current_index = 0
        matched_column = auto_match_column(preferred_key, columns)
        if matched_column in columns:
            current_index = columns.index(matched_column)

        selected_column, ok = QInputDialog.getItem(
            self,
            title,
            prompt,
            columns,
            current_index,
            False,
        )
        if not ok or not selected_column:
            return None
        return selected_column

    def preview_source_coordinates_on_map(self):
        if self.source_df is None:
            QMessageBox.warning(self, "경고", "먼저 헤더를 적용해 주세요.")
            return

        lat_column = self._select_coordinate_column(
            "원본 좌표 확인",
            "위도 컬럼을 선택하세요:",
            "decimalLatitude",
        )
        if not lat_column:
            return

        lon_column = self._select_coordinate_column(
            "원본 좌표 확인",
            "경도 컬럼을 선택하세요:",
            "decimalLongitude",
        )
        if not lon_column:
            return

        if lat_column == lon_column:
            QMessageBox.warning(self, "경고", "위도와 경도는 서로 다른 컬럼을 선택해 주세요.")
            return

        label_columns = [
            str(column)
            for column in self.source_df.columns.tolist()
            if str(column) not in {lat_column, lon_column}
        ][:8]
        self._preview_coordinate_dataframe(
            self.source_df,
            lat_column,
            lon_column,
            label_columns,
            "원본 좌표 확인",
        )

    def preview_coordinates_on_map(self):
        if self.result_df is None:
            QMessageBox.warning(self, "경고", "먼저 '결과 확인'으로 변환 결과를 생성하세요.")
            return

        final_df = self.get_result_df_from_table()
        if final_df is None or final_df.empty:
            QMessageBox.warning(self, "경고", "확인할 결과 데이터가 없습니다.")
            return

        required_columns = {"decimalLatitude", "decimalLongitude"}
        if not required_columns.issubset(final_df.columns):
            QMessageBox.warning(
                self,
                "좌표 컬럼 없음",
                "decimalLatitude와 decimalLongitude 컬럼이 결과에 있어야 좌표를 확인할 수 있습니다.",
            )
            return

        label_columns = [
            "scientificName",
            "vernacularName",
            "eventDate",
            "locality",
            "verbatimLocality",
            "catalogNumber",
            "occurrenceID",
        ]
        self._preview_coordinate_dataframe(
            final_df,
            "decimalLatitude",
            "decimalLongitude",
            label_columns,
            "좌표 확인",
        )

    def _preview_coordinate_dataframe(
        self,
        df: pd.DataFrame,
        lat_column: str,
        lon_column: str,
        label_columns: list[str],
        dialog_title: str,
    ):
        markers = []
        invalid_coordinates = []

        for idx, row in df.iterrows():
            row_number = int(idx) + 1
            raw_lat = row.get(lat_column)
            raw_lon = row.get(lon_column)
            lat = pd.to_numeric(raw_lat, errors="coerce")
            lon = pd.to_numeric(raw_lon, errors="coerce")
            invalid_reasons = []

            if pd.isna(raw_lat) or str(raw_lat).strip() == "":
                invalid_reasons.append("위도 없음")
            elif pd.isna(lat):
                invalid_reasons.append("위도 숫자 아님")
            elif not (-90 <= lat <= 90):
                invalid_reasons.append("위도 범위 초과")

            if pd.isna(raw_lon) or str(raw_lon).strip() == "":
                invalid_reasons.append("경도 없음")
            elif pd.isna(lon):
                invalid_reasons.append("경도 숫자 아님")
            elif not (-180 <= lon <= 180):
                invalid_reasons.append("경도 범위 초과")

            if invalid_reasons:
                invalid_coordinates.append(
                    {
                        "rowNumber": row_number,
                        "latitude": "" if pd.isna(raw_lat) else str(raw_lat).strip(),
                        "longitude": "" if pd.isna(raw_lon) else str(raw_lon).strip(),
                        "reason": ", ".join(invalid_reasons),
                    }
                )
                continue

            details = []
            for column in label_columns:
                if column not in df.columns:
                    continue
                value = row.get(column)
                if pd.isna(value) or str(value).strip() == "":
                    continue
                details.append({"label": column, "value": str(value).strip()})

            markers.append(
                {
                    "rowNumber": row_number,
                    "lat": float(lat),
                    "lon": float(lon),
                    "details": details,
                }
            )

        map_path = OUTPUT_DIR / "coordinate_preview_map.html"
        invalid_report_path = OUTPUT_DIR / "coordinate_invalid_rows.csv"

        if not markers:
            invalid_message = ""
            if invalid_coordinates:
                try:
                    pd.DataFrame(invalid_coordinates).to_csv(
                        invalid_report_path,
                        index=False,
                        encoding="utf-8-sig",
                    )
                    invalid_message = f"\n\n제외 좌표 목록: {invalid_report_path}"
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"제외 좌표 목록 저장 중 오류가 발생했습니다.\n\n{e}")
                    return
            QMessageBox.warning(
                self,
                "좌표 없음",
                f"지도에 표시할 수 있는 {lat_column} / {lon_column} 값이 없습니다."
                f"{invalid_message}",
            )
            return

        try:
            if invalid_coordinates:
                pd.DataFrame(invalid_coordinates).to_csv(
                    invalid_report_path,
                    index=False,
                    encoding="utf-8-sig",
                )
            map_path.write_text(
                self._coordinate_preview_map_html(markers, invalid_coordinates),
                encoding="utf-8",
            )
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(map_path)))
            invalid_lines = ""
            if invalid_coordinates:
                preview_rows = ", ".join(
                    str(item["rowNumber"]) for item in invalid_coordinates[:20]
                )
                more_count = len(invalid_coordinates) - 20
                if more_count > 0:
                    preview_rows += f" 외 {more_count}개"
                invalid_lines = (
                    f"\n제외된 행: {preview_rows}"
                    f"\n제외 좌표 목록: {invalid_report_path}"
                )
            QMessageBox.information(
                self,
                dialog_title,
                f"좌표 지도 미리보기를 생성했습니다.\n\n{map_path}\n\n"
                f"표시된 좌표: {len(markers)}개\n"
                f"제외된 좌표: {len(invalid_coordinates)}개"
                f"{invalid_lines}",
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"{dialog_title} 중 오류가 발생했습니다.\n\n{e}")

    @staticmethod
    def _coordinate_preview_map_html(markers: list[dict], invalid_coordinates: list[dict]) -> str:
        marker_json = json.dumps(markers, ensure_ascii=False)
        invalid_json = json.dumps(invalid_coordinates[:50], ensure_ascii=False)
        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Coordinate Preview Map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map {{
      height: 100%;
      margin: 0;
    }}
    body {{
      font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    }}
    .summary {{
      background: #ffffff;
      border: 1px solid #d8e2ec;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
      color: #1e293b;
      font-size: 13px;
      line-height: 1.45;
      padding: 10px 12px;
    }}
    .summary strong {{
      display: block;
      font-size: 14px;
      margin-bottom: 4px;
    }}
    .invalid-list {{
      border-top: 1px solid #e2e8f0;
      margin-top: 8px;
      max-height: 180px;
      overflow: auto;
      padding-top: 6px;
    }}
    .invalid-row {{
      margin: 3px 0;
      white-space: nowrap;
    }}
    .popup-title {{
      color: #0f766e;
      font-weight: 800;
      margin-bottom: 6px;
    }}
    .popup-row {{
      margin: 2px 0;
    }}
    .popup-row b {{
      color: #334155;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const markers = {marker_json};
    const invalidCoordinates = {invalid_json};
    const invalidCount = {len(invalid_coordinates)};
    const map = L.map("map");

    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }}).addTo(map);

    const bounds = [];
    const markerLayer = L.layerGroup().addTo(map);
    const escapeHtml = (value) => String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

    markers.forEach((item) => {{
      const position = [item.lat, item.lon];
      bounds.push(position);
      const detailRows = item.details.map((detail) =>
        `<div class="popup-row"><b>${{escapeHtml(detail.label)}}:</b> ${{escapeHtml(detail.value)}}</div>`
      ).join("");
      const popup = `
        <div class="popup-title">Row ${{item.rowNumber}}</div>
        <div class="popup-row"><b>Latitude:</b> ${{item.lat}}</div>
        <div class="popup-row"><b>Longitude:</b> ${{item.lon}}</div>
        ${{detailRows}}
      `;
      L.circleMarker(position, {{
        radius: 7,
        color: "#0f766e",
        fillColor: "#14b8a6",
        fillOpacity: 0.72,
        weight: 2
      }}).bindPopup(popup).addTo(markerLayer);
    }});

    if (bounds.length === 1) {{
      map.setView(bounds[0], 12);
    }} else {{
      map.fitBounds(bounds, {{ padding: [36, 36], maxZoom: 14 }});
    }}

    const summary = L.control({{ position: "topright" }});
    summary.onAdd = function() {{
      const div = L.DomUtil.create("div", "summary");
      const invalidRows = invalidCoordinates.map((item) =>
        `<div class="invalid-row">Row ${{item.rowNumber}}: ${{escapeHtml(item.reason)}}</div>`
      ).join("");
      const moreInvalid = invalidCount > invalidCoordinates.length
        ? `<div class="invalid-row">...and ${{invalidCount - invalidCoordinates.length}} more</div>`
        : "";
      div.innerHTML = `
        <strong>Coordinate Preview</strong>
        Displayed: ${{markers.length}}<br>
        Invalid / blank: ${{invalidCount}}
        ${{invalidCount ? `<div class="invalid-list">${{invalidRows}}${{moreInvalid}}</div>` : ""}}
      `;
      return div;
    }};
    summary.addTo(map);
  </script>
</body>
</html>
"""

    def get_manual_values(self) -> dict:
        values = {}

        for key, widget in self.manual_inputs.items():
            if widget is None:
                continue

            try:
                text = widget.text().strip()
                if text:
                    values[key] = text
            except RuntimeError:
                continue

        return values

    def _get_missing_value_summary(self, df) -> tuple[int, list[str], list[tuple[int, int, str]]]:
        blank_mask = df.fillna("").astype(str).apply(lambda col: col.str.strip() == "")
        missing_counts = blank_mask.sum()
        missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=False)

        if missing_counts.empty:
            return 0, [], []

        total_missing = int(missing_counts.sum())
        summary_lines = ["컬럼별 빈칸 수"]
        summary_lines.extend(
            f"{column}: {int(count)}개 비어 있음"
            for column, count in missing_counts.head(8).items()
        )

        if len(missing_counts) > 8:
            summary_lines.append(f"외 {len(missing_counts) - 8}개 컬럼")

        missing_locations = []
        preview_count = 0
        for row_idx in range(len(df)):
            for col_idx, column in enumerate(df.columns):
                value = df.iat[row_idx, col_idx]
                if pd.isna(value) or str(value).strip() == "":
                    missing_locations.append((row_idx, col_idx, str(column)))
                    preview_count += 1
                    if preview_count >= 12:
                        remaining = total_missing - preview_count
                        if remaining > 0:
                            summary_lines.append(f"외 {remaining}개 위치")
                        return total_missing, summary_lines, missing_locations

        return total_missing, summary_lines, missing_locations

    def _clear_missing_summary_content(self):
        while self.missing_summary_content_layout.count():
            item = self.missing_summary_content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def reset_missing_summary_panel(self):
        self._clear_missing_summary_content()
        self.missing_summary_label = QLabel("결과 확인 후 빈칸 요약이 여기에 표시됩니다.")
        self.missing_summary_label.setWordWrap(True)
        self.missing_summary_label.setProperty("class", "sectionDescription")
        self.missing_summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.missing_summary_content_layout.addWidget(self.missing_summary_label)

    def _update_missing_summary_panel(
        self,
        total_missing: int,
        missing_summary: list[str],
        missing_locations: list[tuple[int, int, str]] | None = None,
    ):
        self._clear_missing_summary_content()

        self.missing_summary_label = QLabel()
        self.missing_summary_label.setWordWrap(True)
        self.missing_summary_label.setProperty("class", "sectionDescription")
        self.missing_summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.missing_summary_content_layout.addWidget(self.missing_summary_label)

        if total_missing > 0:
            self.missing_summary_label.setText(
                "총 빈칸 수: "
                f"{total_missing}개\n"
                + "\n".join(missing_summary)
            )

            if missing_locations:
                heading = QLabel("빈칸 위치 예시")
                heading.setProperty("class", "sectionDescription")
                self.missing_summary_content_layout.addWidget(heading)

                for row_idx, col_idx, column in missing_locations:
                    button = QPushButton(f"{column}: {row_idx + 1}행 {col_idx + 1}열")
                    button.setProperty("role", "link")
                    button.setCursor(Qt.PointingHandCursor)
                    button.clicked.connect(
                        lambda checked=False, r=row_idx, c=col_idx: self.focus_result_cell(r, c)
                    )
                    self.missing_summary_content_layout.addWidget(button)
        else:
            self.missing_summary_label.setText("빈칸 없이 모두 채워져 있습니다.")

        self.missing_summary_content_layout.addStretch()

    def focus_result_cell(self, row_idx: int, col_idx: int):
        if row_idx >= self.result_table.rowCount() or col_idx >= self.result_table.columnCount():
            return

        if hasattr(self, "main_tabs"):
            self.main_tabs.setCurrentIndex(0)

        self.result_table.setFocus()
        self.result_table.clearSelection()
        self.result_table.setCurrentCell(row_idx, col_idx)
        self.result_table.scrollToItem(
            self.result_table.item(row_idx, col_idx),
            QAbstractItemView.PositionAtCenter,
        )

    @staticmethod
    def validate_country_code(code: str) -> bool:
        return len(code) == 2 and code.isalpha()

    def preview_mapped_result(self):
        if self.source_df is None:
            QMessageBox.warning(self, "경고", "헤더를 먼저 적용해주세요.")
            return

        basis_combo = self.combo_boxes.get("basisOfRecord")
        if basis_combo is None or not basis_combo.currentText().strip():
            QMessageBox.warning(self, "경고", "basisOfRecord는 반드시 선택해야 합니다.")
            return

        mapping = self.get_selected_mapping()
        manual_values = self.get_manual_values()
        fixed_values = {"basisOfRecord": basis_combo.currentText().strip()}

        country_manual = manual_values.get("countryCode")
        if country_manual:
            fixed_values["countryCode"] = country_manual
        else:
            combo = self.combo_boxes.get("countryCode")
            if combo:
                try:
                    country_value = combo.currentText().strip()
                    if country_value:
                        fixed_values["countryCode"] = country_value
                except RuntimeError:
                    pass

        for key, value in manual_values.items():
            if key != "countryCode":
                fixed_values[key] = value

        try:
            self.result_df = MappingService.convert_dataframe(
                source_df=self.source_df,
                mapping=mapping,
                dwc_fields=self._get_active_fields(),
                fixed_values=fixed_values,
            )

            self.show_result_preview(self.result_df)
            self.btn_export.setEnabled(True)
            self.btn_coordinate_preview.setEnabled(True)
            total_missing, missing_summary, missing_locations = self._get_missing_value_summary(self.result_df)
            self._update_missing_summary_panel(total_missing, missing_summary, missing_locations)

            if total_missing > 0:
                QMessageBox.warning(
                    self,
                    "빈칸 확인 필요",
                    "결과를 아래 편집 테이블에 표시했습니다.\n"
                    "빈칸이 있는 데이터가 있어 저장 전에 확인하는 것을 권장합니다.\n\n"
                    f"총 빈칸 수: {total_missing}개\n"
                    + "\n".join(missing_summary),
                )
            else:
                QMessageBox.information(
                    self,
                    "완료",
                    "결과를 아래 편집 테이블에 표시했습니다.\n필요한 값은 직접 수정한 뒤 저장하세요.",
                )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"결과 확인 중 오류가 발생했습니다.\n\n{e}")

    def show_result_preview(self, df):
        preview_df = df

        self.result_table.clear()
        self.result_table.setRowCount(len(preview_df))
        self.result_table.setColumnCount(len(preview_df.columns))
        self.result_table.setHorizontalHeaderLabels([str(col) for col in preview_df.columns.tolist()])

        for row_idx in range(len(preview_df)):
            for col_idx, _ in enumerate(preview_df.columns):
                value = preview_df.iloc[row_idx, col_idx]
                self.result_table.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem("" if value is None else str(value)),
                )

        self.result_table.resizeColumnsToContents()
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def get_result_df_from_table(self):
        if self.result_df is None:
            return None

        updated_df = self.result_df.copy()

        for row in range(self.result_table.rowCount()):
            for col in range(self.result_table.columnCount()):
                item = self.result_table.item(row, col)
                updated_df.iat[row, col] = item.text() if item else ""

        return updated_df
