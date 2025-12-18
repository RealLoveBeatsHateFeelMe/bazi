# -*- coding: utf-8 -*-
"""一键发布流程：构建发布包 + 验证完整性 + 运行校验。"""

import zipfile
import json
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist"


def run_command(cmd: list[str], cwd: Path = None) -> tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout, stderr)。"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout or "", result.stderr or ""


def build_pack() -> Path:
    """构建发布包。"""
    print("=" * 60)
    print("步骤 1: 构建发布包")
    print("=" * 60)
    
    returncode, stdout, stderr = run_command(
        [sys.executable, str(ROOT_DIR / "scripts" / "build_partner_pack.py")],
        cwd=ROOT_DIR
    )
    
    if returncode != 0:
        print(f"[FAIL] 构建发布包失败！\n{stdout}\n{stderr}", file=sys.stderr)
        sys.exit(1)
    
    # 查找最新生成的发布包
    pack_files = list(DIST_DIR.glob("partner_pack_*.zip"))
    if not pack_files:
        print("[FAIL] 未找到生成的发布包", file=sys.stderr)
        sys.exit(1)
    
    latest_pack = max(pack_files, key=lambda p: p.stat().st_mtime)
    print(f"[OK] 发布包已生成: {latest_pack.name}")
    return latest_pack


def verify_pack_structure(pack_path: Path) -> bool:
    """验证发布包文件结构。"""
    print("\n" + "=" * 60)
    print("步骤 2: 验证发布包文件结构")
    print("=" * 60)
    
    required_files = [
        "BAZI_RULES.md",
        "CODEMAP.md",
        "API_CONTRACT.md",
        "CHANGELOG.md",
        "REGRESS_REPORT.txt",
        "MANIFEST.json",
        "bazi/regress.py",
        "schemas/analyze_basic.schema.json",
        "schemas/api_response.schema.json",
        "fixtures/traits_T1_2005.json",
        "fixtures/traits_T2_2007.json",
    ]
    
    with zipfile.ZipFile(pack_path, "r") as zf:
        files = set(zf.namelist())
        missing = [f for f in required_files if f not in files]
        
        if missing:
            print(f"[FAIL] 缺少必需文件:", file=sys.stderr)
            for f in missing:
                print(f"  - {f}", file=sys.stderr)
            return False
        
        print(f"[OK] 必需文件检查通过 ({len(files)} 个文件)")
        
        # 验证 API_CONTRACT 版本号
        contract_content = zf.read("API_CONTRACT.md").decode("utf-8")
        if not contract_content.startswith("# API Contract Version"):
            print("[WARN] API_CONTRACT.md 顶部可能缺少版本号", file=sys.stderr)
        else:
            print("[OK] API_CONTRACT.md 版本号格式正确")
        
        # 读取并显示 MANIFEST
        try:
            manifest_content = zf.read("MANIFEST.json").decode("utf-8")
            manifest = json.loads(manifest_content)
            print(f"[INFO] Contract Version: {manifest.get('contract_version', 'unknown')}")
            print(f"[INFO] Git SHA: {manifest.get('git_sha', 'unknown')}")
            print(f"[INFO] Build Time: {manifest.get('build_time', 'unknown')}")
        except Exception as e:
            print(f"[WARN] 无法读取 MANIFEST.json: {e}", file=sys.stderr)
    
    return True


def verify_schema_validation() -> bool:
    """在项目根目录运行 schema 校验。"""
    print("\n" + "=" * 60)
    print("步骤 3: Schema 校验")
    print("=" * 60)
    
    returncode, stdout, stderr = run_command(
        [sys.executable, str(ROOT_DIR / "scripts" / "validate_fixtures.py")],
        cwd=ROOT_DIR
    )
    
    # 安全输出（避免编码错误）- 直接写入 buffer
    if stdout:
        sys.stdout.buffer.write(stdout.encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')
        sys.stdout.buffer.flush()
    if stderr:
        sys.stderr.buffer.write(stderr.encode('utf-8', errors='replace'))
        sys.stderr.buffer.write(b'\n')
        sys.stderr.buffer.flush()
    
    if returncode != 0:
        print("[FAIL] Schema 校验失败", file=sys.stderr)
        return False
    
    print("[OK] Schema 校验通过")
    return True


def verify_regress() -> bool:
    """在项目根目录运行回归测试。"""
    print("\n" + "=" * 60)
    print("步骤 4: 回归测试")
    print("=" * 60)
    
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "bazi.regress"],
        cwd=ROOT_DIR
    )
    
    # 安全输出（避免编码错误）
    if stdout:
        try:
            print(stdout)
        except (UnicodeEncodeError, UnicodeDecodeError):
            sys.stdout.buffer.write(stdout.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\n')
    if stderr:
        try:
            print(stderr, file=sys.stderr)
        except (UnicodeEncodeError, UnicodeDecodeError):
            sys.stderr.buffer.write(stderr.encode('utf-8', errors='replace'))
            sys.stderr.buffer.write(b'\n')
    
    if returncode != 0:
        print("[FAIL] 回归测试失败", file=sys.stderr)
        return False
    
    print("[OK] 回归测试通过")
    return True


def main() -> None:
    """主流程：构建 + 验证。"""
    print("\n" + "=" * 60)
    print("Partner 发布包一键构建与验证")
    print("=" * 60 + "\n")
    
    # 1. 构建发布包
    pack_path = build_pack()
    
    # 2. 验证文件结构
    if not verify_pack_structure(pack_path):
        print("\n[FAIL] 发布包文件结构验证失败", file=sys.stderr)
        sys.exit(1)
    
    # 3. Schema 校验（在项目根目录运行）
    if not verify_schema_validation():
        print("\n[FAIL] Schema 校验失败", file=sys.stderr)
        sys.exit(1)
    
    # 4. 回归测试（在项目根目录运行）
    if not verify_regress():
        print("\n[FAIL] 回归测试失败", file=sys.stderr)
        sys.exit(1)
    
    # 5. 显示最终结果
    print("\n" + "=" * 60)
    print("[SUCCESS] 发布包构建与验证完成！")
    print("=" * 60)
    print(f"\n发布包: {pack_path}")
    print(f"邮件文案: {DIST_DIR / 'EMAIL_TO_PARTNER.md'}")
    print("\n请将以下文件发送给 partner:")
    print(f"  1. {pack_path.name}")
    print(f"  2. {DIST_DIR / 'EMAIL_TO_PARTNER.md'}")
    print()


if __name__ == "__main__":
    main()
