# BioFlow - GBIF Darwin Core Mapper

Made by Jinhee Ha

Version 1.0.3

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
- 위도/경도 좌표 지도 미리보기
- BioFlow 로고 표시
- 매핑 결과 엑셀 저장

## 기본 제공 컬럼

아래 컬럼은 기본 매핑 화면에 항상 표시됩니다.

- `occurrenceID`
- `basisOfRecord`
- `eventDate`
- `institutionCode`
- `scientificName`
- `collectionCode`
- `decimalLatitude`
- `decimalLongitude`
- `countryCode`
- `dateIdentified`
- `identifiedBy`
- `stateProvince`
- `county`
- `locality`
- `verbatimLocality`
- `catalogNumber`
- `vernacularName`

그 외 `recordedBy`, `individualCount`, `habitat`, `samplingProtocol`, `coordinateUncertaintyInMeters`, `kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `taxonRank`, `scientificNameAuthorship` 등은 `컬럼 추가` 버튼으로 추가할 수 있습니다.

## 사용 방법

1. `파일 업로드` 버튼을 누릅니다.
2. 사용할 엑셀 또는 CSV 파일을 선택합니다.
3. 시트 선택 창에서 변환할 시트를 선택합니다.
4. 왼쪽 원본 테이블에서 헤더로 사용할 행을 클릭합니다.
5. 상단의 `선택 행을 헤더로 적용` 버튼을 누릅니다.
6. 오른쪽 `GBIF 필드 매핑` 영역에서 자동 매핑된 컬럼을 확인합니다.
7. 필요한 경우 잘못 매핑된 항목을 직접 선택합니다.
8. 기본 컬럼 외에 더 필요한 GBIF 컬럼은 `컬럼 추가` 버튼으로 추가합니다.
9. `결과 확인` 버튼을 누릅니다.
10. 결과 테이블에서 값을 확인하고 필요하면 직접 수정합니다.
11. 아래 `빈칸 점검` 영역에서 빈칸 컬럼과 위치를 확인합니다.
12. `좌표 확인` 버튼으로 `decimalLatitude`, `decimalLongitude` 값을 지도에서 확인합니다.
13. `매핑 결과 엑셀 저장` 버튼으로 결과 파일을 저장합니다.

## 빈칸 점검

`결과 확인`을 누르면 결과 테이블 아래에 빈칸 요약이 표시됩니다.

- 컬럼별 빈칸 개수
- 빈칸 위치 예시
- 예: `scientificName: 3행 5열`

빈칸 위치가 많을 경우 일부 위치만 먼저 보여주고, 나머지는 `외 n개 위치`로 표시합니다.

## 좌표 지도 미리보기

`결과 확인`을 누른 뒤 `좌표 확인` 버튼을 누르면 결과 테이블의 `decimalLatitude`, `decimalLongitude` 값을 이용해 지도 미리보기 HTML을 생성합니다.

- 생성 위치: `data\output\coordinate_preview_map.html`
- 유효한 좌표만 지도에 표시합니다.
- 좌표가 비어 있거나 범위를 벗어나면 제외 개수로 표시합니다.
- 마커를 클릭하면 행 번호, 위도/경도, 학명, 일자, 지역 등 주요 정보를 확인할 수 있습니다.
- 지도 타일은 OpenStreetMap을 사용하므로 지도 화면을 보려면 인터넷 연결이 필요합니다.

## R 설치 및 환경 설정

현재 좌표 지도 미리보기는 R 없이 동작합니다. 다만 R 기반 좌표 이미지 생성이나 별도 분석 스크립트를 함께 사용하는 환경이라면 아래 설정을 권장합니다.

1. CRAN R 다운로드 페이지에 접속합니다.
   - https://cran.r-project.org/bin/windows/base/
2. `Download R-x.x.x for Windows` 설치 파일을 내려받아 실행합니다.
3. 설치 경로는 기본값인 `C:\Program Files\R\R-x.x.x`를 권장합니다.
4. Windows 검색에서 `환경 변수`를 검색한 뒤 `시스템 환경 변수 편집`을 엽니다.
5. `환경 변수` 버튼을 누르고, 사용자 변수 또는 시스템 변수의 `Path`를 선택한 뒤 `편집`을 누릅니다.
6. 아래 경로를 추가합니다. 실제 설치된 R 버전에 맞게 `R-x.x.x` 부분을 바꾸세요.

```text
C:\Program Files\R\R-x.x.x\bin
```

7. 새 PowerShell 창을 열고 아래 명령으로 설정을 확인합니다.

```powershell
R --version
Rscript --version
```

두 명령에서 버전 정보가 출력되면 R 환경 설정이 완료된 것입니다. 명령을 찾을 수 없다고 나오면 PowerShell을 새로 열었는지, `Path`에 추가한 R 버전 경로가 실제 설치 경로와 같은지 확인하세요.

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

빌드 결과는 `dist\BioFlowGBIF_v1.0.3\BioFlowGBIF.exe`처럼 생성됩니다. 같은 버전 폴더가 이미 있으면 덮어쓰지 않고 중단됩니다. 필요하면 `.\build_exe.ps1 -Version 1.0.4`처럼 직접 지정한 버전으로 빌드할 수도 있습니다.

`bioflow_logo.png`는 앱 상단 로고와 창 아이콘으로 사용되며, `build_exe.ps1` 실행 시 배포 폴더에 함께 포함됩니다.

빌드가 완료되면 실행 파일은 아래 경로에 생성됩니다.

```text
dist\BioFlowGBIF_v1.0.3\BioFlowGBIF.exe
```

배포할 때는 `dist\BioFlowGBIF_v1.0.3` 폴더 전체를 압축해서 전달하는 것을 권장합니다. 실행 파일과 필요한 라이브러리, 로고 이미지가 함께 들어 있기 때문입니다.

## 배포 전 확인 사항

- `dist\BioFlowGBIF_v1.0.3\BioFlowGBIF.exe`를 실행해 프로그램이 열리는지 확인합니다.
- 상단에 BioFlow 로고가 표시되는지 확인합니다.
- 샘플 엑셀 파일로 업로드, 시트 선택, 헤더 적용, 결과 확인, 엑셀 저장까지 확인합니다.
- 좌표가 있는 샘플 파일로 `좌표 확인`을 눌러 지도 미리보기가 열리는지 확인합니다.
- 저장 결과 파일에서 날짜가 `YYYY-MM-DD` 형식인지 확인합니다.
- 위도/경도 값이 텍스트 형태로 유지되는지 확인합니다.
# BioFlow-GBIF-Darwin-Core-Mapper
