## Cross-Reference: 다운로드 사유 ↔ 접속기록 교차 검증

> 다운로드 사유 조회 데이터에 같은 사용자의 접속기록 ±5분 내 활동 요약을 추가한다.

- [x] `_enrich_with_access_log_summary`: 빈 접속기록 → 원본 유지 + 빈 요약 컬럼
- [x] `_enrich_with_access_log_summary`: 윈도우 내 매칭 → 요약 문자열 생성
- [x] `_enrich_with_access_log_summary`: 윈도우 밖 → 매칭 안 됨
- [x] `_enrich_with_access_log_summary`: 다른 교직원 → 매칭 안 됨
- [x] `_enrich_with_access_log_summary`: 동일 프로그램+수행업무 중복 → xN 표시
- [x] `_enrich_with_access_log_summary`: dtype 불일치 (int vs str) 처리
- [x] `_load_access_logs`: 파일 없으면 None
- [x] `run_check`: 접속기록 있을 때 enrichment 동작
- [x] `run_check`: 접속기록 없을 때 graceful skip

## Cross-Reference 개선: 최근접속기록거리 컬럼 + 상세내용 포함

> 미매칭 건의 투명성을 위해 가장 가까운 접속기록까지의 시간차(분)를 별도 컬럼으로 추가하고,
> 요약에 상세내용 앞 50자를 포함한다.

- [x] config: `COL_NEAREST_ACCESS_GAP` 상수 추가
- [x] `_enrich`: 매칭 시 최근접속기록거리 = 0 표시
- [x] `_enrich`: 미매칭 시 가장 가까운 접속기록까지 분 단위 거리 표시
- [x] `_enrich`: 접속기록에 해당 교직원 없을 때 NaN
- [x] `_enrich`: 요약에 상세내용 포함 (앞 50자 truncate)
- [x] `_enrich`: 상세내용 컬럼 없을 때 기존 동작 유지

## Login Checker - IP switch reason estimation

> Flagged IP-switch records include a "사유추정" column explaining the likely cause.

- [x] _estimate_ip_switch_reason returns DataFrame with "사유추정" column for empty input
- [x] Same /24 subnet IPs classified as "동일 네트워크 내 PC 변경"
- [x] Same /16 but different /24 classified as "캠퍼스 내 이동 추정"
- [x] Different /16 networks classified as "외부 네트워크 접속 포함"
- [x] Fast IP switch (<=5 min gap, different IPs) appends "(빠른 전환)"
- [x] _filter_ip_switch output includes "사유추정" column
- [x] _filter_ip_switch with no flagged records returns empty DataFrame with "사유추정" column

## Login Checker - IP switch reason robustness & per-cluster estimation

> Fix crashes on malformed/NaN IPs and scope reason estimation to each flagged cluster, not the whole employee.

- [x] NaN IPs skipped in _estimate_ip_switch_reason (no crash)
- [x] Malformed IPs (not 4 octets) skipped in _estimate_ip_switch_reason (no crash)
- [x] NaN IPs excluded from unique count in _filter_ip_switch (no false positives)
- [x] Per-cluster reason: two separate clusters for same employee get independent reasons
- [x] Multi-employee test: two employees get different classifications
- [x] Same-IP rapid logins do NOT trigger fast-switch suffix
- [x] Fast switch NOT triggered when gap exceeds threshold
