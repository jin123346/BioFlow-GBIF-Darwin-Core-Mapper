# BioFlow - GBIF Darwin Core Mapper

Made by Jinhee Ha

Version 2.0.1

© 2026 Jinhee Ha. All rights reserved.

- 문의사항은 이메일로 문의해주세요.
- Email:
- GitHub:

엑셀/CSV 데이터를 GBIF 업로드용 Darwin Core 형식으로 매핑하고, 결과 엑셀로 저장하는 데스크톱 프로그램입니다.

## 주요 기능

- 엑셀/CSV 파일 업로드 및 시트 선택
- 헤더 행 직접 선택
- 기본 GBIF 컬럼 자동 매핑
- 필요한 GBIF 컬럼 추가 매핑
- 결과 데이터 직접 수정
- 빈칸 컬럼/위치 점검
- 매핑 전 원본 위도/경도 좌표 확인
- 위도/경도 좌표 지도 미리보기
- GBIF 종 occurrence 데이터 조회 및 분석
- 연도별/월별/계절별 그래프 리포트
- GBIF occurrence download DOI 요청
- GBIF 분석 데이터 CSV/엑셀/GeoJSON 저장
- BioFlow 로고 표시
- 매핑 결과 엑셀 저장

## 릴리즈 노트

### BioFlowGBIF v2.0.1

GBIF 종 데이터 분석 기능을 추가한 메이저 릴리즈입니다. 기존 Darwin Core 매핑 기능에 더해 GBIF occurrence 데이터를 직접 조회하고, 지도와 그래프로 분포 및 기록 변화를 확인할 수 있습니다.

#### 변경 사항

- `GBIF 분석` 탭 추가
- 종명 기반 GBIF occurrence 조회
- 동일 조건 재조회 시 로컬 캐시 사용
- 한국 주요 지역명을 GBIF geometry bbox 조건으로 자동 변환
- 연도 범위와 월 범위 필터 추가
- 연도별, 월별, 계절별, 종합 그래프 리포트 추가
- 막대 그래프와 선 그래프 선택 지원
- 결측치, 중복 GBIF ID, 자료유형, dataset/institution 제외 키워드 기반 정제 옵션 추가
- GBIF occurrence download DOI 요청 기능 추가
- 다운로드 URL 표시, 열기, 복사 기능 추가
- GBIF 분석 데이터 CSV 저장 추가
- GBIF 분석 데이터와 Excel 차트가 포함된 엑셀 저장 추가
- QGIS에서 열 수 있는 GeoJSON 저장 추가
- 빠른 분석 조회 한도를 최대 100,000건으로 확대

### BioFlowGBIF v1.0.4

원본 엑셀/CSV 데이터의 위도/경도 컬럼을 기준으로, GBIF 매핑 전에 좌표만 먼저 확인할 수 있는 기능을 추가했습니다.

#### 변경 사항

- `원본 좌표 확인` 버튼 추가
- 헤더 적용 후 원본 데이터의 위도 컬럼과 경도 컬럼을 직접 선택해 지도 미리보기 생성
- `위도`, `latitude`, `lat`, `경도`, `longitude`, `lon`, `lng` 등 기존 자동 매핑 후보를 이용해 좌표 컬럼 기본 선택
- 매핑 결과 생성 전에도 좌표 누락, 범위 오류, 위치 이상 여부를 먼저 점검 가능
- 기존 `좌표 확인` 기능은 매핑 결과의 `decimalLatitude`, `decimalLongitude` 확인 용도로 유지

### BioFlowGBIF v1.0.3

BioFlowGBIF의 첫 번째 공개 릴리즈입니다. 엑셀/CSV 데이터를 GBIF 업로드용 Darwin Core 형식으로 매핑하고, 결과를 엑셀 파일로 저장할 수 있는 Windows 데스크톱 프로그램입니다.

#### 주요 포함 기능

- 엑셀/CSV 파일 업로드
- 엑셀 시트 선택
- 원본 데이터에서 헤더 행 직접 지정
- GBIF Darwin Core 기본 컬럼 자동 매핑
- 필요한 GBIF 컬럼 추가 매핑
- 자동 매핑 후보 컬럼명 직접 수정 및 저장
- 변환 결과 미리보기 및 직접 수정
- 빈칸 컬럼/위치 점검
- `decimalLatitude`, `decimalLongitude` 좌표 지도 미리보기
- 매핑 결과 엑셀 저장
- BioFlow 로고 및 창 아이콘 적용

#### 다운로드 및 릴리즈 노트

최신 다운로드 파일과 릴리즈 노트는 아래 링크에서 확인할 수 있습니다.

- [최신 릴리즈 보기](https://github.com/jin123346/BioFlow-GBIF-Darwin-Core-Mapper/releases/latest)

`BioFlowGBIF_v2.0.1.zip` 파일을 다운로드한 뒤 압축을 풀고 실행하세요.

```text
BioFlowGBIF.exe
```

## 문서

- [사용자 가이드](docs/user_guide.md)
- [배포용 PDF 매뉴얼](docs/BioFlowGBIF_User_Guide_v1.0.4.pdf)
- [문서 목록](docs/README.md)

현재 기본 기능과 좌표 지도 미리보기에는 R 또는 Rscript 설치가 필요하지 않습니다. 지도 미리보기는 OpenStreetMap 지도 타일을 사용하므로 인터넷 연결이 필요합니다.

## 개발 환경에서 실행

```powershell
.\.venv\Scripts\python.exe main.py
```

또는 새 환경에서 설치하는 경우:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Windows exe 만들기

의존성 설치 후 아래 명령으로 exe를 생성합니다.

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name BioFlowGBIF main.py
```

버전별 폴더로 따로 빌드하려면 아래 스크립트를 사용합니다. 버전 번호는 `app/config/app_info.py`의 `APP_VERSION` 값을 사용합니다.

```powershell
.\build_exe.ps1
```

빌드 결과는 `dist\BioFlowGBIF_v2.0.1\BioFlowGBIF.exe`처럼 생성됩니다. 같은 버전 폴더가 이미 있으면 덮어쓰지 않고 중단됩니다. 필요하면 `.\build_exe.ps1 -Version 2.0.1`처럼 직접 지정한 버전으로 빌드할 수도 있습니다.

`bioflow_logo.png`는 앱 상단 로고와 창 아이콘으로 사용되며, `build_exe.ps1` 실행 시 배포 폴더에 함께 포함됩니다.

빌드가 완료되면 실행 파일은 아래 경로에 생성됩니다.

```text
dist\BioFlowGBIF_v2.0.1\BioFlowGBIF.exe
```

배포할 때는 `dist\BioFlowGBIF_v2.0.1` 폴더 전체를 압축해서 전달하는 것을 권장합니다. 실행 파일과 필요한 라이브러리, 로고 이미지가 함께 들어 있기 때문입니다.

## 배포 전 확인 사항

- `dist\BioFlowGBIF_v2.0.1\BioFlowGBIF.exe`를 실행해 프로그램이 열리는지 확인합니다.
- 상단에 BioFlow 로고가 표시되는지 확인합니다.
- 샘플 엑셀 파일로 업로드, 시트 선택, 헤더 적용, 결과 확인, 엑셀 저장까지 확인합니다.
- 좌표가 있는 샘플 파일로 `원본 좌표 확인`과 `좌표 확인`을 눌러 지도 미리보기가 열리는지 확인합니다.
- 저장 결과 파일에서 날짜가 `YYYY-MM-DD` 형식인지 확인합니다.
- 위도/경도 값이 텍스트 형태로 유지되는지 확인합니다.
# BioFlow-GBIF-Darwin-Core-Mapper
