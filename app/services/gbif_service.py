from __future__ import annotations

from dataclasses import dataclass
from base64 import b64encode
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from hashlib import sha256
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

import pandas as pd

from app.utils.paths import CACHE_DIR


GBIF_API_BASE = "https://api.gbif.org/v1"
GBIF_CACHE_DIR = CACHE_DIR / "gbif"
GBIF_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GbifSearchResult:
    matched_name: str
    taxon_key: int | None
    rank: str
    status: str
    total_records: int
    dataframe: pd.DataFrame
    from_cache: bool = False


@dataclass
class GbifDownloadRequestResult:
    key: str
    status_url: str
    download_url: str
    citation_url: str


class GbifFetchCancelled(RuntimeError):
    pass


@dataclass
class GbifOccurrenceCriteria:
    scientific_name: str = ""
    taxon_key: int | None = None
    dataset_key: str = ""
    country_code: str = ""
    geometry: str = ""
    basis_of_record: str = ""
    limit: int = 100000
    year_from: int | None = None
    year_to: int | None = None
    month_from: int = 1
    month_to: int = 12


class GbifService:
    @staticmethod
    def _cache_key(params: dict) -> str:
        normalized = json.dumps(params, ensure_ascii=False, sort_keys=True)
        return sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _cache_path(cache_key: str):
        return GBIF_CACHE_DIR / f"{cache_key}.json"

    @classmethod
    def _read_occurrence_cache(cls, cache_key: str) -> dict | None:
        cache_path = cls._cache_path(cache_key)
        if not cache_path.exists():
            return None

        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @classmethod
    def _write_occurrence_cache(cls, cache_key: str, payload: dict) -> None:
        cache_path = cls._cache_path(cache_key)
        cache_payload = {
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        cache_path.write_text(
            json.dumps(cache_payload, ensure_ascii=False),
            encoding="utf-8",
        )

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
            detail = e.read().decode("utf-8", errors="replace").strip()
            message = f"GBIF API 응답 오류: HTTP {e.code}"
            if detail:
                message = f"{message}\n{detail}"
            raise RuntimeError(message) from e
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
        basis_of_record: str = "",
        limit: int = 300,
        use_cache: bool = True,
        year_from: int | None = None,
        year_to: int | None = None,
        month_from: int = 1,
        month_to: int = 12,
        progress_callback=None,
        max_workers: int = 4,
    ) -> GbifSearchResult:
        return cls.fetch_occurrences_by_criteria(
            GbifOccurrenceCriteria(
                scientific_name=scientific_name,
                country_code=country_code,
                basis_of_record=basis_of_record,
                limit=limit,
                year_from=year_from,
                year_to=year_to,
                month_from=month_from,
                month_to=month_to,
            ),
            use_cache=use_cache,
            progress_callback=progress_callback,
            max_workers=max_workers,
        )

    @classmethod
    def fetch_occurrences_by_criteria(
        cls,
        criteria: GbifOccurrenceCriteria,
        use_cache: bool = True,
        progress_callback=None,
        max_workers: int = 4,
    ) -> GbifSearchResult:
        scientific_name = criteria.scientific_name.strip()
        country_code = criteria.country_code.strip().upper()
        basis_of_record = criteria.basis_of_record.strip().upper()
        dataset_key = criteria.dataset_key.strip()
        geometry = criteria.geometry.strip()
        taxon_key = criteria.taxon_key
        requested_limit = max(1, min(int(criteria.limit), 100000))
        cache_params = {
            "scientificName": scientific_name,
            "taxonKey": taxon_key,
            "datasetKey": dataset_key,
            "countryCode": country_code,
            "geometry": geometry,
            "basisOfRecord": basis_of_record,
            "limit": requested_limit,
            "hasCoordinate": True,
            "yearFrom": criteria.year_from,
            "yearTo": criteria.year_to,
            "monthFrom": criteria.month_from,
            "monthTo": criteria.month_to,
        }
        cache_key = cls._cache_key(cache_params)

        if use_cache:
            cached = cls._read_occurrence_cache(cache_key)
            if cached:
                match = cached.get("match", {})
                return GbifSearchResult(
                    matched_name=match.get("scientificName") or scientific_name or dataset_key or "Custom criteria",
                    taxon_key=match.get("usageKey") or taxon_key,
                    rank=match.get("rank", ""),
                    status=match.get("status", ""),
                    total_records=int(cached.get("totalRecords", 0) or 0),
                    dataframe=cls._to_dataframe(cached.get("records", [])),
                    from_cache=True,
                )

        match = {}
        if taxon_key is None and scientific_name:
            match = cls.match_species(scientific_name)
            taxon_key = match.get("usageKey")
            if not taxon_key:
                raise RuntimeError("GBIF에서 일치하는 taxonKey를 찾지 못했습니다.")
        elif taxon_key is not None:
            match = {
                "scientificName": scientific_name or f"taxonKey {taxon_key}",
                "usageKey": taxon_key,
            }

        if taxon_key is None and not dataset_key and not country_code and not geometry:
            raise ValueError("학명/taxonKey, datasetKey, 국가코드, geometry 중 하나 이상을 입력하세요.")

        page_size = min(300, requested_limit)
        rows = []
        total_records = 0
        cancel_message = "GBIF 데이터 가져오기가 취소되었습니다."

        base_params = {
            "hasCoordinate": "true",
            "limit": page_size,
        }
        if taxon_key is not None:
            base_params["taxon_key"] = taxon_key
        if dataset_key:
            base_params["dataset_key"] = dataset_key
        if country_code:
            base_params["country"] = country_code
        if geometry:
            base_params["geometry"] = geometry
        if basis_of_record:
            base_params["basis_of_record"] = basis_of_record
        if criteria.year_from is not None and criteria.year_to is not None:
            base_params["year"] = f"{criteria.year_from},{criteria.year_to}"
        elif criteria.year_from is not None:
            base_params["year"] = f"{criteria.year_from},"
        elif criteria.year_to is not None:
            base_params["year"] = f",{criteria.year_to}"
        if criteria.month_from > 1 or criteria.month_to < 12:
            base_params["month"] = f"{criteria.month_from},{criteria.month_to}"

        first_params = dict(base_params)
        first_params["offset"] = 0
        first_params["limit"] = page_size
        first_payload = cls._get_json("/occurrence/search", first_params)
        total_records = int(first_payload.get("count", 0) or 0)
        first_results = first_payload.get("results", [])
        rows.extend(first_results)

        target_records = min(requested_limit, total_records or requested_limit)

        def check_cancel(fetched_count: int | None = None) -> None:
            if progress_callback is None:
                return
            should_continue = progress_callback(
                min(fetched_count if fetched_count is not None else len(rows), target_records),
                total_records,
                requested_limit,
            )
            if should_continue is False:
                raise GbifFetchCancelled(cancel_message)

        check_cancel(len(rows))

        if first_results and not first_payload.get("endOfRecords", False) and len(rows) < target_records:
            offsets = list(range(len(rows), target_records, page_size))
            worker_count = max(1, min(int(max_workers), 8, len(offsets)))

            def fetch_page(offset: int) -> list[dict]:
                params = dict(base_params)
                params["offset"] = offset
                params["limit"] = min(page_size, target_records - offset)
                payload = cls._get_json("/occurrence/search", params)
                return payload.get("results", [])

            executor = ThreadPoolExecutor(max_workers=worker_count)
            try:
                future_map = {executor.submit(fetch_page, offset): offset for offset in offsets}
                pending = set(future_map)
                while pending:
                    check_cancel(len(rows))
                    done, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue
                    for future in done:
                        page_results = future.result()
                        if page_results:
                            rows.extend(page_results)
                        check_cancel(len(rows))
            except GbifFetchCancelled:
                for future in future_map:
                    future.cancel()
                raise
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

        if len(rows) > target_records:
            rows = rows[:target_records]

        dataframe = cls._to_dataframe(rows)
        cls._write_occurrence_cache(
            cache_key,
            {
                "params": cache_params,
                "match": match,
                "totalRecords": total_records,
                "records": rows,
            },
        )
        return GbifSearchResult(
            matched_name=match.get("scientificName") or scientific_name or dataset_key or "Custom criteria",
            taxon_key=taxon_key,
            rank=match.get("rank", ""),
            status=match.get("status", ""),
            total_records=total_records,
            dataframe=dataframe,
            from_cache=False,
        )

    @classmethod
    def request_occurrence_download(
        cls,
        scientific_name: str = "",
        country_code: str = "",
        username: str = "",
        password: str = "",
        email: str = "",
        taxon_key: int | None = None,
        dataset_key: str = "",
        geometry: str = "",
        basis_of_record: str = "",
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

        if taxon_key is None and scientific_name.strip():
            match = cls.match_species(scientific_name)
            taxon_key = match.get("usageKey")
            if not taxon_key:
                raise RuntimeError("GBIF에서 일치하는 taxonKey를 찾지 못했습니다.")
        if taxon_key is None and not dataset_key.strip() and not country_code.strip() and not geometry.strip():
            raise ValueError("학명/taxonKey, datasetKey, 국가코드, geometry 중 하나 이상을 입력하세요.")

        predicates = [
            {
                "type": "equals",
                "key": "HAS_COORDINATE",
                "value": "true",
            },
        ]
        if taxon_key is not None:
            predicates.append(
                {
                    "type": "equals",
                    "key": "TAXON_KEY",
                    "value": str(taxon_key),
                }
            )
        if dataset_key.strip():
            predicates.append(
                {
                    "type": "equals",
                    "key": "DATASET_KEY",
                    "value": dataset_key.strip(),
                }
            )
        if country_code.strip():
            predicates.append(
                {
                    "type": "equals",
                    "key": "COUNTRY",
                    "value": country_code.strip().upper(),
                }
            )
        if geometry.strip():
            predicates.append(
                {
                    "type": "within",
                    "key": "GEOMETRY",
                    "value": geometry.strip(),
                }
            )
        if basis_of_record.strip():
            predicates.append(
                {
                    "type": "equals",
                    "key": "BASIS_OF_RECORD",
                    "value": basis_of_record.strip().upper(),
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
            "taxonKey",
            "datasetKey",
            "scientificName",
            "acceptedScientificName",
            "kingdom",
            "phylum",
            "class",
            "order",
            "family",
            "genus",
            "species",
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
                    "taxonKey": record.get("taxonKey", ""),
                    "datasetKey": record.get("datasetKey", ""),
                    "scientificName": record.get("scientificName", ""),
                    "acceptedScientificName": record.get("acceptedScientificName", ""),
                    "kingdom": record.get("kingdom", ""),
                    "phylum": record.get("phylum", ""),
                    "class": record.get("class", ""),
                    "order": record.get("order", ""),
                    "family": record.get("family", ""),
                    "genus": record.get("genus", ""),
                    "species": record.get("species", ""),
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
