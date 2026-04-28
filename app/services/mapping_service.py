import difflib

import pandas as pd

from app.config.auto_mapping import AUTO_MAPPING_RULES

DATE_FIELDS = {"eventDate", "dateIdentified"}
TEXT_NUMBER_FIELDS = {
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
}


def normalize(text: str) -> str:
    return str(text).lower().replace(" ", "").replace("_", "").replace("-", "")


def auto_match_column(dwc_key: str, source_columns: list[str]) -> str | None:
    candidates = AUTO_MAPPING_RULES.get(dwc_key, [])

    for col in source_columns:
        col_norm = normalize(col)

        for keyword in candidates:
            if normalize(keyword) in col_norm:
                return col

    return fuzzy_match(dwc_key, source_columns)


def fuzzy_match(dwc_key: str, source_columns: list[str]) -> str | None:
    candidates = AUTO_MAPPING_RULES.get(dwc_key, [])
    normalized_map = {normalize(col): col for col in source_columns}

    for candidate in candidates:
        matches = difflib.get_close_matches(
            normalize(candidate),
            list(normalized_map.keys()),
            n=1,
            cutoff=0.82,
        )
        if matches:
            return normalized_map[matches[0]]

    return None


def _format_date_value(value) -> str:
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=False)

    if pd.isna(parsed):
        return text

    return parsed.strftime("%Y-%m-%d")


def _format_text_number_value(value) -> str:
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    if isinstance(value, float):
        return format(value, ".15g")

    return text


def _format_series(dwc_key: str, series: pd.Series) -> pd.Series:
    if dwc_key in DATE_FIELDS:
        return series.apply(_format_date_value).astype(str)

    if dwc_key in TEXT_NUMBER_FIELDS:
        return series.apply(_format_text_number_value).astype(str)

    return series


class MappingService:
    @staticmethod
    def build_mapping(combo_map: dict) -> dict:
        mapping = {}
        for dwc_field, source_col in combo_map.items():
            source_col = (source_col or "").strip()
            if source_col:
                mapping[dwc_field] = source_col
        return mapping

    @staticmethod
    def convert_dataframe(
        source_df: pd.DataFrame,
        mapping: dict,
        dwc_fields: list[dict],
        fixed_values: dict | None = None,
    ) -> pd.DataFrame:
        fixed_values = fixed_values or {}
        result = pd.DataFrame(index=source_df.index)

        for field in dwc_fields:
            dwc_key = field["key"]

            if dwc_key in fixed_values:
                if dwc_key in DATE_FIELDS:
                    result[dwc_key] = [_format_date_value(fixed_values[dwc_key])] * len(source_df)
                elif dwc_key in TEXT_NUMBER_FIELDS:
                    result[dwc_key] = [_format_text_number_value(fixed_values[dwc_key])] * len(source_df)
                else:
                    result[dwc_key] = [fixed_values[dwc_key]] * len(source_df)
                continue

            source_col = mapping.get(dwc_key)
            if source_col and source_col in source_df.columns:
                result[dwc_key] = _format_series(dwc_key, source_df[source_col])
            else:
                result[dwc_key] = ""

        return result
