#!/usr/bin/env python3
"""통합 번들(패키지) 빌더: python tools/build_package.py <package-slug>

package-manifest.json + thumbnail.png(선택) + courses/<slug>.zip 구조의
단일 통합 ZIP(converted/<package-slug>.zip)을 생성한다.
"""

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

    # [P0] 각 항목이 CourseMeta 객체인지 확인
    required_fields = {"slug", "title", "description", "tags"}
    for i, course in enumerate(courses):
        if not isinstance(course, dict):
            print(f"ERROR [P0]: courses[{i}]가 객체(dict)가 아닙니다. 문자열 슬러그 형식은 더 이상 지원하지 않습니다.")
            sys.exit(1)
        missing_fields = required_fields - set(course.keys())
        if missing_fields:
            print(f"ERROR [P0]: courses[{i}] (slug={course.get('slug', '?')})에 필수 필드가 없습니다: {missing_fields}")
            sys.exit(1)
        if not isinstance(course.get("tags"), list) or len(course["tags"]) < 3:
            print(f"ERROR [P0]: courses[{i}] (slug={course.get('slug', '?')})의 tags는 3개 이상이어야 합니다.")
            sys.exit(1)

    slugs = [c["slug"] for c in courses]

    # [P2] courses 슬러그 중복 금지 (실재 확인보다 먼저 검사해 중복 슬러그를 한 번만 보고)
    dupes = [s for s, c in Counter(slugs).items() if c > 1]
    if dupes:
        print(f"ERROR [P2]: 중복된 슬러그가 있습니다: {dupes}")
        sys.exit(1)

    # [P1] 하위 강좌 ZIP 실재 확인 — 폴더가 아닌 <slug>/<slug>.zip 파일 자체가 있어야 함
    course_zip_paths = {}
    missing = []
    for slug in slugs:
        zip_path = os.path.join(converted_dir, slug, f"{slug}.zip")
        if not os.path.isfile(zip_path):
            pkg_sub_zip_path = os.path.join(converted_dir, package_slug, slug, f"{slug}.zip")
            if os.path.isfile(pkg_sub_zip_path):
                zip_path = pkg_sub_zip_path
            else:
                missing.append(f"converted/{slug}/{slug}.zip or converted/{package_slug}/{slug}/{slug}.zip")
                continue
        course_zip_paths[slug] = zip_path
    if missing:
        print("ERROR [P1]: 다음 강좌 ZIP 파일이 없습니다 (먼저 개별 강좌 ZIP을 생성하세요):")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # thumbnail이 아이콘 참조("icon:*")인지 이미지 파일인지 구분
    is_icon = thumbnail and thumbnail.startswith("icon:")
    thumb_path = None

    # [P3] thumbnail 파일 존재 확인 (이미지 파일인 경우에만)
    if thumbnail and not is_icon:
        thumb_path = os.path.join(package_dir, thumbnail)
        if not os.path.exists(thumb_path):
            print(f"ERROR [P3]: thumbnail 파일이 없습니다: {thumb_path}")
            sys.exit(1)
        if os.path.splitext(thumb_path)[1].lower() != ".png":
            print(f"WARNING [P6]: thumbnail 원본 파일이 .png가 아닙니다 ({thumbnail}). 파일명만 thumbnail.png로 정규화되며 내용은 변환되지 않습니다.")

    # [P5] 통합 번들 출력 경로 충돌 확인 — 출력 파일명은 <package-slug>.zip (구 -pkg.zip 접미사 폐지)
    out_path = os.path.join(converted_dir, f"{package_slug}.zip")
    if os.path.isdir(out_path):
        print(f"ERROR [P5]: 출력 경로가 이미 폴더로 존재합니다: {out_path}")
        sys.exit(1)
    if os.path.exists(out_path):
        os.remove(out_path)

    # 통합 번들 ZIP 생성: package-manifest.json + thumbnail.png(선택) + courses/<slug>.zip
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "package-manifest.json")
        if thumb_path:
            # [P6] 원본 파일명과 무관하게 ZIP 내부명은 항상 thumbnail.png로 고정
            zf.write(thumb_path, "thumbnail.png")
        for slug in slugs:
            zf.write(course_zip_paths[slug], f"courses/{slug}.zip")

    print(f"통합 번들 ZIP 생성 완료: {out_path}")
    print(f"포함 강좌 수: {len(courses)}개")
    for i, course in enumerate(courses, 1):
        print(f"  {i:2d}. {course['slug']} - {course['title']}")
    if thumbnail:
        if is_icon:
            print(f"썸네일: {thumbnail} (플랫폼 아이콘, 파일 미포함)")
        else:
            print(f"썸네일: {thumbnail} → thumbnail.png (이미지 파일 포함)")
    else:
        print("썸네일: 없음 (기본 icon:book 적용)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/build_package.py <package-slug>")
        sys.exit(1)
    build_package(sys.argv[1])
