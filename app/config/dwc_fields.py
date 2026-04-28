ALL_DWC_FIELDS = [
    {"key": "occurrenceID", "label": "occurrenceID", "description": "출현 기록의 고유 ID"},
    {"key": "basisOfRecord", "label": "basisOfRecord", "description": "기록 유형 (필수)"},
    {"key": "catalogNumber", "label": "catalogNumber", "description": "내부 데이터 번호"},
    {"key": "recordedBy", "label": "recordedBy", "description": "채집자"},
    {"key": "individualCount", "label": "individualCount", "description": "개체 수"},
    {"key": "sex", "label": "sex", "description": "성별"},
    {"key": "lifeStage", "label": "lifeStage", "description": "생애 단계"},
    {"key": "occurrenceStatus", "label": "occurrenceStatus", "description": "존재 여부"},
    {"key": "occurrenceRemarks", "label": "occurrenceRemarks", "description": "관찰/표본 비고"},
    {"key": "eventDate", "label": "eventDate", "description": "관찰 날짜"},
    {"key": "year", "label": "year", "description": "연도"},
    {"key": "month", "label": "month", "description": "월"},
    {"key": "day", "label": "day", "description": "일"},
    {"key": "habitat", "label": "habitat", "description": "서식지"},
    {"key": "samplingProtocol", "label": "samplingProtocol", "description": "조사 방법"},
    {"key": "countryCode", "label": "countryCode", "description": "국가 코드 (ISO 3166-1 alpha-2)"},
    {"key": "stateProvince", "label": "stateProvince", "description": "시/도 영문"},
    {"key": "county", "label": "county", "description": "시/군/구 영문"},
    {"key": "locality", "label": "locality", "description": "읍/면/동 영문"},
    {"key": "verbatimLocality", "label": "verbatimLocality", "description": "상세 위치 영문"},
    {"key": "decimalLatitude", "label": "decimalLatitude", "description": "위도"},
    {"key": "decimalLongitude", "label": "decimalLongitude", "description": "경도"},
    {
        "key": "coordinateUncertaintyInMeters",
        "label": "coordinateUncertaintyInMeters",
        "description": "좌표 오차",
    },
    {"key": "identifiedBy", "label": "identifiedBy", "description": "동정자 영문"},
    {"key": "dateIdentified", "label": "dateIdentified", "description": "동정 날짜"},
    {
        "key": "identificationRemarks",
        "label": "identificationRemarks",
        "description": "동정 비고",
    },
    {"key": "scientificName", "label": "scientificName", "description": "학명"},
    {"key": "vernacularName", "label": "vernacularName", "description": "국명"},
    {"key": "kingdom", "label": "kingdom", "description": "계"},
    {"key": "phylum", "label": "phylum", "description": "문"},
    {"key": "class", "label": "class", "description": "강"},
    {"key": "order", "label": "order", "description": "목"},
    {"key": "family", "label": "family", "description": "과"},
    {"key": "genus", "label": "genus", "description": "속"},
    {"key": "taxonRank", "label": "taxonRank", "description": "종/속 등 분류 단계"},
    {
        "key": "scientificNameAuthorship",
        "label": "scientificNameAuthorship",
        "description": "명명자",
    },
    {"key": "institutionCode", "label": "institutionCode", "description": "기관 코드"},
    {"key": "collectionCode", "label": "collectionCode", "description": "컬렉션 코드"},
]

DEFAULT_DWC_FIELD_KEYS = [
    "occurrenceID",
    "basisOfRecord",
    "eventDate",
    "institutionCode",
    "scientificName",
    "collectionCode",
    "decimalLatitude",
    "decimalLongitude",
    "countryCode",
    "dateIdentified",
    "identifiedBy",
    "stateProvince",
    "county",
    "locality",
    "verbatimLocality",
    "catalogNumber",
    "vernacularName",
]

DWC_FIELD_MAP = {field["key"]: field for field in ALL_DWC_FIELDS}


def get_default_dwc_fields() -> list[dict]:
    return [DWC_FIELD_MAP[key] for key in DEFAULT_DWC_FIELD_KEYS]


def get_optional_dwc_fields(active_keys: list[str]) -> list[dict]:
    active_key_set = set(active_keys)
    return [field for field in ALL_DWC_FIELDS if field["key"] not in active_key_set]


def get_dwc_field(key: str) -> dict:
    return DWC_FIELD_MAP[key]
