#!/usr/bin/env python3
"""
Build one zip per skill in dist/, for uploading to claude.ai (Settings → Capabilities → Skills)
or provisioning to an organisation. Each zip holds the skill's folder (SKILL.md at its top).

Usage: python3 scripts/build_skill_zips.py
"""
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SKIP = {"__pycache__", ".DS_Store"}


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for skill_md in sorted(ROOT.glob("plugins/*/skills/*/SKILL.md")):
        skill = skill_md.parent
        target = DIST / f"{skill.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(skill.rglob("*")):
                if f.is_file() and not SKIP & set(f.parts):
                    z.write(f, f"{skill.name}/{f.relative_to(skill).as_posix()}")
        print(f"{target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
