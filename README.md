# MapleMobMap

## 사전 요구 사항

- Python 3.8 이상

> [WzComparerR2](https://github.com/seotbeo/WzComparerR2)(seotbeo 포크) 빌드본이 `WzComparerR2/`에 동봉되어 있어 별도로 다운로드할 필요가 없습니다.
> (.NET Framework 4.6.2 빌드이며, Windows 10/11에는 기본 내장되어 별도 런타임 설치가 필요 없습니다.)

## 사용 방법

1. `WzComparerR2/WzComparerR2.exe`를 실행하여 MapleStory WZ 파일을 로드합니다.
2. **도구** > **Lua 콘솔**을 선택합니다.
3. **파일** > **열기**를 선택하고 `DumpXml.lua` 파일을 엽니다.
4. F5 키를 눌러 스크립트를 실행합니다. 프로젝트 루트에 `data` 폴더가 바로 생성됩니다.
5. `python main.py`를 실행합니다.

## 계산 방식

분당 경험치는 [Official-like Mob Spawn Rate](https://forum.ragezone.com/threads/official-like-mob-spawn-rate.1164342/) (RageZone, BMS 유출 소스 기반) 문서의 공식 서버 스폰 메커니즘을 재현하여 계산합니다.

- **맵 크기**: foothold(발판)들의 경계 사각형(MBR)으로 계산 (`CFieldMan::RestoreFoothold`)
- **몹 수용량**: `clamp(맵 너비 × 맵 높이 × mobRate × 0.0000078125, 1, 40)`, `fixedMobCapacity`가 있으면 그 값 사용 (`CLifePool::Init`)
- **리젠**: 7초 주기 틱마다 수용량 한도까지 스폰. `mobTime > 0`인 스폰 포인트는 사망 후 `mobTime × 1.3~2.0` 뒤 리젠, `mobTime == -1`은 1회성이므로 제외 (`CLifePool::TryCreateMob`)
- **분당 경험치**: 솔로 플레이 + 스폰 즉시 처치 가정의 정상상태 기대값. 일반 젠은 틱마다 `min(수용량, 스폰 포인트 수) × 평균 경험치`, 시간 젠은 포인트당 `경험치 / (1.65 × mobTime + 3.5초)`
