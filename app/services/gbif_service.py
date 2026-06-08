from __future__ import annotations

from dataclasses import dataclass
from base64 import b64encode
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

import pandas as pd


GBIF_API_BASE = "https://api.gbif.org/v1"


@dataclass
class GbifSearchResult:
    matched_name: str
    taxon_key: int | None
    rank: str
    status: str
    total_records: int
    dataframe: pd.DataFrame


@dataclass
class GbifDownloadRequestResult:
    key: str
    status_url: str
    download_url: str
    citation_url: str


class GbifService:
    @staticmethod
    def _get_json(path: str, params: dict | None = None) -> dict:
        query = f"?{urlencode(params or {}, doseq=True)}" if params else ""
        request = Request(
            f"{GBIF_API_BASE}{path}{query}",
            headers={"User-Agent": "BioFlowGBIF/1.0"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            raise RuntimeError(f"GBIF API 응답 오류: HTTP {e.code}") from e
        except URLError as e:
            raise RuntimeError(f"GBIF API에 연결할 수 없습니다: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError("GBIF API 요청 시간이 초과되었습니다.") from e

    @staticmethod
    def _post_json(
        path: str,
        payload: dict,
        username: str,
        password: str,
    ) -> str:
        auth_value = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request = Request(
            f"{GBIF_API_BASE}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Basic {auth_value}",
                "Content-Type": "application/json",
                "User-Agent": "BioFlowGBIF/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8").strip()
        except HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace").strip()
            message = f"GBIF API 응답 오류: HTTP {e.code}"
            if detail:
                message = f"{message}\n{detail}"
            raise RuntimeError(message) from e
        except URLError as e:
            raise RuntimeError(f"GBIF API에 연결할 수 없습니다: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError("GBIF API 요청 시간이 초과되었습니다.") from e

    @classmethod
    def match_species(cls, scientific_name: str) -> dict:
        name = scientific_name.strip()
        if not name:
            raise ValueError("검색할 학명을 입력하세요.")

        return cls._get_json("/species/match", {"name": name})

    @classmethod
    def fetch_occurrences(
        cls,
        scientific_name: str,
        country_code: str = "",
        limit: int = 300,
    ) -> GbifSearchResult:
        match = cls.match_species(scientific_name)
        taxon_key = match.get("usageKey")
        if not taxon_key:
            raise RuntimeError("GBIF에서 일치하는 taxonKey를 찾지 못했습니다.")

        requested_limit = max(1, min(int(limit), 100000))
        page_size = min(300, requested_limit)
        rows = []
        total_records = 0

        base_params = {
            "taxon_key": taxon_key,
            "hasCoordinate": "true",
            "limit": page_size,
        }
        if country_code.strip():
            base_params["country"] = country_code.strip().upper()

        while len(rows) < requested_limit:
            params = dict(base_params)
            params["offset"] = len(rows)
            params["limit"] = min(page_size, requested_limit - len(rows))
            payload = cls._get_json("/occurrence/search", params)
            total_records = int(payload.get("count", 0) or 0)
            results = payload.get("results", [])
            if not results:
                break
            rows.extend(results)
            if payload.get("endOfRecords", False):
                break

        dataframe = cls._to_dataframe(rows)
        return GbifSearchResult(
            matched_name=match.get("scientificName") or scientific_name.strip(),
            taxon_key=taxon_key,
            rank=match.get("rank", ""),
            status=match.get("status", ""),
            total_records=total_records,
            dataframe=dataframe,
        )

    @classmethod
    def request_occurrence_download(
        cls,
        scientific_name: str,
        country_code: str,
        username: str,
        password: str,
        email: str,
        year_from: int | None = None,
        year_to: int | None = None,
        month_from: int = 1,
        month_to: int = 12,
    ) -> GbifDownloadRequestResult:
        if not username.strip():
            raise ValueError("GBIF 사용자 이름을 입력하세요.")
        if not password:
            raise ValueError("GBIF 비밀번호를 입력하세요.")
        if not email.strip():
            raise ValueError("GBIF 계정 이메일을 입력하세요.")

        match = cls.match_species(scientific_name)
        taxon_key = match.get("usageKey")
        if not taxon_key:
            raise RuntimeError("GBIF에서 일치하는 taxonKey를 찾지 못했습니다.")

        predicates = [
            {
                "type": "equals",
                "key": "TAXON_KEY",
                "value": str(taxon_key),
            },
            {
                "type": "equals",
                "key": "HAS_COORDINATE",
                "value": "true",
            },
        ]
        if country_code.strip():
            predicates.append(
                {
                    "type": "equals",
                    "key": "COUNTRY",
                    "value": country_code.strip().upper(),
                }
            )
        if year_from is not None:
            predicates.append(
                {
                    "type": "greaterThanOrEquals",
                    "key": "YEAR",
                    "value": str(year_from),
                }
            )
        if year_to is not None:
            predicates.append(
                {
                    "type": "lessThanOrEquals",
                    "key": "YEAR",
                    "value": str(year_to),
                }
            )
        if month_from > 1:
            predicates.append(
                {
                    "type": "greaterThanOrEquals",
                    "key": "MONTH",
                    "value": str(month_from),
                }
            )
        if month_to < 12:
            predicates.append(
                {
                    "type": "lessThanOrEquals",
                    "key": "MONTH",
                    "value": str(month_to),
                }
            )

        payload = {
            "creator": username.strip(),
            "notificationAddresses": [email.strip()],
            "sendNotification": True,
            "format": "SIMPLE_CSV",
            "predicate": {
                "type": "and",
                "predicates": predicates,
            },
        }
        key = cls._post_json(
            "/occurrence/download/request",
            payload,
            username.strip(),
            password,
        ).strip('"')
        if not key:
            raise RuntimeError("GBIF 다운로드 요청 key를 받지 못했습니다.")

        return GbifDownloadRequestResult(
            key=key,
            status_url=f"{GBIF_API_BASE}/occurrence/download/{key}",
            download_url=f"https://www.gbif.org/occurrence/download/{key}",
            citation_url="",
        )

    @staticmethod
    def _to_dataframe(records: list[dict]) -> pd.DataFrame:
        columns = [
            "gbifID",
            "scientificName",
            "acceptedScientificName",
            "decimalLatitude",
            "decimalLongitude",
            "year",
            "month",
            "eventDate",
            "countryCode",
            "locality",
            "basisOfRecord",
            "institutionCode",
            "datasetName",
        ]
        rows = []
        for record in records:
            rows.append(
                {
                    "gbifID": record.get("key", ""),
                    "scientificName": record.get("scientificName", ""),
                    "acceptedScientificName": record.get("acceptedScientificName", ""),
                    "decimalLatitude": record.get("decimalLatitude", ""),
                    "decimalLongitude": record.get("decimalLongitude", ""),
                    "year": record.get("year", ""),
                    "month": record.get("month", ""),
                    "eventDate": record.get("eventDate", ""),
                    "countryCode": record.get("countryCode", ""),
                    "locality": record.get("locality", ""),
                    "basisOfRecord": record.get("basisOfRecord", ""),
                    "institutionCode": record.get("institutionCode", ""),
                    "datasetName": record.get("datasetName", ""),
                }
            )

        return pd.DataFrame(rows, columns=columns)
