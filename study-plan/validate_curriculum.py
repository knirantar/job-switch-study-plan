"""Repository-wide structural validator for the study-plan completion contract."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
SECTION = re.compile(r"^## (10|[1-9])\.", re.MULTILINE)
PROBLEM = re.compile(r"^### (?:(?:Worked )?Problem|[0-9]+\. Problem)", re.MULTILINE)
NUMBERED = re.compile(r"^[0-9]+\.", re.MULTILINE)
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


def between(text: str, start: str, end: str) -> str:
    left = text.find(start)
    right = text.find(end, left + len(start))
    return "" if left < 0 or right < 0 else text[left + len(start):right]


def validate_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for raw_target in LINK.findall(text):
        target = raw_target.strip()
        if target.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if target and not (path.parent / target).exists():
            errors.append(f"broken local link: {raw_target}")
    return errors


def validate_lesson(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    sections = [int(value) for value in SECTION.findall(text)]
    if sections != list(range(1, 11)):
        errors.append(f"sections are {sections}, expected 1..10 exactly")
    if len(PROBLEM.findall(text)) < 8:
        errors.append("fewer than eight worked problems")
    practice = len(NUMBERED.findall(between(text, "## 8.", "## 9.")))
    if not 6 <= practice <= 10:
        errors.append(f"practice count {practice}, expected 6..10")
    resources = len(NUMBERED.findall(between(text, "## 9.", "## 10.")))
    if resources < 1:
        errors.append("no numbered curated resources")
    bridges = len(NUMBERED.findall(between(text, "## 10.", "---ANSWER KEY BELOW---")))
    if bridges < 3:
        errors.append(f"only {bridges} numbered bridge topics")
    if text.count("---ANSWER KEY BELOW---") != 1:
        errors.append("answer-key marker must occur exactly once")
    headings = re.findall(r"^(?:## .+|---ANSWER KEY BELOW---)$", text, re.MULTILINE)
    if not headings or headings[-1] != "---ANSWER KEY BELOW---":
        errors.append("answer key is not the final top-level section")
    if len(text.split()) < 2500:
        errors.append("fewer than 2,500 whitespace-delimited words")
    errors.extend(validate_links(path, text))
    return errors


def main() -> int:
    parents = sorted(path for path in ROOT.iterdir() if path.is_dir() and re.match(r"^[0-9]{2}-", path.name))
    lessons: list[Path] = []
    errors: list[str] = []
    if len(parents) != 8:
        errors.append(f"expected 8 parent directories, found {len(parents)}")
    for parent in parents:
        children = sorted(path for path in parent.iterdir() if path.is_dir() and re.match(r"^[0-9]{2}-", path.name))
        for required in (parent / "README.md", parent / "CAPSTONE.md"):
            if not required.is_file():
                errors.append(f"missing {required.relative_to(ROOT)}")
        for child in children:
            lesson = child / "lesson.md"
            if lesson.is_file():
                lessons.append(lesson)
            else:
                errors.append(f"missing {lesson.relative_to(ROOT)}")
    if len(lessons) != 47:
        errors.append(f"expected 47 lessons, found {len(lessons)}")
    for lesson in lessons:
        for error in validate_lesson(lesson):
            errors.append(f"{lesson.relative_to(ROOT)}: {error}")
    for markdown in ROOT.rglob("*.md"):
        if markdown not in lessons:
            text = markdown.read_text(encoding="utf-8")
            for error in validate_links(markdown, text):
                errors.append(f"{markdown.relative_to(ROOT)}: {error}")
    if errors:
        print("CURRICULUM INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    words = sum(len(path.read_text(encoding="utf-8").split()) for path in lessons)
    print(f"CURRICULUM VALID: {len(parents)} parents, {len(lessons)} lessons, {words:,} lesson words, 8 capstones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
