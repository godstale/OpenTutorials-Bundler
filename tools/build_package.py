#!/usr/bin/env python3
"""패키지 ZIP 빌더: python tools/build_package.py <package-slug>"""

import sys
import json
import zipfile
import os
from collections import Counter


def build_package(package_slug: str) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package_dir = os.path.join(base_dir, "packages", package_slug)
    manifest_path = os.path.join(package_dir, "package-manifest.json")
    converted_dir = os.path.join(base_dir, "converted")

    if not os.path.exists(manifest_path):
        print(f"ERROR: package-manifest.json not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    courses = manifest.get("courses", [])
    thumbnail = manifest.get("thumbnail")

    # courses 빈 목록 검사
    if not courses:
        print("ERROR: courses 목록이 비어 있습니다. package-manifest.json을 확인하세요.")
        sys.exit(1)

    # [P1] courses 슬러그 존재 확인
    missing = [s for s in courses if not os.path.isdir(os.path.join(converted_dir, s))]
    if missing:
        print("ERROR [P1]: 다음 강좌 슬러그가 converted/ 폴더에 없습니다:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # [P2] courses 슬러그 중복 금지
    dupes = [s for s, c in Counter(courses).items() if c > 1]
    if dupes:
        print(f"ERROR [P2]: 중복된 슬러그가 있습니다: {dupes}")
        sys.exit(1)

    # [P3] thumbnail 파일 존재 확인
    if thumbnail:
        thumb_path = os.path.join(package_dir, thumbnail)
        if not os.path.exists(thumb_path):
            print(f"ERROR [P3]: thumbnail 파일이 없습니다: {thumb_path}")
            sys.exit(1)

    # ZIP 생성
    zip_path = os.path.join(converted_dir, f"{package_slug}-pkg.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "package-manifest.json")
        if thumbnail:
            zf.write(os.path.join(package_dir, thumbnail), thumbnail)

    print(f"패키지 ZIP 생성 완료: {zip_path}")
    print(f"포함 강좌 수: {len(courses)}개")
    for i, slug in enumerate(courses, 1):
        print(f"  {i:2d}. {slug}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/build_package.py <package-slug>")
        sys.exit(1)
    build_package(sys.argv[1])
