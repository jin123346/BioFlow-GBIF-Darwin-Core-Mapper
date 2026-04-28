from pathlib import Path

import pandas as pd


class ExcelService:
    EXCEL_EXTENSIONS = {".xlsx", ".xls"}
    CSV_EXTENSIONS = {".csv"}
    CSV_ENCODINGS = ("utf-8-sig", "cp949", "euc-kr", "utf-8")
    TEXT_FORMAT_COLUMNS = {
        "eventDate",
        "dateIdentified",
        "decimalLatitude",
        "decimalLongitude",
    }

    @staticmethod
    def _validate_excel_path(file_path: str) -> None:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in ExcelService.EXCEL_EXTENSIONS:
            raise ValueError("지원하지 않는 파일 형식입니다. .xlsx 또는 .xls 파일만 가능합니다.")

    @staticmethod
    def _validate_supported_path(file_path: str) -> None:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in ExcelService.EXCEL_EXTENSIONS | ExcelService.CSV_EXTENSIONS:
            raise ValueError("지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일만 가능합니다.")

    @staticmethod
    def is_csv_path(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in ExcelService.CSV_EXTENSIONS

    @staticmethod
    def _read_csv(file_path: str, **kwargs) -> pd.DataFrame:
        last_error = None

        for encoding in ExcelService.CSV_ENCODINGS:
            try:
                return pd.read_csv(file_path, encoding=encoding, **kwargs)
            except UnicodeDecodeError as error:
                last_error = error

        if last_error is not None:
            raise last_error

        return pd.read_csv(file_path, **kwargs)

    @staticmethod
    def get_sheet_names(file_path: str) -> list[str]:
        ExcelService._validate_supported_path(file_path)
        if ExcelService.is_csv_path(file_path):
            return ["CSV"]

        excel_file = pd.ExcelFile(file_path)
        return excel_file.sheet_names

    @staticmethod
    def read_excel_raw(file_path: str, sheet_name=0) -> pd.DataFrame:
        ExcelService._validate_supported_path(file_path)
        if ExcelService.is_csv_path(file_path):
            return ExcelService._read_csv(file_path, header=None)

        return pd.read_excel(file_path, header=None, sheet_name=sheet_name)

    @staticmethod
    def read_excel_with_header(file_path: str, header_row: int, sheet_name=0) -> pd.DataFrame:
        ExcelService._validate_supported_path(file_path)
        if ExcelService.is_csv_path(file_path):
            return ExcelService._read_csv(file_path, header=header_row)

        return pd.read_excel(file_path, header=header_row, sheet_name=sheet_name)

    @staticmethod
    def get_columns(df: pd.DataFrame) -> list[str]:
        return df.columns.tolist()

    @staticmethod
    def get_preview(df: pd.DataFrame, rows: int = 10) -> pd.DataFrame:
        return df.head(rows)

    @staticmethod
    def save_excel(df: pd.DataFrame, output_path: str) -> None:
        export_df = df.copy()

        for column in ExcelService.TEXT_FORMAT_COLUMNS & set(export_df.columns):
            export_df[column] = export_df[column].apply(
                lambda value: "" if pd.isna(value) else str(value)
            )

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False)
            worksheet = writer.sheets["Sheet1"]

            for column_index, column_name in enumerate(export_df.columns, start=1):
                if column_name not in ExcelService.TEXT_FORMAT_COLUMNS:
                    continue

                for row_index in range(1, len(export_df) + 2):
                    worksheet.cell(row=row_index, column=column_index).number_format = "@"
