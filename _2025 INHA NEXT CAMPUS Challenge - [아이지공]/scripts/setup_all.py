#!/usr/bin/env python3
"""
전체 환경을 한 번에 설정하는 스크립트
- DB 초기화 → 데이터 적재 → 요약본 생성 → 검증
"""
from pathlib import Path
import sys
import subprocess

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(name: str) -> bool:
    """스크립트를 실행하고 성공 여부를 반환"""
    script_path = SCRIPTS_DIR / name
    print(f"\n{'='*60}")
    print(f"실행 중: {name}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"⚠️  경고: {name} 실행 중 오류 발생 (계속 진행)")
            return False
        return True
    except Exception as e:
        print(f"❌ 오류: {name} 실행 실패: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 전체 환경 설정 시작")
    print("=" * 60)

    steps = [
        ("clear_db.py", "데이터베이스 초기화", True),
        ("init_db.py", "테이블 생성", True),
        ("import_data.py", "데이터 적재", True),
        ("verify_counts.py", "데이터 검증", True),
        ("export_summaries.py", "요약본 생성", True),
        ("verify_exports.py", "요약본 검증", True),
    ]

    failed = []
    for script, desc, required in steps:
        print(f"\n📋 {desc}...")
        success = run_script(script)
        if not success and required:
            failed.append((script, desc))

    print("\n" + "=" * 60)
    if failed:
        print("⚠️  일부 단계에서 문제가 발생했습니다:")
        for script, desc in failed:
            print(f"   - {desc} ({script})")
        print("\n나머지 단계는 정상 완료되었습니다.")
    else:
        print("✅ 전체 설정 완료!")
        print("\n📦 생성된 파일:")
        print(f"   - 데이터베이스: {PROJECT_ROOT / 'app.db'}")
        print(f"   - 요약본: {PROJECT_ROOT / 'exports'}")
        print("\n🌐 웹으로 보기:")
        print(f"   cd {PROJECT_ROOT / 'exports'} && python -m http.server 8000")
    print("=" * 60)


if __name__ == "__main__":
    main()


