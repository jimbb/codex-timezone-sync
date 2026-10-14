#!/usr/bin/env python3
"""Guard the panel translations: every referenced key must exist, in all languages.

Fails if markup references a key no dictionary defines, if an entry is blank, or if
the three dictionaries drift apart. Runs on the raw HTML, no browser needed.
"""
import pathlib
import re
import sys

LANGS = ("zh-Hans", "zh-Hant", "en")
HTML = pathlib.Path(__file__).resolve().parent / "dashboard.html"


def dictionaries(html):
    """Slice the I18N object literal into one text block per language."""
    start = html.index("const I18N={")
    end = html.index("}};", start)
    body = html[start + len("const I18N={"):end]
    blocks = {}
    for i, lang in enumerate(LANGS):
        marker = ("'" + lang + "'" if lang != "en" else "en") + ":{"
        begin = body.index(marker) + len(marker)
        if i + 1 < len(LANGS):
            nxt = LANGS[i + 1]
            endmark = ("'" + nxt + "'" if nxt != "en" else "en") + ":{"
            stop = body.index(endmark, begin)
        else:
            stop = len(body)
        blocks[lang] = {m[0]: m[1] for m in re.findall(r"'([^']+)':\s*'([^']*)'", body[begin:stop])}
    return blocks


def main():
    html = HTML.read_text(encoding="utf-8")
    used = set(re.findall(r'data-i18n(?:-title|-aria|-placeholder)?="([^"]+)"', html))
    # Keys reached only from JS rather than markup.
    used |= set(re.findall(r"t\('((?:fb|st|reason|kind|state|flag|lastRefresh|protocol|activity|failures|metrics|core|status|auth|ops|settings|app|doc)\.[A-Za-z0-9_.]+)'", html))
    dicts = dictionaries(html)
    failures = []

    for lang in LANGS:
        defined = dicts[lang]
        missing = {k for k in used if k not in defined}
        blank = {k for k, v in defined.items() if not v.strip()}
        if missing:
            failures.append(f"{lang}: missing {sorted(missing)}")
        if blank:
            failures.append(f"{lang}: blank {sorted(blank)}")

    base = set(dicts[LANGS[0]])
    for lang in LANGS[1:]:
        diff = base ^ set(dicts[lang])
        if diff:
            failures.append(f"{lang}: key set differs from {LANGS[0]} -> {sorted(diff)}")

    if failures:
        print("FAIL")
        for line in failures:
            print("  " + line)
        return 1
    print(f"OK: {len(used)} keys used, {len(base)} defined per language, {len(LANGS)} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
