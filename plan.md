# Plan

## Cross-Reference: 다운로드 사유 ↔ 접속기록 교차 검증

> 다운로드 사유 조회 데이터에 같은 사용자의 접속기록
> ±5분 내 활동 요약을 추가한다.

- [x] `_enrich_with_access_log_summary`: 빈 접속기록
      → 원본 유지 + 빈 요약 컬럼
- [x] `_enrich_with_access_log_summary`: 윈도우 내 매칭
      → 요약 문자열 생성
- [x] `_enrich_with_access_log_summary`: 윈도우 밖
      → 매칭 안 됨
- [x] `_enrich_with_access_log_summary`: 다른 교직원
      → 매칭 안 됨
- [x] `_enrich_with_access_log_summary`: 동일
      프로그램+수행업무 중복 → xN 표시
- [x] `_enrich_with_access_log_summary`: dtype
      불일치 (int vs str) 처리
- [x] `_load_access_logs`: 파일 없으면 None
- [x] `run_check`: 접속기록 있을 때 enrichment 동작
- [x] `run_check`: 접속기록 없을 때 graceful skip

## Cross-Reference 개선: 최근접속기록거리 + 상세내용

> 미매칭 건의 투명성을 위해 가장 가까운 접속기록까지의
> 시간차(분)를 별도 컬럼으로 추가하고,
> 요약에 상세내용 앞 50자를 포함한다.

- [x] config: `COL_NEAREST_ACCESS_GAP` 상수 추가
- [x] `_enrich`: 매칭 시 최근접속기록거리 = 0 표시
- [x] `_enrich`: 미매칭 시 가장 가까운 접속기록까지
      분 단위 거리 표시
- [x] `_enrich`: 접속기록에 해당 교직원 없을 때 NaN
- [x] `_enrich`: 요약에 상세내용 포함 (앞 50자 truncate)
- [x] `_enrich`: 상세내용 컬럼 없을 때 기존 동작 유지

## Login Checker - IP switch reason estimation

> Flagged IP-switch records include a "사유추정" column
> explaining the likely cause.

- [x] `_estimate_ip_switch_reason` returns DataFrame
      with "사유추정" column for empty input
- [x] Same /24 subnet IPs classified as
      "동일 네트워크 내 PC 변경"
- [x] Same /16 but different /24 classified as
      "캠퍼스 내 이동 추정"
- [x] Different /16 networks classified as
      "외부 네트워크 접속 포함"
- [x] Fast IP switch (<=5 min gap, different IPs)
      appends "(빠른 전환)"
- [x] `_filter_ip_switch` output includes "사유추정"
- [x] `_filter_ip_switch` with no flagged records returns
      empty DataFrame with "사유추정" column

## Login Checker - IP switch robustness & per-cluster

> Fix crashes on malformed/NaN IPs and scope reason
> estimation to each flagged cluster, not the whole employee.

- [x] NaN IPs skipped in `_estimate_ip_switch_reason`
- [x] Malformed IPs (not 4 octets) skipped
- [x] NaN IPs excluded from unique count in
      `_filter_ip_switch`
- [x] Per-cluster reason: two separate clusters for
      same employee get independent reasons
- [x] Multi-employee test: two employees get
      different classifications
- [x] Same-IP rapid logins do NOT trigger
      fast-switch suffix
- [x] Fast switch NOT triggered when gap exceeds threshold

## Fix: 접속기록 파일 검색 접두사에서 날짜 제거

> `_load_access_logs`가 `prev_month`로 접속기록 파일을
> 검색하지만, KORUS 파일명은 다운로드 날짜(당월)를
> 사용하므로 파일을 못 찾는 버그 수정.

- [x] `_load_access_logs`에서 `prev_month` 파라미터를
      제거하고 날짜 없이
      `PERSONAL_INFO_ACCESS_LOG_PREFIX`만으로 파일 검색
- [x] 기존 `test_uses_prev_month_for_prefix` 테스트를
      새 동작에 맞게 수정

## 접속기록요약 형식 간소화

> 접속기록요약에서 수행업무(`(조회)`)와 상세내용(`[...]`)을
> 제거하고, 프로그램명과 횟수만 표시한다.

- [x] 요약 형식을 `프로그램명 xN`으로 변경
      (수행업무, 상세내용 제거)

## 접속기록 탐색 윈도우 동적 확장 + 이전 시간만

> 다운로드 이전 접속기록만 탐색하고, 5분→10분→15분으로
> 동적 확장. 요약에 `[N분이내]` 접두사 표기.

- [x] 윈도우를 다운로드 이전 시간만으로 변경 (이후 제외)
- [x] 5분 내 매칭 없으면 10분→15분으로 확장,
      요약에 `[N분이내]` 접두사
- [x] 최근접속기록거리(분)를 이전 시간 기준으로 계산

## 최근접속기록거리 컬럼 제거 + 접속기록요약 너비 제한

> `최근접속기록거리(분)` 컬럼 제거,
> `접속기록요약` 컬럼 Excel 최대 너비 400px(≈57문자) 제한.

- [x] `_enrich_with_access_log_summary`에서
      `COL_NEAREST_ACCESS_GAP` 컬럼 제거
- [ ] `_apply_korus_style`에서 컬럼 최대 너비 상한 적용
      (사용자가 별도 처리 예정)

## IP Switch 사유추정 고도화 — 사설/공인 구분 + 위험도

> 사설/공인 IP 구분으로 사유추정 정확도를 높이고,
> 위험도·고유IP수·고유서브넷수 컬럼을 추가한다.

### Phase 1: `_is_private_ip` 헬퍼

- [x] `_is_private_ip`: 10.x.x.x 사설 판별
- [x] `_is_private_ip`: 172.16-31.x.x 사설 판별
      (경계값 포함)
- [x] `_is_private_ip`: 192.168.x.x 사설 판별
- [x] `_is_private_ip`: 공인 IP → False
- [x] `_is_private_ip`: 비정상 입력 → False

### Phase 2: `_calculate_risk_level` 헬퍼

- [x] `_calculate_risk_level`: 동일서브넷 → 낮음,
      빠른전환 시 → 중간
- [x] `_calculate_risk_level`: 캠퍼스이동/사설간이동
      → 중간
- [x] `_calculate_risk_level`: 사설간이동 + 빠른전환
      → 높음
- [x] `_calculate_risk_level`: 혼용/공인전환 → 높음

### Phase 3: 분류 로직 개선

- [x] 모두 사설 + 다른 /16 → "사설 네트워크 간 이동"
      (기존 테스트 수정 포함)
- [x] 사설 + 공인 혼합 → "사설/공인 네트워크 혼용"
- [x] 모두 공인 → "공인 네트워크 간 전환"

### Phase 4: 위험도 + 분석 컬럼

- [x] 출력에 위험도 컬럼 존재 + 같은 /24 → "낮음"
- [x] 사설간이동 + 빠른전환 → 위험도 "높음"
- [x] 고유IP수, 고유서브넷수 컬럼 정상 출력
- [x] 빈 입력 / 빈 필터 결과에도 신규 컬럼 포함
