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
