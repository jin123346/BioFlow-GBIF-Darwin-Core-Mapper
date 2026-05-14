import json

from app.utils.paths import MAPPING_DIR


AUTO_MAPPING_RULES = {
    "occurrenceID": ["개체번호", "데이터베이스번호", "출현id", "occurrenceid", "recordid", "catalogid", "db_no", "id"],
    "basisOfRecord": ["기록유형", "basisofrecord"],
    "catalogNumber": ["표본번호", "기록번호", "catalognumber"],
    "recordedBy": ["채집자", "조사자", "recordedby", "collector"],
    "individualCount": ["개체수", "개체수량", "individualcount", "count"],
    "sex": ["성별", "sex"],
    "lifeStage": ["생활단계", "life stage", "lifestage"],
    "occurrenceStatus": ["존재여부", "occurrencestatus"],
    "occurrenceRemarks": ["비고", "관찰비고", "occurrenceremarks", "remarks"],
    "eventDate": ["관찰일", "관찰연월일", "관찰일 영문", "eventdate", "observationdate", "collectiondate", "date"],
    "year": ["연도", "year"],
    "month": ["월", "month"],
    "day": ["일", "day"],
    "habitat": ["서식지", "habitat"],
    "samplingProtocol": ["조사방법", "samplingprotocol", "protocol"],
    "countryCode": ["국가코드", "countrycode", "country"],
    "stateProvince": ["시도", "시도 영문", "stateprovince", "state", "province"],
    "county": ["시군구", "시군구 영문", "county", "district"],
    "locality": ["읍면동", "읍면동 영문", "locality", "location", "site"],
    "verbatimLocality": ["상세위치", "상세위치 영문", "verbatimlocality", "detaillocation", "locationdetail"],
    "decimalLatitude": ["위도", "위도 영문", "decimallatitude", "latitude", "lat"],
    "decimalLongitude": ["경도", "경도 영문", "decimallongitude", "longitude", "lon", "lng"],
    "coordinateUncertaintyInMeters": ["좌표오차", "coordinateuncertaintyinmeters", "coordinateuncertainty"],
    "identifiedBy": ["동정자", "동정자 영문", "identifiedby", "determinavit", "identifier"],
    "dateIdentified": ["동정일", "동정연월일", "동정연월일 영문", "dateidentified", "identifieddate"],
    "identificationRemarks": ["동정비고", "identificationremarks"],
    "scientificName": ["학명", "학명 영문", "scientificname", "scientific", "sci_name", "species"],
    "vernacularName": ["국명", "국명 영문", "vernacularname", "commonname"],
    "kingdom": ["계", "kingdom"],
    "phylum": ["문", "phylum"],
    "class": ["강", "class"],
    "order": ["목", "order"],
    "family": ["과", "family"],
    "genus": ["속", "genus"],
    "taxonRank": ["분류계급", "taxonrank", "rank"],
    "scientificNameAuthorship": ["명명자", "scientificnameauthorship", "authorship"],
    "institutionCode": ["기관코드", "institutioncode"],
    "collectionCode": ["분류코드", "컬렉션코드", "collectioncode"],
}

CUSTOM_AUTO_MAPPING_PATH = MAPPING_DIR / "auto_mapping_rules.json"


def get_default_auto_mapping_rules() -> dict[str, list[str]]:
    return {key: list(values) for key, values in AUTO_MAPPING_RULES.items()}


def _clean_rules(rules: dict) -> dict[str, list[str]]:
    cleaned = {}
    for key, values in rules.items():
        if not isinstance(values, list):
            continue

        keywords = []
        seen = set()
        for value in values:
            text = str(value).strip()
            if not text:
                continue

            normalized = text.lower()
            if normalized in seen:
                continue

            seen.add(normalized)
            keywords.append(text)

        cleaned[str(key)] = keywords

    return cleaned


def load_auto_mapping_rules() -> dict[str, list[str]]:
    rules = get_default_auto_mapping_rules()

    if not CUSTOM_AUTO_MAPPING_PATH.exists():
        return rules

    with CUSTOM_AUTO_MAPPING_PATH.open("r", encoding="utf-8") as file:
        custom_rules = json.load(file)

    if not isinstance(custom_rules, dict):
        raise ValueError("자동 매핑 설정 파일 형식이 올바르지 않습니다.")

    rules.update(_clean_rules(custom_rules))
    return rules


def save_auto_mapping_rules(rules: dict[str, list[str]]) -> None:
    CUSTOM_AUTO_MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned = _clean_rules(rules)
    with CUSTOM_AUTO_MAPPING_PATH.open("w", encoding="utf-8") as file:
        json.dump(cleaned, file, ensure_ascii=False, indent=2)


def reset_auto_mapping_rules() -> None:
    if CUSTOM_AUTO_MAPPING_PATH.exists():
        CUSTOM_AUTO_MAPPING_PATH.unlink()