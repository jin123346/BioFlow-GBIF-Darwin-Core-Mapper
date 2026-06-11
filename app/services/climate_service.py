from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

import pandas as pd

from app.utils.paths import CACHE_DIR


NASA_POWER_API_BASE = "https://power.larc.nasa.gov/api/temporal/monthly/point"
CLIMATE_CACHE_DIR = CACHE_DIR / "climate"
CLIMATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ClimateMonthlyResult:
    dataframe: pd.DataFrame
    latitude: float
    longitude: float
    start_year: int
    end_year: int
    source: str
    from_cache: bool = False


class ClimateService:
    PARAMETER_LABELS = {
        "T2M": "temperatureC",
        "PRECTOTCORR": "precipitationMmPerDay",
    }

    @staticmethod
    def _cache_key(params: dict) -> str:
        normalized = json.dumps(params, ensure_ascii=False, sort_keys=True)
        return sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _cache_path(cache_key: str):
        return CLIMATE_CACHE_DIR / f"{cache_key}.json"

    @classmethod
    def _read_cache(cls, cache_key: str) -> dict | None:
        cache_path = cls._cache_path(cache_key)
        if not cache_path.exists():
            return None
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @classmethod
    def _write_cache(cls, cache_key: str, payload: dict) -> None:
        cache_path = cls._cache_path(cache_key)
        cache_payload = {
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def fetch_monthly_power(
        cls,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        use_cache: bool = True,
    ) -> ClimateMonthlyResult:
        latest_available_year = datetime.now(timezone.utc).year - 1
        if start_year > latest_available_year:
            raise ValueError(
                f"NASA POWER monthly climate data is currently available through {latest_available_year}. "
                "The selected GBIF data only contains newer years."
            )
        end_year = min(end_year, latest_available_year)
        if start_year > end_year:
            raise ValueError("Climate start year must be less than or equal to end year.")
        params = {
            "parameters": "T2M,PRECTOTCORR",
            "community": "SB",
            "longitude": round(float(longitude), 4),
            "latitude": round(float(latitude), 4),
            "format": "JSON",
            "start": int(start_year),
            "end": int(end_year),
        }
        cache_key = cls._cache_key(params)
        if use_cache:
            cached = cls._read_cache(cache_key)
            if cached:
                return ClimateMonthlyResult(
                    dataframe=cls._payload_to_dataframe(cached),
                    latitude=float(cached.get("latitude", params["latitude"])),
                    longitude=float(cached.get("longitude", params["longitude"])),
                    start_year=int(cached.get("startYear", params["start"])),
                    end_year=int(cached.get("endYear", params["end"])),
                    source="NASA POWER",
                    from_cache=True,
                )

        query = urlencode(params)
        request = Request(f"{NASA_POWER_API_BASE}?{query}", headers={"User-Agent": "BioFlowClimate/1.0"})
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace").strip()
            message = f"NASA POWER API error: HTTP {e.code}"
            if detail:
                message = f"{message}\n{detail}"
            raise RuntimeError(message) from e
        except URLError as e:
            raise RuntimeError(f"NASA POWER API connection failed: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError("NASA POWER API request timed out.") from e

        cache_payload = {
            "latitude": params["latitude"],
            "longitude": params["longitude"],
            "startYear": params["start"],
            "endYear": params["end"],
            "payload": payload,
        }
        cls._write_cache(cache_key, cache_payload)
        return ClimateMonthlyResult(
            dataframe=cls._payload_to_dataframe(cache_payload),
            latitude=float(params["latitude"]),
            longitude=float(params["longitude"]),
            start_year=int(params["start"]),
            end_year=int(params["end"]),
            source="NASA POWER",
            from_cache=False,
        )

    @classmethod
    def _payload_to_dataframe(cls, cache_payload: dict) -> pd.DataFrame:
        payload = cache_payload.get("payload", cache_payload)
        parameter_data = payload.get("properties", {}).get("parameter", {})
        rows_by_period: dict[str, dict] = {}
        for parameter_key, output_column in cls.PARAMETER_LABELS.items():
            values = parameter_data.get(parameter_key, {})
            for period_key, raw_value in values.items():
                if len(str(period_key)) != 6:
                    continue
                year = int(str(period_key)[:4])
                month = int(str(period_key)[4:6])
                row = rows_by_period.setdefault(
                    str(period_key),
                    {"year": year, "month": month, "period": str(period_key)},
                )
                value = pd.to_numeric(raw_value, errors="coerce")
                row[output_column] = None if pd.isna(value) else float(value)

        dataframe = pd.DataFrame(rows_by_period.values())
        if dataframe.empty:
            return pd.DataFrame(
                columns=[
                    "year",
                    "month",
                    "period",
                    "temperatureC",
                    "precipitationMmPerDay",
                    "precipitationTotalMm",
                ]
            )
        if "precipitationMmPerDay" in dataframe.columns:
            month_start = pd.to_datetime(
                dataframe["year"].astype(str) + "-" + dataframe["month"].astype(str).str.zfill(2) + "-01",
                errors="coerce",
            )
            dataframe["precipitationTotalMm"] = dataframe["precipitationMmPerDay"] * month_start.dt.days_in_month
        return dataframe.sort_values(["year", "month"]).reset_index(drop=True)
