#!/usr/bin/env python3
"""통합 번들(패키지) 빌더: python tools/build_package.py <package-slug>

package-manifest.json + thumbnail.png(선택) + courses/<slug>.zip 구조의
단일 통합 ZIP(converted/<package-slug>.zip)을 생성한다.
"""

import sys
import json
import zipfile
import os
import re
from collections import Counter

def increment_patch_version(version_str: str) -> str:
    prefix = ""
    if version_str.startswith('v'):
        prefix = "v"
        version_str = version_str[1:]
    
    parts = version_str.split('.')
    if len(parts) >= 3:
        try:
            patch = int(parts[2])
            parts[2] = str(patch + 1)
            return prefix + ".".join(parts[:3])
        except ValueError:
            pass
    elif len(parts) == 2:
        return prefix + f"{parts[0]}.{parts[1]}.1"
    elif len(parts) == 1:
        return prefix + f"{parts[0]}.0.1"
    return "1.0.0"


def build_package(package_slug: str, version_set: str = None, no_bump: bool = False) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package_dir = os.path.join(base_dir, "converted", package_slug)
    manifest_path = os.path.join(package_dir, "package-manifest.json")
    converted_dir = os.path.join(base_dir, "converted")

    if not os.path.exists(manifest_path):
        print(f"ERROR: package-manifest.json not found at {manifest_path}")
        sys.exit(1)

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: package-manifest.json 파싱 실패 (올바른 JSON 형식이 아닙니다): {e}")
        sys.exit(1)

    courses = manifest.get("courses", [])
    thumbnail = manifest.get("thumbnail")

    # [P0] 패키지 매니페스트 필수 필드 검사
    required_manifest_fields = [
        "title", "slug", "description", "author", "published",
        "version", "changelog", "bundler_protocol_version",
        "target_age", "category", "tags", "courses"
    ]
    
    package_errors = []
    for field in required_manifest_fields:
        if field not in manifest:
            package_errors.append(f"package-manifest.json 오류: 필수 필드 '{field}'가 누락되었습니다.")
            
    # author 세부 검증
    author_data = manifest.get("author")
    if author_data:
        if not isinstance(author_data, dict):
            package_errors.append("package-manifest.json 오류: 'author' 필드는 객체 형식이어야 합니다.")
        elif "nickname" not in author_data or not str(author_data.get("nickname")).strip():
            package_errors.append("package-manifest.json 오류: 'author.nickname' 필드가 없거나 비어 있습니다.")

    # tags 세부 검증
    tags_data = manifest.get("tags")
    if tags_data is not None:
        if not isinstance(tags_data, list):
            package_errors.append("package-manifest.json 오류: 'tags' 필드는 배열 형식이어야 합니다.")
        elif len(tags_data) < 3:
            package_errors.append("package-manifest.json 오류: 'tags' 배열은 최소 3개 이상의 태그를 포함해야 합니다.")

    # 프로토콜 버전 검증
    proto_ver = manifest.get("bundler_protocol_version")
    if proto_ver and proto_ver != "1.1.5":
        package_errors.append(f"package-manifest.json 오류: 프로토콜 버전이 '1.1.5'이어야 합니다 (현재: '{proto_ver}')")

    # [P0] target_age 형식 검증: all / x+ / min-max
    target_age_val = manifest.get("target_age")
    if target_age_val is not None and not re.match(r'^(all|\d+\+|\d+-\d+)$', str(target_age_val)):
        package_errors.append(f"package-manifest.json 오류: target_age 형식이 잘못되었습니다: '{target_age_val}' ('all', 'x+', 'min-max' 형식만 허용, 예: 'all', '10+', '8-13')")

    # [P0] language 형식 검증 (선택 필드)
    language_val = manifest.get("language")
    if language_val is not None and language_val not in ("ko", "en"):
        package_errors.append(f"package-manifest.json 오류: language 값이 잘못되었습니다: '{language_val}' ('ko' 또는 'en'만 허용)")

    # license / license_file 검증 (선택 필드)
    license_val = manifest.get("license")
    allowed_licenses = (
        "CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0", "CC-BY-NC-SA-4.0",
        "CC-BY-ND-4.0", "CC-BY-NC-ND-4.0", "CC0-1.0", "all-rights-reserved", "custom"
    )
    license_file_val = manifest.get("license_file")
    if license_val is not None and license_val not in allowed_licenses:
        package_errors.append(f"package-manifest.json 오류: license 값이 잘못되었습니다: '{license_val}' (허용값: {', '.join(allowed_licenses)})")
    elif license_val == "custom" and (not license_file_val or not str(license_file_val).strip()):
        package_errors.append("package-manifest.json 오류: license가 'custom'인 경우 license_file 필드가 반드시 필요합니다.")
    # license_file은 custom이 아니어도(제3자 리소스 고지 목적) 선택적으로 사용 가능하므로, 지정된 경우 항상 실재 여부를 검증한다
    if license_file_val:
        license_file_path = os.path.join(package_dir, license_file_val)
        if not os.path.exists(license_file_path):
            package_errors.append(f"package-manifest.json 오류: license_file에 지정된 파일이 존재하지 않습니다: {license_file_path}")

    if package_errors:
        print("\n[ERROR] 패키지 매니페스트 검증 실패! 다음 오류들을 수정해주세요:")
        for err in package_errors:
            print(f"  - {err}")
        sys.exit(1)

    # 버전 업데이트 로직 추가
    updated = False
    if version_set:
        manifest["version"] = version_set
        manifest["changelog"] = f"버전 {version_set} 업데이트"
        updated = True
        print(f"[INFO] 패키지 버전을 사용자가 지정한 값으로 설정합니다: {version_set}")
    elif not no_bump:
        old_version = manifest.get("version", "1.0.0")
        new_version = increment_patch_version(old_version)
        manifest["version"] = new_version
        manifest["changelog"] = f"버전 {new_version} 업데이트"
        updated = True
        print(f"[INFO] 패키지 버전 자동 업데이트: {old_version} -> {new_version}")

    if updated:
        try:
            with open(manifest_path, "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERROR: package-manifest.json 버전 업데이트 저장 실패: {e}")
            sys.exit(1)

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
        pkg_sub_zip_path = os.path.join(converted_dir, package_slug, slug, f"{slug}.zip")
        if os.path.isfile(pkg_sub_zip_path):
            zip_path = pkg_sub_zip_path
        else:
            zip_path = os.path.join(converted_dir, slug, f"{slug}.zip")
            
        if not os.path.isfile(zip_path):
            missing.append(f"converted/{package_slug}/{slug}/{slug}.zip or converted/{slug}/{slug}.zip")
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

    # [P5] 통합 번들 출력 경로 충돌 확인 — 출력 파일명은 <package-slug>/<package-slug>.zip
    package_out_dir = os.path.join(converted_dir, package_slug)
    os.makedirs(package_out_dir, exist_ok=True)
    out_path = os.path.join(package_out_dir, f"{package_slug}.zip")
    if os.path.isdir(out_path):
        print(f"ERROR [P5]: 출력 경로가 이미 폴더로 존재합니다: {out_path}")
        sys.exit(1)
    if os.path.exists(out_path):
        os.remove(out_path)

    license_file_path = None
    if license_file_val:
        license_file_path = os.path.join(package_dir, license_file_val)

    # 통합 번들 ZIP 생성: package-manifest.json + thumbnail.png(선택) + LICENSE(선택) + courses/<slug>.zip
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "package-manifest.json")
        if thumb_path:
            # [P6] 원본 파일명과 무관하게 ZIP 내부명은 항상 thumbnail.png로 고정
            zf.write(thumb_path, "thumbnail.png")
        if license_file_path and os.path.exists(license_file_path):
            zf.write(license_file_path, license_file_val)
        for slug in slugs:
            zf.write(course_zip_paths[slug], f"courses/{slug}.zip")

    print(f"통합 번들 ZIP 생성 완료: {out_path}")
    
    # 통합 번들 ZIP 사후 검증 [P7]
    print(f"[*] 통합 번들 ZIP 사후 검증 시작: {out_path}")
    try:
        import io
        with zipfile.ZipFile(out_path, 'r') as zf:
            namelist = zf.namelist()
            zip_errors = []
            
            # package-manifest.json 검사
            if "package-manifest.json" not in namelist:
                zip_errors.append("통합 ZIP 루트에 'package-manifest.json' 파일이 누락되었습니다.")

            # license_file(라이선스/제3자 리소스 고지 파일) ZIP 포함 여부 검사
            if license_file_path and license_file_val not in namelist:
                zip_errors.append(f"통합 ZIP 루트에 커스텀 라이선스 파일 '{license_file_val}'이 누락되었습니다.")


            # courses/ 하위 강좌 ZIP들 존재 검사 및 내부에 config.json 존재 여부 사후 검사
            for slug in slugs:
                expected_zip = f"courses/{slug}.zip"
                if expected_zip not in namelist:
                    zip_errors.append(f"통합 ZIP 내부에 하위 강좌 '{expected_zip}' 파일이 누락되었습니다.")
                else:
                    # 하위 강좌 ZIP 내용물 읽어서 config.json/wiki.md/package-manifest.json 존재하는지 추가 검사
                    try:
                        sub_data = zf.read(expected_zip)
                        with zipfile.ZipFile(io.BytesIO(sub_data), 'r') as szf:
                            s_namelist = szf.namelist()
                            for req_file in ["config.json", "wiki.md", "package-manifest.json"]:
                                if req_file not in s_namelist:
                                    zip_errors.append(f"하위 강좌 ZIP '{expected_zip}' 내부에 필수 파일 '{req_file}'이 누락되었습니다.")
                    except Exception as sub_err:
                        zip_errors.append(f"하위 강좌 ZIP '{expected_zip}' 읽기/검증 실패: {sub_err}")
                        
            if zip_errors:
                print("\n[ERROR] 통합 번들 ZIP 사후 검증 실패! 다음 파일 오류를 해결하세요:")
                for err in zip_errors:
                    print(f"  - {err}")
                os.remove(out_path)
                sys.exit(1)
            else:
                print(f"[OK] 통합 번들 ZIP 사후 검증 완료 (모든 하위 강좌 ZIP 내부의 config.json, wiki.md, package-manifest.json 존재 확인 완료)")
    except Exception as e:
        print(f"ERROR: 통합 번들 ZIP 사후 검증 중 예외 발생: {e}")
        sys.exit(1)

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


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="통합 번들(패키지) 빌더")
    parser.add_argument("package_slug", help="빌드할 패키지의 슬러그")
    parser.add_argument("--version-set", "-v", help="패키지의 버전을 명시적으로 지정합니다 (예: 1.0.5).")
    parser.add_argument("--no-bump", action="store_true", help="버전을 올리지 않고 기존 버전을 그대로 유지합니다.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_package(args.package_slug, args.version_set, args.no_bump)
