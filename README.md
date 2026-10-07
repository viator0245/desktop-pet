# Sakuragi Desktop Pet · 강백호 데스크톱 펫

Windows 10/11용 Python/PySide6 데스크톱 농구 펫. **현재 포함된 캐릭터는 직접 그린 일반 농구 선수 placeholder**입니다. 실제 강백호 이미지나 인터넷에서 가져온 캐릭터 이미지는 포함하지 않습니다. 캐릭터 PNG만 교체하면 같은 행동 루프를 사용할 수 있습니다.

모니터마다 독립적인 선수·공·골대가 나타납니다. 기본 동작은 **드리블하며 3회 왕복 → 제자리 슛 → 랜덤 성공/실패 → 표정 리액션 → 바닥에서 공 회수 → 시작점 복귀**를 무한 반복합니다. 일반 창 배경·제목줄은 없습니다. 각각의 작은 투명 창을 사용하며 전체 화면을 30 FPS로 다시 그리지 않습니다.

## 설치 및 실행 (Windows PowerShell)

Python 3.10 이상, 권장 Python 3.12 64-bit. Python 설치 시 PATH를 등록하세요.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

PowerShell에서 activate 실행이 정책으로 제한되어 있으면 활성화 없이 실행할 수 있습니다.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

프로그램이 바로 일반 창을 띄우지 않는 것은 정상입니다. 각 화면 오른쪽 아래에 작은 선수와 골대가 나타나고, 트레이에 주황색 공 아이콘이 생깁니다. 숨겨진 트레이 아이콘 목록도 확인하세요.

## 트레이와 설정

우클릭 메뉴: Pause, Resume, Reset Position, Reload Assets, Settings, Run at Windows Startup, Exit.

- **Pause / Resume**: 모든 화면의 이동·공·프레임을 함께 정지/재개합니다. 정지 중에는 프레임 타이머도 멈춥니다.
- **Reset Position**: 모든 화면의 현재 슛과 진행 상태를 버리고 왼쪽 시작점부터 다시 시작합니다.
- **Settings**: 외부 `config.json`을 기본 편집기로 엽니다. 저장 후 **Reload Assets**를 선택하면 설정과 PNG를 함께 다시 읽고 루프를 초기화합니다. 잘못된 설정/이미지는 오류를 표시하고 기존 장면을 유지합니다.
- **Run at Windows Startup**: 현재 사용자 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`의 `SakuragiDesktopPet` 항목을 켜거나 끕니다. 관리자 권한은 필요하지 않습니다. exe나 프로젝트를 이동했다면 이 항목을 껐다가 다시 켜세요.
- **Exit**: 모든 창과 타이머를 종료합니다.

`config.json`은 소스 실행 시 프로젝트 루트, 패키지 실행 시 **exe 옆**에서 읽습니다. `--config C:\path\config.json`으로 지정할 수도 있습니다. 단독 exe에 외부 설정이 없으면 번들 설정을 읽으며 Settings가 편집용 외부 파일을 생성합니다.

| 설정 | 기본값 | 의미 |
| --- | --- | --- |
| `scale` | 1.0 | 화면의 논리 픽셀 기준 전체 크기 |
| `move_speed` | 80 | 초당 이동 논리 픽셀 (scale 적용) |
| `fps` | 30 | 1–30, 렌더링 타이머 목표 FPS |
| `patrol_width` | 700 | 오른쪽 정지점으로부터 왼쪽 이동 거리 (scale 적용) |
| `animation_speed` | 1.0 | sprite 재생·드리블 주기 배율; 이동 속도는 별도 |
| `shot_make_probability` | 0.5 | 0–1, 매 슛 성공 확률 |
| `laps_before_shot` | 3 | 슛 전 왕복 횟수 |
| `reaction_duration` | 1.2 | 성공/실패 표정 유지 초 |
| `always_on_top` | true | 일반 앱보다 위에 표시 |
| `sprite_canvas` | [256,256] | sprite 기준 캔버스 크기 |
| `sprite_display_height` | 144 | 기준 캔버스의 표시 높이 |
| `sprite_fps` | 10 | PNG 프레임 재생 속도 |
| `sprite_foot_anchor` | [128,256] | metadata가 없는 프레임의 기본 발 앵커 |
| `safe_margin` | 24 | 순찰 중 골대와 캐릭터 사이 간격 |

작은 해상도에서는 캐릭터·골대·궤적이 화면에 들어가도록 전체 scale을 자동으로 줄입니다. PNG 프레임은 미리 로드하고 재사용합니다. 골대 창은 배치가 변할 때만 다시 그립니다. 공은 캐릭터 그림과 분리되어 관리됩니다.

## Windows 투명 창과 작업표시줄

Qt `FramelessWindowHint`, `WindowStaysOnTopHint`, `WindowTransparentForInput`, `WindowDoesNotAcceptFocus`, `WA_TranslucentBackground`를 사용합니다. Windows 네이티브 창 생성 시 ctypes로 다음 확장 스타일을 추가하고 `SetWindowPos`를 적용합니다.

- `WS_EX_LAYERED` — 투명 레이어
- `WS_EX_TRANSPARENT` — 뒤의 다른 프로그램으로 클릭 통과
- `WS_EX_TOOLWINDOW` — 작업표시줄/Alt+Tab의 일반 앱 창으로 등록하지 않음
- `WS_EX_NOACTIVATE` — 포커스 획득 방지

`SHAppBarMessage(ABM_GETSTATE)`의 `ABS_AUTOHIDE` 비트로 Windows 작업표시줄 자동 숨김 설정을 읽습니다.

- **자동 숨김 OFF**: 해당 `QScreen.availableGeometry()`의 아래쪽 경계를 floor로 사용합니다. 아래/위/좌/우 작업표시줄 및 예약된 작업 영역에 대응하며 높이를 하드코딩하지 않습니다.
- **자동 숨김 ON**: 해당 `QScreen.geometry()`의 아래쪽 경계를 floor로 사용합니다. 마우스로 작업표시줄이 잠깐 나타나도 `availableGeometry()`를 사용하지 않으므로 선수나 골대가 위로 튀지 않습니다.

Qt QRect의 `bottom()`은 마지막 포함 픽셀이므로, 렌더링 기준 바닥 경계는 `y + height`입니다. Win32 물리 픽셀 좌표와 Qt 논리 픽셀 좌표를 섞지 않습니다. Windows 10/11의 자동 숨김 설정은 시스템 단위로 읽고 각 모니터의 작업 영역은 따로 계산합니다. 제3자 작업표시줄이 모니터별로 다른 숨김 규칙을 제공하는 경우는 지원 대상이 아닙니다.

## 멀티모니터

`QApplication.screens()`로 현재 화면마다 `MonitorController`를 만듭니다. 각 controller에 별도의 `StateMachine`, 랜덤 생성기, `Ball`, `Layout`, 타이머와 작은 창 세 개가 있습니다. 공유하는 PNG 캐시 외에 행동 상태를 공유하지 않습니다.

`screenAdded` / `screenRemoved`와 화면의 `geometryChanged`, `availableGeometryChanged`, `logicalDotsPerInchChanged`에 대응합니다. 작업표시줄 설정도 1초마다 다시 확인합니다. 좌표가 바뀌면 해당 화면의 루프를 재배치·초기화하여 비행 중 공이 새 화면 밖으로 나가지 않게 합니다. 자동 숨김 상태에서 작업 영역만 순간적으로 바뀌면 기존 상태를 유지합니다. 새 모니터도 Pause 상태를 따릅니다. 음수 좌표, 세로 위치가 다른 화면, 서로 다른 DPI는 Qt의 논리 좌표 체계를 사용합니다.

## 상태 머신 및 슛

`src/state_machine.py`는 enum과 상태별 handler dispatch table을 사용합니다.

```text
idle
 → walk_to_hoop → turn_at_hoop → walk_back → turn_at_start
   └─ 왼쪽에 완전히 돌아올 때 completed_laps += 1
   └─ 3회 미만이면 다시 walk_to_hoop
 → shoot_prep → shoot_release → ball_in_flight
 → shot_made / shot_missed
 → reaction_success / reaction_miss
 → (필요하면 ball_falling / ball_bouncing에서 기다림)
 → walk_to_ball → pickup_ball → return_to_start
 → completed_laps = 0 → turn_at_start → 반복
```

공은 `dribbling`, `held`, `shot`, `falling`, `bouncing`, `grounded` 모드를 별도로 가집니다. 리액션 중에도 공의 낙하·바운스는 계속됩니다. 바닥에서 공이 멈춘 뒤 회수를 시작합니다. pickup의 가장 깊이 숙이는 순간에 공을 손에 붙입니다.

매 슛 `random.random() < shot_make_probability`로 결과를 정합니다. `src/shot.py`에서 발사 지점과 목표, 정점 높이로 초속도와 비행 시간을 계산합니다. 경로는 `x=x0+vx*t`, `y=y0+vy*t+0.5*g*t²`입니다.

- 성공: 내려오는 궤적으로 림 중앙 통과 → 네트 아래 낙하 → 바닥 두 번 바운스 → 정지.
- 실패: 림 왼쪽 가장자리와 공 반지름이 접하는 위치까지 비행 → 충돌 순간 속도가 반전되며 위/옆으로 반동 → 감쇠된 움직임으로 골대 아래 착지 → 두 번 바운스 → 정지. 현재 버전은 **림 충돌 실패**를 구현하며, 백보드 충돌 좌표는 metadata/Layout에 준비되어 있습니다.

## 실제 강백호 sprite 넣기

인터넷 다운로드 기능은 없습니다. 사용자가 제공한 transparent RGBA PNG를 아래 폴더에 넣습니다. 기존 placeholder 파일은 **폴더별로 삭제하고** 실제 프레임으로 교체하세요. 남은 placeholder가 함께 재생되지 않도록 합니다. 골대와 농구공은 그대로 사용할 수 있습니다.

```text
assets/
  sakuragi/
    idle/                 01.png, 02.png, ...
    walk_dribble/         01.png, 02.png, ...
    shoot_prep/           01.png, 02.png, ...
    shoot_release/        01.png, 02.png, ...
    reaction_success/     01.png, 02.png, ...
    reaction_miss/        01.png, 02.png, ...
    pickup_ball/          01.png, 02.png, ...
    metadata.json
  basketball.png
  hoop/
    hoop.png
    metadata.json
```

파일은 이름순으로 정렬됩니다. 100프레임 이상이면 `001.png` 등 같은 자릿수를 사용하세요. 폴더가 비어 있으면 그 동작에만 procedural placeholder를 사용합니다. 공/골대 이미지가 없어도 procedural fallback이 동작합니다. **Reload Assets**로 빌드 없이 교체할 수 있습니다.

exe 배포 시 외부 `assets/` 폴더를 exe 옆에 둡니다. 외부 assets 폴더가 있으면 이를 사용하고, 없으면 내부 번들을 사용합니다. 일부 동작만 외부에 넣었을 때 나머지 동작은 procedural fallback입니다.

### 필요한 동작과 규격

| 폴더 | 권장 프레임 | 요구 동작 |
| --- | --- | --- |
| idle | 1–8 | 편안한 정지 자세 |
| walk_dribble | 6–12 | 공이 없는 걷기/드리블 손 자세 |
| shoot_prep | 4–8 | 공을 얼굴 앞까지 올리는 준비 |
| shoot_release | 4–8 | 팔을 뻗고 손목을 꺾는 슛/팔 유지 |
| reaction_success | 4–12 | 웃음과 주먹 올리기 |
| reaction_miss | 4–12 | 눈 크게 뜨기/당황 |
| pickup_ball | 8–12 | 서기 → 깊이 숙이기 → 다시 서기 |

기본 **256×256 RGBA**, 오른쪽을 바라보고, 공을 sprite에 포함하지 않습니다. 발바닥 기준 앵커는 `[128,256]`. 표시 높이는 기본 144 logical px입니다. 이미지 크기를 바꾸면 `sprite_canvas`, `sprite_foot_anchor`를 수정하고 metadata도 함께 수정하세요. 왼쪽 이동은 같은 PNG를 발 앵커 기준으로 수평 반전합니다.

프레임별 크기나 여백이 다르면 `assets/sakuragi/metadata.json`에서 발 앵커와 손 앵커를 지정합니다. **프레임마다 잘못 남아 있는 placeholder metadata도 반드시 교체하세요.** 좌표는 각각의 원본 이미지 픽셀 기준입니다. 기본 캔버스에 비해 과도하게 큰 프레임은 순찰 안전 간격에도 영향을 주므로 일관된 캔버스를 권장합니다.

```json
{
  "default_foot_anchor": [128, 256],
  "default_hand_anchor": [177, 159],
  "frames": {
    "idle/01.png": {
      "foot_anchor": [128, 256],
      "hand_anchor": [177, 159]
    },
    "pickup_ball/06.png": {
      "foot_anchor": [126, 252],
      "hand_anchor": [175, 238]
    }
  }
}
```

`foot_anchor`가 매 프레임 동일한 화면상의 발 위치에 정렬됩니다. 이 위치가 캐릭터의 이동 중심 pivot 역할도 합니다. `hand_anchor`는 드리블의 x 위치, 슛 준비/릴리즈와 pickup의 공 부착 지점입니다. pickup은 1.1초 전체에 걸쳐 프레임을 한 번 재생하며 중앙 시점(0.55초)에 공을 붙이므로 중앙 프레임의 손이 바닥 공 위치에 닿게 하세요. 공통 foot/hand 값이 있으면 default 필드를 사용합니다.

골대 metadata:

```json
{
  "canvas": [150, 230],
  "floor_anchor": [75, 230],
  "rim_center": [48, 73],
  "rim_radius": 20,
  "backboard_x": 95
}
```

골대 원본 이미지 안의 좌표입니다. 공 반지름은 10 기준 단위이고 림 반지름은 그보다 커야 합니다. 바닥 앵커는 골대 받침의 바닥 y좌표입니다. 골대를 바꾸면 이미지와 metadata를 함께 교체하세요. 전체 canvas가 기본 단위의 크기이므로 큰 고해상도 골대는 이 좌표 공간에 맞춰 리사이즈하거나 동일한 비율의 표시 크기를 고려해 `scale`을 조절하세요.

직접 작성된 placeholder를 다시 생성하려면 `python tools/generate_placeholders.py`를 실행합니다. 이 명령은 assets 안의 같은 파일을 **덮어쓰므로 실제 sprite를 넣은 뒤에는 실행하지 마세요.**

## .exe 빌드

**Windows에서 빌드하세요. PyInstaller는 Linux에서 Windows exe로 크로스 컴파일하지 않습니다.** 프로젝트 전체 파일이 필요하며 Python/PySide6는 exe에 포함됩니다.

간편하게 `build_windows.bat`를 실행하거나:

```powershell
.venv\Scripts\python.exe tools\build.py --onefile
```

결과: `dist\SakuragiDesktopPet.exe`, `dist\config.json`, `dist\assets\`. 이 세 항목을 함께 배포하면 설정과 이미지를 쉽게 교체할 수 있습니다. exe만 배포해도 번들 placeholder와 기본 설정으로 실행됩니다.

수동 PyInstaller 명령:

```powershell
pyinstaller --noconsole --onefile --name SakuragiDesktopPet --add-data "assets;assets" --add-data "config.json;." main.py
Copy-Item config.json dist\config.json
Copy-Item assets dist\assets -Recurse -Force
```

빠른 시작과 디버깅에 유리한 폴더형 빌드는 `python tools/build.py`로 만듭니다. 결과는 `dist\SakuragiDesktopPet\SakuragiDesktopPet.exe`입니다. `.github/workflows/build-windows.yml`에는 Windows 테스트·onefile 빌드·패키지 시작 smoke test·배포 artifact 생성이 준비되어 있습니다. 이 저장소에 업로드하고 GitHub Actions에서 실행할 수 있습니다.

## 검증

```powershell
python -m unittest discover -s tests -v
python tools\windows_check.py
python main.py --smoke-seconds 5
```

자동 테스트는 3회 왕복, 성공/실패 전체 회수 루프, 림 충돌 속도, 두 번 바운스 후 정지, 음수 모니터 좌표, 작은 화면, 확률/모니터 독립성, PNG alpha, 프레임별 앵커, 창 속성, Pause/Reset/Reload, 가상 hotplug, 자동 숨김 중 임시 작업 영역 변경을 확인합니다.

`tools/windows_check.py`는 **실제 Windows 데스크톱에서** 네이티브 확장 스타일·제목줄 없음·모니터별 floor를 자동 확인합니다. Linux/offscreen에서는 실행할 수 없습니다. 실제 Chrome/Excel 클릭 통과, 트레이 표시, DPI/배치 변경, 작업표시줄이 나타날 때의 z-order는 다음 수동 확인이 필요합니다.

1. Chrome/Excel 위에서 캐릭터/공/골대를 클릭해 뒤의 앱이 클릭되는지 확인.
2. 작업표시줄 자동 숨김 OFF/ON을 바꾸어 floor 변화 확인. ON에서 마우스로 작업표시줄을 열어도 캐릭터가 올라가지 않는지 확인.
3. 확장 모니터를 연결·분리하고 해상도/DPI/좌우·상하 배치를 바꿔 각 화면에서 장면이 재생성되는지 확인.
4. Tray Pause/Resume/Reset/Exit 확인. Windows 전체 화면 독점 앱 및 보안 데스크톱 위 표시를 보장하지 않습니다.

### 이 프로젝트를 만든 클라우드 환경에서 확인한 결과

- Python 3.12 / PySide6 6.8.3, Linux Qt offscreen에서 13개 테스트 통과.
- 실제 Qt 타이머·윈도우로 성공 강제/실패 강제 controller를 동시에 실행해 각각 **전체 루프 2회** 완료, 매 슛 왕복 카운트 `[3,3]` 확인.
- `artifacts/runtime-validation.json`에 결과, `artifacts/runtime-contact-sheet.png`에 렌더링 샘플 저장. 샘플의 어두운 배경은 검증용 합성 배경이며 프로그램 창 배경이 아닙니다.
- PyInstaller Linux 폴더형/onefile 빌드 및 패키지 시작 검증. **Windows native 실행/실제 클릭 통과와 Windows exe 빌드는 이 Linux 머신에서 검증하지 않았습니다.** Windows CI와 진단 도구로 재현할 수 있습니다.

Linux의 `QT_QPA_PLATFORM=offscreen` 경고(raise/tray 미지원)는 실제 Windows 기능을 검증했다는 의미가 아닙니다. 그래픽 데스크톱이 없는 Linux에서 통합 렌더링을 재현하려면:

```bash
QT_QPA_PLATFORM=offscreen python tools/validate_runtime.py
```

## 파일 구조

```text
desktop-pet/
  main.py                  # 진입점
  config.json
  requirements.txt
  build_windows.bat
  assets/                  # original placeholder + 교체용 metadata
  src/
    app.py                 # screen 연결/분리와 tray 명령
    monitor_controller.py  # 화면당 작은 창 3개와 frame timer
    overlay.py             # 투명·입력 통과 창
    windows_taskbar.py      # SHAppBarMessage / Win32 styles
    screen_geometry.py     # 논리 좌표 floor
    state_machine.py       # 상태별 handler
    movement.py
    shot.py                # 포물선
    pet.py                 # procedural player 생성
    ball.py
    hoop.py                # screen layout
    animation.py           # 프레임 / foot pivot / 방향 반전
    assets.py              # PNG 캐시와 fallback
    config.py
    tray.py
    startup.py             # HKCU startup 토글
  tests/                   # model + Qt 통합 테스트
  tools/                   # build, native check, placeholder 생성, runtime 검증
  artifacts/               # 실행 결과와 렌더링 증거
  .github/workflows/       # Windows CI
```
