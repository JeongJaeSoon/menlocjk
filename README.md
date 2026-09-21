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

`weights.py`는 400과 700 사이를 채웁니다. Orca는 터미널에
`-webkit-font-smoothing: antialiased`를 걸어 같은 페이스도 VSCode보다 얇게 나오는데,
Orca의 Font Weight만 올려 보정하고 다른 앱은 400 그대로 두기 위한 것입니다.

| 웨이트 | 스템 두께 | 용도 |
|---|---|---|
| 400 Regular | 172 | VSCode · iTerm2 |
| 500 Medium | 190 | Orca 보정용 |
| 600 SemiBold | 209 | Orca 보정용 (더 굵게) |
| 700 Bold | 227 | 볼드 |

스트로크 폭은 Menlo 자체의 Regular→Bold 증가폭(172 → 227)을 100 단위로 선형 보간한
값입니다. Italic도 같은 4단계로 만듭니다.

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
```

`prep.py` 상단의 경로 상수와 `weights.py`의 `TARGETS`로 소스 위치·굵기를 조정합니다.

## 앱 설정

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
- **Thin Strokes: Never** — 기본값(Always)이면 CoreText가 획을 얇게 그려 Chromium 쪽보다 가늘어 보입니다

**Orca** — Settings → Terminal

- Font Family: `MenloCJK`
- Font Size: 14
- Font Weight: 400에서 시작해 얇아 보이면 500 또는 600

### 설정 파일을 직접 고칠 때 주의

두 앱 모두 **실행 중에는 설정 파일을 고쳐도 소용없습니다.** 메모리 상태로 덮어씁니다.

- iTerm2: custom prefs folder를 쓰면 종료할 때 덮어씁니다. 종료하지 말고 Python API로
  라이브 수정하는 쪽이 확실합니다 — `iterm2.PartialProfile.async_query` →
  `async_get_full_profile()` → `profile._async_simple_set(key, value)`.
  공개 API에 없는 키는 `_simple_get` / `_async_simple_set`으로 직접 다룹니다.
- Orca: 프로필 데이터 파일을 실행 중에 고치면 몇 초 만에 덮어씁니다. UI에서 설정하거나
  앱을 종료한 뒤 고칩니다.

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
