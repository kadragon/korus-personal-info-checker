# 성능 분석 — KORUS 개인정보 점검 파이프라인

> 측정 기반 분석. 추정 아님. 재현: `tools/bench_perf.py`, `tools/bench_filters_parity.py`, `tools/bench_write_and_stress.py`
> 데이터 형상(사용자 확인): 월 10만~100만 행 · 사용자당 ≤1천 건 · `.xlsx` 소수 · 현재 수 분.
>
> **구현 상태 (branch `perf/pipeline-hotpaths`):** §3 로드맵 1~5 완료 — 필터 벡터화(동결 테스트 동반),
> 재파싱 제거(2a), calamine `.xlsx` 읽기, 캐시 라우팅. **2b(셀 루프 제거)는 외형 검증 필요로 보류.**
> 검증: 193 tests green · 동결 테스트 4 추가 · E2E 스모크 통과 · ruff/mypy/bandit clean · coverage 96%.

## TL;DR — 측정으로 뒤집힌 결론

정적 분석의 직관(O(n²)가 범인)은 **틀렸다**. 측정 결과 진짜 병목은:

| 순위 | 병목 | 원인 | 측정(100k행) | 수정 후 | 배율 |
|---|---|---|---|---|---|
| 1 | `_filter_ip_switch` + `_filter_high_freq_download` | **per-row pandas 오버헤드** (`.iloc[i]` + 행마다 DataFrame 불리언 마스킹) | 20.4s + 17.0s = **37.4s** | 0.49s + 0.075s | **43× / 222×** |
| 2a | `save_excel_with_autofit` 재파싱 낭비 | `to_excel`→`load_workbook`(전체 재파싱)→style→**save 2회** | 13.2s 중 ~3.4s | 재파싱 제거(기존 스타일 유지) | **1.31× (증명·출력동일)** |
| 2b | `_apply_korus_style` 셀 단위 2회 루프 | 셀마다 `ws.cell()`+`_display_width` | 13.2s 중 **7.7s** | xlsxwriter 단일 패스 | **~6.6× (외형 포팅 검증필요)** |
| 3 | `pd.read_excel(openpyxl)` | 느린 순수-Python 파서 | 1.47s/파일 | calamine(Rust) 0.31s | **4.8×** |
| 4 | `_load_access_logs` 중복 읽기 | 캐시 우회(`load_merged_excel`) | 1.5s | 0 (캐시 재사용) | 제거 |

**O(n²)는 이 형상에서 노이즈** (사용자당 ≤1천 → 최대 10⁶ 연산). 37초의 정체는 알고리즘이 아니라
**행마다 pandas 스칼라 접근/마스킹 상수**(~200µs/행)다. 총 행수에 선형 비례 → 데이터 늘면 더 악화.

**언어 교체 불필요.** 한계는 CPython이 아니라 (1) Excel 라이브러리 (2) per-row pandas 패턴 (3) 순수-Python 셀 스타일링.
셋 다 Python 안에서 해결된다. Rust/Go 재작성은 이미 Rust인 calamine·polars를 재발명하는 꼴.

---

## 1. 측정 베이스라인 (100k행 / 사용자 2000명, max 74행/사용자)

```
[READ]   pd.read_excel(openpyxl)      1465 ms   →  calamine        306 ms   (4.8×)
[WRITE]  save_excel_with_autofit 분해:
  1. df.to_excel(openpyxl)            1815 ms
  2. openpyxl.load_workbook           1650 ms   ← 방금 쓴 파일을 전부 재파싱(순수 낭비)
  3. _apply_korus_style (2x 셀 루프)   7743 ms   ← 셀마다 ws.cell()+_display_width 호출
  4. wb.save                          1964 ms
     CURRENT 합계                    13172 ms   →  xlsxwriter 단일패스  1976 ms  (6.6×)
[FILTERS]
  _filter_ip_switch                  20424 ms   →  벡터화            492 ms   (43×)
  _filter_high_freq_download         17001 ms   →  벡터화             75 ms   (222×)
  _check_download_sayu (.apply)         61 ms   (미미)
  _enrich_with_access_log (py loop)   1027 ms   (중간)
```

### 500k행 측정 — 깨끗한 선형 스케일 (≈5×)

```
[READ]  openpyxl   7046 ms   →  calamine 1620 ms   (4.3×)
[WRITE] CURRENT   65588 ms   (이 중 _apply_korus_style 셀 루프 = 38738 ms)
        xlsxwriter 9850 ms   (6.7×)
[FILTERS] ip_switch 102593 ms · high_freq 83303 ms · enrich 5350 ms
```

전체 파이프라인(4개 체커)은 원본 raw 덤프를 **4번** 스타일 저장(login·personal·download·ncmarm) +
필터 2종을 돌린다. 500k행 기준 두 항목만으로:
- **4× 스타일 raw 저장 = 4 × 65.6s = 262s** (스타일 셀 루프만 4×38.7=155s)
- **2× 필터 = 102.6 + 83.3 = 186s**

→ 합쳐 ~7.5분, 읽기·필터 출력까지 더하면 **500k에서 단일 실행 ~10분**, 1M이면 ~20분.
지금은 "수 분"이라도 데이터가 커지면 선형으로 그대로 끌려 올라간다.

> **투영(500k 기준):**
> - 무위험·증명된 수정만(필터 벡터화 + calamine + 재파싱제거 2a + 캐시): ~10min → **~3.3min (≈3×)**.
>   잔여 비용 대부분은 셀 루프(4×~47s)다 → 2b가 큰 수의 관문.
> - 2b(셀 루프 제거)까지 포함: ~10min → **~55s (≈10×)**. 단 2b는 외형 검증 통과 후.

---

## 2. 병목별 처방

### #1 두 필터 벡터화 — 최대 효과, 검증 완료 ✅

**문제.** 두 함수가 동일 안티패턴:
```python
for _, group in df.groupby(...):          # 그룹마다
    for i in range(len(group)):           # 행마다
        cur = group.iloc[i][TIME]         # 느린 스칼라 접근
        win = group[(group[TIME] >= cur) & (group[TIME] <= cur+W)]  # 매 행 새 DataFrame
```
비용은 알고리즘이 아니라 행당 pandas 객체 생성. 총 행수 × ~200µs.

**처방.** 그룹당 numpy 배열을 한 번만 뽑고, 윈도 경계를 `searchsorted`로 계산 → 차분배열로 플래그 합집합.
윈도 경계를 **비트 단위로 동일**하게 유지:
```
원본 mask:  (t >= t_i) & (t <= t_i+W)
대체:       lo_i = searchsorted(t, t_i,   "left")   # 첫 t>=t_i
            hi_i = searchsorted(t, t_i+W, "right")  # 첫 t> t_i+W  → [lo_i, hi_i)
플래그 = qualifying i 들의 [lo_i,hi_i) 합집합 (np.add.at 차분배열, 벡터화)
```

**검증 (필수 게이트 — 탐지 결과 불변).** `tools/bench_filters_parity.py` + `tools/bench_write_and_stress.py`:
- random / burst / **동률 타임스탬프 / NaN IP / 빈 입력 / 단일 행** 전 케이스에서
  플래그된 원본 인덱스 집합 **완전 일치**, IP 검사는 `사유추정/위험도/고유IP수/고유서브넷수` 컬럼까지 일치.
- 속도: high_freq 16721→75ms(222×), ip_switch 21068→492ms(43×).
- → PIPA 컴플라이언스 도구이므로 "다른 행을 플래그하는 빠른 필터"는 버그.

**커밋할 회귀 테스트 주의.** parity 하니스는 *신규 vs 원본* 비교다 — 원본을 교체하면 비교 대상이 사라진다.
`tests/`에 고정할 테스트는 **시드 고정 픽스처 → 알려진 플래그 인덱스 집합(+사유/위험도 컬럼)을 동결**해
신규 함수 단독으로 단언해야 한다. 순서: [TEST] 동결 → [REFACTOR] 교체.

**한계 (정직하게).** 빠른 `_filter_ip_switch`는 그룹당 `for i in range(n)` + `np.unique`(거리 윈도 distinct count)를 유지한다.
한 사용자가 매우 무거우면 그룹 내부에서 다시 커진다: 측정상 60k행을 **전원 ~857행/사용자**(병적 케이스)로 몰면 3.4s
— 그래도 원본(~20s+)보다 빠르다. 실제 형상(소수 heavy + 다수 light)에선 비용이 소수 heavy 사용자에 집중되어
1M행에서도 sub-초~수초 수준. 단일 사용자가 수천 행을 넘기 시작하면 distinct-count를 완전 벡터화(팩터화+세그먼트 방식)로 한 단계 더 내릴 수 있다.

### #2 스타일 저장 — 두 부분으로 분리(증명 vs 검증필요)

**문제.** `save_excel_with_autofit`이 데이터를 3번 통과: 쓰기 → `load_workbook`(전체 재파싱) → 셀 2회 루프 → 다시 쓰기.
`_apply_korus_style`은 셀마다 `ws.cell()` 접근 + `_display_width()` 문자별 유니코드 조회 = 100k행에서 7.7s.

**2a. 재파싱 제거 — 즉시 적용 가능·출력 바이트 동일·증명됨 ✅**
`to_excel`이 이미 in-memory 워크북을 만든다 → 그걸 디스크에서 다시 읽을 이유가 없다. 기존 스타일 코드 그대로:
```python
with pd.ExcelWriter(path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)
    _apply_korus_style(writer.book.active)   # 기존 함수 재사용
# context 종료 시 1회 저장 (load_workbook 제거 + 이중 save 제거)
```
`tools/bench_write_and_stress.py` 측정: 14431→11058ms(**1.31×**), 셀 값·컬럼 폭 **완전 동일**. 위험 0.

**2b. 셀 루프(7.7s) 제거 — ~6.6× 가능하나 외형 포팅 검증 필요 ⚠️**
`_apply_korus_style`의 셀 단위 루프가 진짜 monster(500k에서 38.7s). 이걸 없애려면 write-time 포맷팅
(xlsxwriter, 또는 openpyxl `write_only`)로 포팅해야 한다. 벤치의 단일패스 측정(1.98s)은 **간이 writer**라
다음을 누락했다 — 그래서 "6.6×"는 *목표치*이지 증명 아님:
- CJK 폭 가중(`_display_width`) / 컬럼별 좌·중 정렬 임계 / 행 높이(헤더·데이터) / **셀별 테두리**.
- 함정 1: 행 높이를 `set_row` 행마다 호출하면 O(rows) 새 병목 → `set_default_row`+헤더만 처리.
- 함정 2: pandas `to_excel(engine="xlsxwriter")`는 셀마다 자체 포맷으로 써서 `set_column` 테두리가 **셀에 안 닿음**.
  모든 데이터 셀 테두리 재현이 실제 난점 → 수동 write 또는 `write_only` 필요.
- 컬럼 폭만은 df에서 벡터 산출 가능(셀 루프 불필요): `df[col].astype(str).map(_display_width).max()`.

**주의(외형은 납품물).** `[붙임2]…_{월}.xlsx`는 `ZIP_FILE_PREFIXES`에 들려 압축·납품된다. 스타일을 **빼지 말 것**.
2b는 외형 픽셀 동등성 회귀 테스트(셀 값+폭+정렬+테두리+행높이 스냅샷)를 통과해야 머지. 큰 raw 덤프의
스타일 자체를 줄일지는 사용자 결정사항. → **먼저 2a(무위험)로 확정 이득, 2b는 포팅+검증 후.**

### #3 calamine 읽기 엔진 — 4.8×, 한 줄 변경

`_merge_and_preprocess_files`의 `pd.read_excel(file_path)` → `pd.read_excel(file_path, engine="calamine")`.
- python-calamine(Rust) 검증: pandas 3.0.3에서 **`.xlsx` 직접 측정 4.8× (1465→306ms)**.
- `.xls`는 calamine 문서상 지원하나 **여기서 미측정**(사용자 데이터는 `.xlsx`라 무관). 전환 시 `.xls` 별도 확인.
- `python-calamine`을 `dependencies`에 추가 필요.
- `pd.to_datetime(...)`도 `format=` 명시 시 추론 비용 제거(소폭).

### #4 접속기록 캐시 재사용 — 중복 읽기 제거, 무위험

`download_reason_checker._load_access_logs()`가 `load_merged_excel`(비캐시)로 접속기록을 다시 읽는다.
그런데 `personal_file_checker`가 **먼저** 같은 접두사(`개인정보 접속기록 조회_`) 파일을 `load_access_logs_cached`로 이미 읽어 캐시가 따뜻하다(CHECKER_ORDER: login→personal→download).
→ `_load_access_logs`를 `load_access_logs_cached`로 라우팅하면 접속기록 전체 1회 읽기가 사라진다. 출력 불변.

### (후순위) `_enrich_with_access_log_summary` / `_estimate_ip_switch_reason`
- enrich: 다운로드 행마다 py 루프 + `np.searchsorted`. 1s 수준이라 후순위. 그룹 벡터화 여지 있음.
- estimate: 이미 필터된 소량에만 동작 → 영향 작음. `.iloc[i]`/`result.loc[idx]=` 반복은 정리하면 깔끔.

---

## 3. 권장 실행 순서 (효과 ÷ 위험)

1. **[TEST]** 두 필터 출력을 **동결**한 회귀 테스트 (시드 픽스처 → 알려진 플래그 집합). 안전망 먼저.
2. **[REFACTOR]** 두 필터 벡터화 교체 → 37s(100k)/186s(500k) 제거. 최대 효과·검증 완료.
3. **[PERF]** 2a 재파싱 제거(무위험·증명됨) 먼저 적용 → 즉시 1.31×.
4. **[PERF]** `read_excel(engine="calamine")` + `python-calamine` 의존성 추가 (`.xlsx` 4.8× 증명).
5. **[REFACTOR]** `_load_access_logs` → `load_access_logs_cached` 라우팅 (중복 읽기 제거).
6. **[PERF]** 2b 셀 루프 제거(xlsxwriter/`write_only` 포팅) — **외형 픽셀 동등성 회귀 테스트 통과 후** 머지.
7. (선택) enrich 그룹 벡터화, `to_datetime(format=...)`, 단일 사용자 초대형 시 distinct-count 완전 벡터화.

각 단계는 독립 커밋 + 동등성/회귀 테스트. 골든 원칙 #1(탐지 결과 불변) 위반 시 머지 금지.
순서 의도: **무위험·증명된 이득(1–5) 먼저, 외형 검증이 필요한 2b(6)는 뒤로.**

---

## 4. 언어 교체 — 정면 답변

**Python을 바꿀 이유 없음.** 병목은 언어가 아니라 라이브러리·패턴 선택이었다:

| 후보 | 평가 |
|---|---|
| **유지 + 위 처방** | ✅ 권장. numpy 벡터화·calamine·재파싱제거(증명분)만 ~3×, 셀루프 포팅(2b)까지 ~10×. 위험 최소, 코드베이스 보존. |
| **Polars** | 멀티스레드 groupby/filter로 추가 이득 가능. 단 Excel 외형 저장은 여전히 xlsxwriter 필요, 전면 포팅은 과함. 1M+ 상시화되면 hot path만 polars 검토. |
| **DuckDB** | 대용량 집계·디스크 스필 강점. 현 형상엔 과투자. |
| **Rust/Go 재작성** | ❌ 비권장. calamine(Rust)·polars(Rust)를 Python에서 이미 호출 가능 → 재작성은 그걸 재발명. |

**재작성 트리거(측정 기준).** 위 처방 적용 후에도 실데이터에서 목표 시간을 못 맞추면 그때 hot path만 포팅.
"느낌"이 아니라 `tools/bench_perf.py` 수치로 판단.

---

## 5. 재현

```bash
uv pip install python-calamine xlsxwriter polars   # 벤치 전용 (.venv에만, pyproject 미반영 → uv sync 시 제거됨)
uv run python tools/bench_perf.py --rows 100000 --users 2000      # 스테이지별 분해
uv run python tools/bench_filters_parity.py                       # 필터 동등성 + 속도 증명
uv run python tools/bench_write_and_stress.py                     # 재파싱-제거 동일성 + 1000/user 스트레스
```

**측정 한계 (수치는 보수적).**
- 합성 데이터는 컬럼이 좁다(3~6개). 실제 KORUS export는 더 넓다 → 읽기·쓰기는 O(행×열)이라
  **실제 write/read 비용은 측정보다 크다**(= write 수정의 가치가 더 큼, 결론 강화).
- 벤치는 `main()` end-to-end가 아니라 스테이지 분해 + 합산 투영이다(분해가 더 유용). 실파일 1회 전체 실행으로
  스테이지 합성이 가정대로인지 최종 확인하면 좋음(필수 아님).
- 벤치 라이브러리는 `.venv`에만 설치됨. 실제 채택 시 `python-calamine`(필수)·`xlsxwriter`(2b 채택 시)를
  `pyproject.toml [dependencies]`에 명시할 것. `polars`는 현재 권장 아님(후순위).
