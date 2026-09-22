# MenloCJK

macOS에서 **VSCode · iTerm2 · Orca**가 한국어·일본어·영어를 **완전히 동일하게** 출력하도록
Menlo + UDEV Gothic NF + D2Coding을 하나의 폰트로 병합하는 빌드 스크립트.

> ⚠️ **폰트 파일은 이 저장소에 없습니다.** Menlo는 Apple 소유라 재배포할 수 없습니다.
> 각자 자기 Mac에서 직접 빌드해야 합니다. [라이선스](#라이선스) 참고.

## 왜 필요한가

세 앱이 폰트 폴백을 다루는 방식이 전부 다릅니다.

| 앱 | 폴백 방식 |
|---|---|
| VSCode | CSS 폰트 목록 — 원하는 만큼 나열 가능 |
| iTerm2 | ASCII 폰트 + 비ASCII 폰트 **2슬롯**, 추가로 코드포인트 범위 예외 |
| Orca | 패밀리 **1개**. 입력값을 통째로 따옴표로 감싸 CSS에 넣음 |

`Menlo, UDEV Gothic NF, D2Coding` 같은 체인을 세 앱에 똑같이 넣는 건 불가능합니다.
그래서 **폴백을 폰트 안으로 밀어 넣어** 패밀리 하나로 끝냅니다.

## 글자별 출처

cmap 충돌은 앞 폰트가 이깁니다.

| 문자 | 출처 | advance (upm 2048) |
|---|---|---|
| 라틴·숫자·기호, 박스드로잉, 블록 | Menlo | 1233 (0.602em) |
| 가나·한자, Nerd Font 아이콘, Powerline | UDEV Gothic NF | 2048 / 1024 |
| 한글 음절·자모 | D2Coding (upm 1000 → 2048 스케일) | 2048 |

세로 메트릭(hhea/OS2)은 Menlo 값으로 덮어써 줄 간격을 유지하고, advance는 손대지
않아 기존 폴백 체인과 렌더링 결과가 같습니다.

## 굵기

Menlo는 두 웨이트만 그려져 있고 그 간격도 좁습니다 — 스템 172와 227. 화면에서
그 1/3은 구분이 안 되므로, 14px에서 차이가 실제로 보이는 최소 단위인 **27을 한 칸**으로
잡았습니다. 그러면 Menlo의 Bold(227)가 **600 자리에 정확히 떨어집니다**
(172 + 2×27 = 226). 그 위는 Bold에서 파생시켜 전 구간 간격을 똑같이 맞춥니다.

Orca가 터미널에 `-webkit-font-smoothing: antialiased`를 걸어 같은 페이스도 VSCode보다
얇게 나오는데, 이 램프가 있으면 Orca의 Font Weight만 올려 보정하고 다른 앱은 400을
그대로 쓸 수 있습니다.

| 웨이트 | 스템 | 출처 |
|---|---|---|
| 400 Regular | 172 | Menlo Regular (원본) |
| 500 Medium | 199 | Regular +27 |
| 600 SemiBold | 227 | **Menlo Bold (원본)** |
| 700 Bold | 254 | Bold +27 |
| 800 ExtraBold | 281 | Bold +54 |
| 900 Black | 308 | Bold +81 |

Italic도 같은 6단계. advance는 건드리지 않으므로 터미널 그리드는 그대로입니다.
54,587자 중 유니온이 실패하는 1~2자는 원본 아웃라인을 유지합니다.

> **주의:** 700은 더 이상 Menlo가 그린 Bold가 아니라 그보다 굵은 합성입니다. 터미널
> ANSI 볼드는 기본적으로 700을 쓰므로 볼드가 굵어집니다. 원본 Bold를 볼드로 쓰려면
> 앱의 볼드 웨이트 설정을 600으로 내리세요 — Orca는 `Bold Font Weight`,
> VSCode는 `terminal.integrated.fontWeightBold`.

## 빌드

준비물:

- macOS (Menlo 필요)
- [`uv`](https://docs.astral.sh/uv/)
- [UDEV Gothic NF](https://github.com/yuru7/udev-gothic) — Regular / Bold / Italic / BoldItalic
- [D2Coding](https://github.com/naver/d2codingfont)

앞의 두 폰트를 사용자 폰트 디렉터리에 설치한 뒤:

```sh
./build.sh
cp out/MenloCJK-*.ttf ~/Library/Fonts/
python3 apply.py            # 세 앱 설정까지 한 번에, --check 로 미리보기
```

`prep.py` 상단의 경로 상수와 `weights.py`의 `TARGETS`로 소스 위치·굵기를 조정합니다.

### apply.py

세 앱 설정을 코드로 들고 있습니다. **값을 바꾸려면 앱이 아니라 이 파일을 고치세요.**
인자로 앱을 골라 적용합니다 (없으면 전부):

```sh
python3 apply.py                 # 전부
python3 apply.py vscode          # 하나만
python3 apply.py iterm2 orca     # 일부
python3 apply.py --check         # 변경 없이 현재 상태만
```

- VSCode — `settings.json`이 JSONC라 다시 직렬화하지 않고 해당 키만 제자리에서 고칩니다. 없으면 끝에 추가하고, 고치기 전에 타임스탬프 백업을 남깁니다.
- iTerm2 — 실행 중인 앱을 Python API로 조종합니다. 꺼져 있으면 건너뛰고 안내만 합니다(디스크의 prefs를 고쳐봤자 종료할 때 덮어쓰므로).
- Orca — 꺼져 있을 때만 `orca-data.json`을 고칩니다. 켜져 있으면 몇 초 만에 되돌아가므로 거부하고 안내합니다.

```
$ python3 apply.py --check
[  ok] fonts: 12 faces installed
[  ok] vscode: already set
[  ok] iterm2: Default: already set
[  ok] iterm2: tmux: already set
[warn] orca: running - quit it and rerun, or set it by hand in Settings > Terminal
```

## 앱 설정

세 앱을 나란히 놓고 맞춘 조합입니다. 굵기까지 같아 보이는 지점이 **Orca만 한 칸 위**라는
점이 핵심입니다.

| | 폰트 | 크기 | 웨이트 | 스템 |
|---|---|---:|---:|---:|
| VSCode | `MenloCJK` | 14 | 기본 (400) | 172 |
| iTerm2 | `MenloCJK-Regular` | 14 | 400 | 172 |
| Orca | `MenloCJK` | 14 | **500** | **199** |

Orca만 500인 이유는 아래 [앱별 함정](#앱별-함정)의 font-smoothing 항목입니다.

**VSCode**

```jsonc
"editor.fontFamily": "MenloCJK",
"terminal.integrated.fontFamily": "MenloCJK",
"editor.fontSize": 14,
"terminal.integrated.fontSize": 14,
```

**iTerm2** — Profiles → Text

- Font: `MenloCJK-Regular` 14
- Use a different font for non-ASCII text: **끄기**
- 코드포인트 범위 예외(Special Font Config): **비우기**
- **Thin Strokes: Never**

**Orca** — Settings → Terminal

- Font Family: `MenloCJK`
- Font Size: 14
- Font Weight: **500**

## 앱별 함정

**iTerm2의 Thin Strokes** — 기본값이 Always(`3`)라 CoreText가 획을 얇게 그립니다.
Chromium에는 대응하는 동작이 없어 iTerm2만 가늘어 보입니다. Never(`0`)로 끄세요.

**Orca의 font-smoothing** — Orca는 번들 CSS의 `body`에
`-webkit-font-smoothing: antialiased`를 겁니다(VSCode에는 없음). macOS Chromium에서
이건 subpixel AA를 grayscale AA로 바꾸는 스위치라 **같은 페이스가 더 얇게** 그려집니다.
플러그인 매니페스트가 CSS 주입을 지원하지 않아 정공법으로는 못 고칩니다. 대신 웨이트를
정확히 한 칸(+27) 올려 상쇄합니다 — Orca 500(199) ≒ VSCode 400(172).

**새 웨이트 설치 후 Orca 재시작** — Chromium이 시작 시점의 패밀리 구성을 캐싱합니다.
재시작 전에는 500이 400으로, 600 이상이 700으로 떨어져서 "400과 500이 똑같고 600에서
갑자기 굵어지는" 증상이 납니다.

### 설정 파일을 직접 고칠 때 주의

두 앱 모두 **실행 중에는 설정 파일을 고쳐도 소용없습니다.** 메모리 상태로 덮어씁니다.

- iTerm2: custom prefs folder를 쓰면 종료할 때 덮어씁니다. 종료하지 말고 Python API로
  라이브 수정하는 쪽이 확실합니다 — `iterm2.PartialProfile.async_query` →
  `async_get_full_profile()` → `profile._async_simple_set(key, value)`.
  공개 API에 없는 키는 `_simple_get` / `_async_simple_set`으로 직접 다룹니다.
- Orca: 프로필 데이터 파일을 실행 중에 고치면 몇 초 만에 덮어씁니다. UI에서 설정하거나
  앱을 종료한 뒤 고칩니다.

## Claude Code 스킬

저장소 안에 `.claude/skills/`로 들어 있어 클론만 하면 바로 붙습니다.

- **`menlocjk-build`** — 소스 폰트 확인부터 빌드·설치·검증(스템 그리드, advance, bold 비트)까지
- **`menlocjk-apply`** — 앱 설정 적용(인자로 앱 선택)과 "한 앱만 다르게 보인다" 진단 체크리스트

## 라이선스

빌드 스크립트는 [MIT](LICENSE).

**빌드 결과물(.ttf)은 재배포할 수 없습니다.**

| 소스 | 라이선스 | 재배포 |
|---|---|---|
| Menlo | Apple 독점 (macOS 번들) | ❌ |
| UDEV Gothic NF | SIL OFL 1.1 | ⭕ (OFL 조건 하에) |
| D2Coding | SIL OFL 1.1 | ⭕ (OFL 조건 하에) |

Menlo가 섞여 있는 한 결과물은 개인 로컬 사용에 한정됩니다. 배포 가능한 폰트를 원한다면
`prep.py`의 Menlo 자리를 MesloLGS NF(Apache-2.0, Menlo 클론, advance 1233으로 동일)
같은 것으로 바꾸고, 이름에서 `Menlo`를 빼고, OFL 원문과 원저작권 표기를 함께 배포하세요.
