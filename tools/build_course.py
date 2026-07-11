#!/usr/bin/env python3
"""개별 강좌 번들 빌더 및 검증 도구: python tools/build_course.py <course-slug> [--package <package-slug>]

개별 강좌 디렉토리를 검증(C1~C11, Z2)하고 검증 성공 시 <course-slug>.zip을 생성합니다.
만약 package-manifest.json이 누락된 경우, config.json이나 패키지 매니페스트 정보를 기반으로 자동 복구/생성합니다.
"""

import sys
import json
import zipfile
import os
import re
from typing import List, Dict, Any, Set

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="개별 강좌 번들 검증 및 ZIP 빌드 도구")
    parser.add_argument("course_slug", help="빌드할 강좌의 슬러그")
    parser.add_argument("--package", "-p", help="강좌가 속한 패키지의 슬러그 (패키지 하위 강좌 빌드 시)")
    parser.add_argument("--force-manifest", "-f", action="store_true", help="package-manifest.json 파일이 존재하더라도 강제로 재설정/재생성합니다.")
    parser.add_argument("--auto-manifest", "-a", action="store_true", help="package-manifest.json 파일이 없을 경우 자동으로 생성합니다.")
    return parser.parse_args()

def validate_slug(slug: str) -> bool:
    # 소문자 영문, 숫자, 하이픈(-)만 허용
    return bool(re.match(r'^[a-z0-9\-]+$', slug))

def extract_image_references(mdx_content: str) -> List[str]:
    # ![alt](../images/filename.png) 또는 ![alt](./images/filename.png) 패턴 매칭
    # [웹 이미지(http/https)는 제외]
    pattern = r'!\[.*?\]\((?:\.\.?/)?images/([^)]+)\)'
    return re.findall(pattern, mdx_content)

def check_toc_node(node: Dict[str, Any], cards_in_toc: List[str], errors: List[str]):
    # [C3] 필수 필드 존재 검사
    for field in ["type", "title", "description"]:
        if field not in node or not str(node.get(field, "")).strip():
            errors.append(f"TOC 노드 오류: 필수 필드 '{field}'가 없거나 비어 있습니다. 노드: {node.get('title', '이름없음')}")
            return

    # [C4] type 값 범위 검사
    node_type = node.get("type")
    if node_type not in ["chapter", "section", "subsection"]:
        errors.append(f"TOC 노드 오류: '{node.get('title')}'의 type이 허용되지 않는 값({node_type})입니다. (chapter, section, subsection만 허용)")

    description = node.get("description", "")
    if description in ["TODO", "설명 없음", "임시 설명", "더미 문구"]:
        errors.append(f"TOC 노드 오류: '{node.get('title')}'의 description에 더미/임시 문구가 사용되었습니다.")

    # leaf 노드 검사
    children = node.get("children")
    filename = node.get("filename")

    if not children:
        # leaf node
        if not filename:
            errors.append(f"TOC 노드 오류: 하위 노드가 없는 leaf 노드 '{node.get('title')}'에 filename 필드가 누락되었습니다.")
        else:
            cards_in_toc.append(filename)
    else:
        # non-leaf node
        if filename:
            errors.append(f"TOC 노드 오류: 하위 노드가 있는 비leaf 노드 '{node.get('title')}'에 filename 필드가 존재합니다 (비leaf 노드는 filename을 가질 수 없습니다).")
        
        # [C3] children 빈 배열 금지
        if len(children) == 0:
            errors.append(f"TOC 노드 오류: 비leaf 노드 '{node.get('title')}'의 children 배열이 비어있습니다.")
        else:
            for child in children:
                check_toc_node(child, cards_in_toc, errors)

def build_course(course_slug: str, package_slug: str = None, force_manifest: bool = False, auto_manifest: bool = False) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. 강좌 경로 설정
    if package_slug:
        course_dir = os.path.join(base_dir, "converted", package_slug, course_slug)
        package_manifest_path = os.path.join(base_dir, "converted", package_slug, "package-manifest.json")
    else:
        course_dir = os.path.join(base_dir, "converted", course_slug)
        package_manifest_path = None

    if not os.path.exists(course_dir):
        # 엣지케이스: 혹시 converted/course_slug/course_slug 형태의 중첩인지 확인
        nested_dir = os.path.join(base_dir, "converted", course_slug, course_slug)
        if os.path.exists(nested_dir):
            course_dir = nested_dir
        else:
            print(f"ERROR: 강좌 디렉토리가 존재하지 않습니다: {course_dir}")
            sys.exit(1)

    print(f"[*] 강좌 빌드 시작: {course_slug} (위치: {course_dir})")

    config_path = os.path.join(course_dir, "config.json")
    manifest_path = os.path.join(course_dir, "package-manifest.json")
    wiki_path = os.path.join(course_dir, "wiki.md")

    errors = []

    # 1. 파일 존재성 검사
    config_exists = os.path.exists(config_path)
    manifest_exists = os.path.exists(manifest_path)
    wiki_exists = os.path.exists(wiki_path)

    if not config_exists:
        errors.append(f"필수 파일 config.json이 존재하지 않습니다: {config_path}")
    if not wiki_exists:
        errors.append(f"필수 파일 wiki.md가 존재하지 않습니다: {wiki_path}")

    # package-manifest.json 자동 복구/생성 로직 (요청 시 또는 force_manifest 시에만 동작)
    if not manifest_exists and auto_manifest:
        print(f"[INFO] package-manifest.json이 없으므로 자동 생성을 시도합니다...")
        do_create_manifest = True
    elif force_manifest:
        print(f"[INFO] force-manifest 옵션에 따라 package-manifest.json 재설정을 시도합니다...")
        do_create_manifest = True
    else:
        do_create_manifest = False

    if not manifest_exists and not do_create_manifest:
        errors.append(f"package-manifest.json 파일이 존재하지 않습니다: {manifest_path}")

    # config.json 로드
    config_data = {}
    if config_exists:
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config_data = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"config.json 파싱 실패: {e}")

    # 매니페스트 생성 처리
    if do_create_manifest and config_exists and not errors:
        # 기본 메타데이터 초기화
        title = config_data.get("title", course_slug)
        description = config_data.get("description", "강좌 요약 설명")
        author = config_data.get("author", {
            "nickname": "Kailash",
            "email": "godstale@hotmail.com",
            "website": "https://hardcopyworld.com"
        })
        category = "Programming"
        target_age = "전연령"
        tags = []
        thumbnail = config_data.get("thumbnail", "icon:book")

        # 만약 패키지 하위 강좌라면, 부모 패키지의 매니페스트를 참고하여 메타데이터 상속
        if package_slug and package_manifest_path and os.path.exists(package_manifest_path):
            try:
                with open(package_manifest_path, "r", encoding="utf-8") as pf:
                    p_manifest = json.load(pf)
                author = p_manifest.get("author", author)
                category = p_manifest.get("category", category)
                target_age = p_manifest.get("target_age", target_age)
                # 패키지 매니페스트 courses 목록에서 본인 정보 상속
                for c in p_manifest.get("courses", []):
                    if c.get("slug") == course_slug:
                        title = c.get("title", title)
                        description = c.get("description", description)
                        tags = c.get("tags", tags)
                        break
            except Exception as e:
                print(f"WARNING: 부모 패키지 매니페스트 읽기 실패: {e}")

        # 단과 강좌이고 config.json에 tags가 있다면 사용
        if not tags:
            tags = config_data.get("tags", ["AI", "Tutorial"])

        # 강좌 package-manifest.json 생성
        manifest_data = {
            "title": title,
            "slug": course_slug,
            "description": description,
            "author": author,
            "thumbnail": thumbnail,
            "published": True,
            "version": "1.0.0",
            "changelog": "최초 릴리즈",
            "bundler_protocol_version": "1.1.1",
            "target_age": target_age,
            "category": category,
            "tags": tags
        }

        try:
            with open(manifest_path, "w", encoding="utf-8") as mf:
                json.dump(manifest_data, mf, ensure_ascii=False, indent=2)
            print(f"[OK] package-manifest.json 파일 생성 완료: {manifest_path}")
            manifest_exists = True
        except Exception as e:
            errors.append(f"package-manifest.json 파일 생성 실패: {e}")

    # package-manifest.json 로드 및 필수 필드 검증 [C8]
    manifest_data = {}
    if manifest_exists and not errors:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"package-manifest.json 파싱 실패 (올바른 JSON 형식이 아닙니다): {e}")

        if manifest_data:
            # 필수 필드
            required_manifest_fields = [
                "title", "slug", "description", "author", "published",
                "version", "changelog", "bundler_protocol_version",
                "target_age", "category", "tags"
            ]
            for field in required_manifest_fields:
                if field not in manifest_data:
                    errors.append(f"[C8] package-manifest.json에 필수 필드가 누락되었습니다: '{field}'")
            
            # author 세부 검사
            author_data = manifest_data.get("author")
            if not author_data or not isinstance(author_data, dict) or "nickname" not in author_data or not str(author_data.get("nickname")).strip():
                errors.append(f"[C8] package-manifest.json의 author.nickname 필드가 유효하지 않거나 누락되었습니다.")

            # tags 세부 검사
            tags_data = manifest_data.get("tags")
            if tags_data is not None:
                if not isinstance(tags_data, list):
                    errors.append("[C8] package-manifest.json의 tags 필드가 배열 형식이 아닙니다.")
                elif len(tags_data) < 3:
                    errors.append("[C8] package-manifest.json의 tags 배열은 최소 3개 이상의 태그를 포함해야 합니다.")

            # 프로토콜 버전
            if manifest_data.get("bundler_protocol_version") != "1.1.1":
                errors.append(f"[C8] 프로토콜 버전이 '1.1.1'이어야 합니다 (현재: '{manifest_data.get('bundler_protocol_version')}')")

    # config.json 상세 검증
    if config_data:
        # [C6] slug 형식 검증
        course_slug_conf = config_data.get("slug")
        if not course_slug_conf:
            errors.append("config.json에 'slug' 필드가 누락되었습니다.")
        elif not validate_slug(course_slug_conf):
            errors.append(f"[C6] config.json의 slug 형식이 잘못되었습니다: '{course_slug_conf}' (소문자, 숫자, 하이픈만 허용)")

        if course_slug != course_slug_conf:
            errors.append(f"강좌 폴더 슬러그({course_slug})와 config.json 내 slug({course_slug_conf})가 일치하지 않습니다.")

        # [C1, C2] cards 리스트 검증
        cards = config_data.get("cards", [])
        if not cards:
            errors.append("config.json에 'cards' 배열이 누락되었거나 비어있습니다.")
        else:
            for idx, card in enumerate(cards):
                # [C1] "cards/" 접두어 금지
                if card.startswith("cards/"):
                    errors.append(f"[C1] cards[{idx}]에 'cards/' 접두어가 사용되었습니다: '{card}' (접두어 없이 파일명만 기재해야 합니다)")

        # [C2, C3, C4, C5] TOC 트리 구조 검사
        toc = config_data.get("toc", [])
        if not toc:
            errors.append("[C12] config.json에 'toc' 목차 트리 배열이 누락되었거나 비어있습니다.")

        cards_in_toc = []
        if toc:
            for node in toc:
                check_toc_node(node, cards_in_toc, errors)

        # filename 형식 검사 및 접두어 확인
        for filename in cards_in_toc:
            if filename.startswith("cards/"):
                errors.append(f"[C1] TOC leaf filename에 'cards/' 접두어가 사용되었습니다: '{filename}' (파일명만 기재해야 합니다)")

        # [C2] toc leaf 집합 ↔ cards[] 완전 일치 대조
        if cards and cards_in_toc:
            cards_set = set(cards)
            toc_cards_set = set(cards_in_toc)

            missing_in_toc = cards_set - toc_cards_set
            missing_in_cards = toc_cards_set - cards_set

            if missing_in_toc:
                errors.append(f"[C2] TOC leaf 노드에 누락된 카드가 존재합니다 (cards[] 에는 있으나 TOC 에는 없음): {missing_in_toc}")
            if missing_in_cards:
                errors.append(f"[C2] cards[] 배열에 누락된 카드가 존재합니다 (TOC 에는 있으나 cards[] 에는 없음): {missing_in_cards}")

        # [C7] checkpoints.afterCard 존재 검증
        checkpoints = config_data.get("checkpoints", [])
        if checkpoints and cards:
            cards_set = set(cards)
            for cp in checkpoints:
                after_card = cp.get("afterCard")
                if not after_card:
                    errors.append(f"checkpoints 항목에 'afterCard'가 누락되었습니다.")
                elif after_card not in cards_set:
                    errors.append(f"[C7] checkpoints.afterCard '{after_card}'가 cards[] 리스트에 존재하지 않습니다.")

        # 카드 실제 파일 존재 여부 및 이미지 리소스 실재 확인 [C10]
        if cards:
            cards_dir = os.path.join(course_dir, "cards")
            images_dir = os.path.join(course_dir, "images")
            
            if not os.path.exists(cards_dir):
                errors.append(f"cards/ 디렉토리가 존재하지 않습니다: {cards_dir}")
            else:
                for card_file in cards:
                    card_path = os.path.join(cards_dir, card_file)
                    if not os.path.exists(card_path):
                        errors.append(f"실물 카드 파일이 존재하지 않습니다: {card_path}")
                        continue

                    # [C10] MDX 내 로컬 이미지 링크 유효성 검사
                    if card_file.endswith(".mdx") or card_file.endswith(".md"):
                        try:
                            with open(card_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            image_refs = extract_image_references(content)
                            for img in image_refs:
                                img_path = os.path.join(images_dir, img)
                                if not os.path.exists(img_path):
                                    errors.append(f"[C10] 카드 '{card_file}'에서 참조하는 로컬 이미지 파일이 존재하지 않습니다: {img} (경로: {img_path})")
                        except Exception as e:
                            errors.append(f"카드 파일 '{card_file}' 읽기 실패: {e}")

    # 4. 검증 리포트
    if errors:
        print("\n[ERROR] 검증 실패! 다음 오류들을 수정해주세요:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[OK] 모든 검증 통과! (C1 ~ C11 통과 완료)")

    # 5. ZIP 압축 생성 [Z1, Z2]
    # ZIP 파일은 항상 converted/<course-slug>/<course-slug>.zip 에 생성
    zip_out_path = os.path.join(course_dir, f"{course_slug}.zip")
    
    if os.path.exists(zip_out_path):
        os.remove(zip_out_path)

    print(f"[*] ZIP 생성 시작: {zip_out_path}")
    
    with zipfile.ZipFile(zip_out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # package-manifest.json
        zf.write(manifest_path, "package-manifest.json")
        # config.json
        zf.write(config_path, "config.json")
        # wiki.md
        zf.write(wiki_path, "wiki.md")
        
        # cards/
        if os.path.exists(cards_dir):
            for root, dirs, files in os.walk(cards_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, course_dir).replace('\\', '/')
                    zf.write(full_path, arcname)

        # images/
        if os.path.exists(images_dir):
            for root, dirs, files in os.walk(images_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, course_dir).replace('\\', '/')
                    zf.write(full_path, arcname)

    print(f"[OK] ZIP 생성 성공: {zip_out_path} ({os.path.getsize(zip_out_path)} bytes)")

    # 6. ZIP 파일 사후 검증 [Z2]
    print(f"[*] ZIP 파일 사후 검증 시작: {zip_out_path}")
    try:
        with zipfile.ZipFile(zip_out_path, 'r') as zf:
            namelist = zf.namelist()
            zip_errors = []
            
            # 필수 파일 존재 검사
            for required in ["package-manifest.json", "config.json", "wiki.md"]:
                if required not in namelist:
                    zip_errors.append(f"ZIP 내부에 '{required}' 파일이 누락되었습니다.")
            
            # cards 및 images 경로 검사
            for name in namelist:
                if name in ["package-manifest.json", "config.json", "wiki.md"]:
                    continue
                if not (name.startswith("cards/") or name.startswith("images/")):
                    zip_errors.append(f"ZIP 내부에 올바르지 않은 경로의 파일이 포함되어 있습니다: '{name}' (cards/ 또는 images/ 하위 경로여야 합니다.)")
                    
            if zip_errors:
                print("\n[ERROR] ZIP 파일 사후 검증 실패! 다음 파일 오류를 해결하세요:")
                for err in zip_errors:
                    print(f"  - {err}")
                os.remove(zip_out_path)
                sys.exit(1)
            else:
                print(f"[OK] ZIP 파일 사후 검증 완료 (config.json, package-manifest.json, wiki.md 모두 정상 포함)")
    except Exception as e:
        print(f"ERROR: ZIP 파일 사후 검증 중 예외 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    args = parse_args()
    build_course(args.course_slug, args.package, args.force_manifest, args.auto_manifest)
