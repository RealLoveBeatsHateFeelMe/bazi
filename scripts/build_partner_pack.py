# -*- coding: utf-8 -*-
"""构建 partner 发布包：包含文档、schema、fixtures、回归报告等。"""

import os
import sys
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist"


def ensure_dir(path: Path) -> None:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)


def run_command(cmd: list[str], cwd: Path = None) -> tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout, stderr)。"""
    result = subprocess.run(
        cmd,
        cwd=cwd or ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout or "", result.stderr or ""


def get_git_sha() -> str:
    """获取当前 git commit SHA（短版本，7位）。"""
    returncode, stdout, _ = run_command(["git", "rev-parse", "--short=7", "HEAD"])
    if returncode != 0:
        # 如果没有 git 或不在 git 仓库中，返回 "unknown"
        return "unknown"
    return stdout.strip()


def extract_contract_version() -> str:
    """从 API_CONTRACT.md 提取 contract_version。"""
    contract_path = ROOT_DIR / "docs" / "partner" / "API_CONTRACT.md"
    content = contract_path.read_text(encoding="utf-8")
    
    # 匹配 "# API Contract Version X.Y.Z"
    match = re.search(r"# API Contract Version (\d+\.\d+\.\d+)", content)
    if match:
        return match.group(1)
    
    # 如果没有找到，尝试从第一行提取
    lines = content.split("\n")
    for line in lines[:5]:
        match = re.search(r"Version (\d+\.\d+\.\d+)", line)
        if match:
            return match.group(1)
    
    # 默认版本号
    return "1.0.0"


def update_api_contract_version(version: str) -> None:
    """在 API_CONTRACT.md 顶部添加/更新 contract_version。"""
    contract_path = ROOT_DIR / "docs" / "partner" / "API_CONTRACT.md"
    content = contract_path.read_text(encoding="utf-8")
    
    # 检查是否已有版本号
    if content.startswith("## Analyze 基础接口约定"):
        # 在开头添加版本号
        version_header = f"# API Contract Version {version}\n\n"
        content = version_header + content
    
    # 如果已有版本号，更新它
    lines = content.split("\n")
    if lines[0].startswith("# API Contract Version"):
        lines[0] = f"# API Contract Version {version}"
        content = "\n".join(lines)
    
    contract_path.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新 API_CONTRACT.md 版本号为 {version}")


def run_regress() -> str:
    """运行回归测试，返回输出。"""
    print("运行回归测试...")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "bazi.regress"])
    
    if returncode != 0:
        print(f"[FAIL] 回归测试失败！\nstdout:\n{stdout}\nstderr:\n{stderr}", file=sys.stderr)
        sys.exit(1)
    
    print("[OK] 回归测试通过")
    return stdout + "\n" + stderr


def export_fixtures() -> None:
    """重新导出 fixtures。"""
    print("重新导出 fixtures...")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "bazi.export_fixtures"])
    
    if returncode != 0:
        print(f"[FAIL] 导出 fixtures 失败！\nstdout:\n{stdout}\nstderr:\n{stderr}", file=sys.stderr)
        sys.exit(1)
    
    print("[OK] fixtures 已重新导出")


def validate_fixtures() -> None:
    """校验 fixtures 是否符合 schema。"""
    print("校验 fixtures...")
    try:
        import jsonschema
    except ImportError:
        print("[WARN] jsonschema 未安装，跳过 fixtures 校验")
        print("       如需校验，请运行：pip install jsonschema")
        return
    
    returncode, stdout, stderr = run_command([
        sys.executable,
        str(ROOT_DIR / "scripts" / "validate_fixtures.py")
    ])
    
    if returncode != 0:
        print(f"[FAIL] fixtures 校验失败！\nstdout:\n{stdout}\nstderr:\n{stderr}", file=sys.stderr)
        sys.exit(1)
    
    print("[OK] fixtures 校验通过")


def create_changelog(version: str, git_sha: str) -> str:
    """创建 CHANGELOG.md（自动生成版本号 + 简要变更点）。"""
    # 尝试从 git log 获取最近的变更
    returncode, git_log, _ = run_command([
        "git", "log", "--oneline", "-10", "--no-decorate"
    ])
    
    recent_changes = []
    if returncode == 0 and git_log:
        lines = git_log.strip().split("\n")[:5]  # 最近 5 条
        recent_changes = [f"- {line}" for line in lines if line.strip()]
    
    changelog = f"""# Changelog

## Version {version} - {datetime.now().strftime("%Y-%m-%d")}

**Git SHA**: `{git_sha}`

### 变更摘要

"""
    
    if recent_changes:
        changelog += "**最近提交**:\n"
        changelog += "\n".join(recent_changes)
        changelog += "\n\n"
    
    changelog += """### 详细变更

请参考 `BAZI_RULES.md`、`CODEMAP.md` 和 `API_CONTRACT.md` 获取详细变更说明。

---
"""
    return changelog


def create_manifest(version: str, git_sha: str, files_in_zip: list[str]) -> dict:
    """创建 MANIFEST.json。"""
    return {
        "contract_version": version,
        "git_sha": git_sha,
        "build_time": datetime.now().isoformat(),
        "files": sorted(files_in_zip),
        "file_count": len(files_in_zip),
    }


def detect_schema_changes(version: str) -> list[str]:
    """检测 schema 变更（简单实现：列出所有 schema 文件）。"""
    schema_dir = ROOT_DIR / "schemas"
    schema_files = list(schema_dir.glob("*.json"))
    return [f.name for f in schema_files]


def detect_new_fields_from_schema() -> list[str]:
    """从 schema 检测新增字段（简化实现）。"""
    # 这里可以解析 schema 的 required 字段，但为了简化，先返回空列表
    # 后续可以扩展为解析 analyze_basic.schema.json 的 required 字段
    return []


def create_email_to_partner(version: str, git_sha: str, build_time: str) -> str:
    """生成给 partner 的发包文案。"""
    schema_files = detect_schema_changes(version)
    new_fields = detect_new_fields_from_schema()
    
    email = f"""# Partner 发包说明

## Contract Version

**{version}** (Git SHA: `{git_sha}`, Build Time: {build_time})

## 本次新增/变更字段列表

### Schema 文件
"""
    for schema_file in schema_files:
        email += f"- `schemas/{schema_file}`\n"
    
    if new_fields:
        email += "\n### 新增字段\n"
        for field in new_fields:
            email += f"- `{field}`\n"
    else:
        email += "\n### 新增字段\n"
        email += "- 请查看 `API_CONTRACT.md` 和 `CHANGELOG.md` 获取详细变更\n"
    
    email += """
## 兼容性说明

- **新增字段可忽略**：如果前端遇到未知字段，可以安全忽略，不影响现有功能
- **破坏性变更**：如有破坏性变更，会在 `CHANGELOG.md` 中明确标注
- **字段类型变更**：请参考 `schemas/*.json` 中的类型定义

## 如何验收

### 1. 回归测试

```bash
python -m bazi.regress
```

**要求**：必须全绿（ALL REGRESSION TESTS PASS）

### 2. Schema 校验

```bash
python scripts/validate_fixtures.py
```

**要求**：所有 fixtures 必须通过对应 schema 校验

### 3. 验证发布包

```bash
python scripts/verify_pack.py
```

**要求**：解包检查通过，schema 校验通过，regress 通过

## 文件清单

请参考 `MANIFEST.json` 查看完整的文件清单。

---
"""
    return email


def build_pack() -> tuple[str, str, str]:
    """构建发布包，返回 (pack_path, version, git_sha)。"""
    # 1. 确保目录存在
    ensure_dir(DIST_DIR)
    
    # 2. 获取版本号和 git SHA
    version = extract_contract_version()
    git_sha = get_git_sha()
    
    print(f"构建 partner 发布包 v{version} (git: {git_sha})...")
    
    # 3. 更新 API_CONTRACT.md 版本号（确保一致）
    update_api_contract_version(version)
    
    # 4. 运行回归测试
    regress_output = run_regress()
    
    # 5. 重新导出 fixtures
    export_fixtures()
    
    # 6. 校验 fixtures
    validate_fixtures()
    
    # 7. 创建 CHANGELOG.md
    changelog = create_changelog(version, git_sha)
    changelog_path = ROOT_DIR / "CHANGELOG.md"
    changelog_path.write_text(changelog, encoding="utf-8")
    print("[OK] 已创建 CHANGELOG.md")
    
    # 8. 保存回归报告
    report_path = ROOT_DIR / "REGRESS_REPORT.txt"
    report_path.write_text(regress_output, encoding="utf-8")
    print("[OK] 已保存 REGRESS_REPORT.txt")
    
    # 9. 构建 zip 包
    pack_name = f"partner_pack_{version}_{git_sha}.zip"
    pack_path = DIST_DIR / pack_name
    
    files_in_zip = []
    
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 文档
        zf.write(ROOT_DIR / "bazi" / "BAZI_RULES.md", "BAZI_RULES.md")
        files_in_zip.append("BAZI_RULES.md")
        
        zf.write(ROOT_DIR / "CODEMAP.md", "CODEMAP.md")
        files_in_zip.append("CODEMAP.md")
        
        zf.write(ROOT_DIR / "docs" / "partner" / "API_CONTRACT.md", "API_CONTRACT.md")
        files_in_zip.append("API_CONTRACT.md")
        
        # Schema
        schema_dir = ROOT_DIR / "schemas"
        for schema_file in schema_dir.glob("*.json"):
            rel_path = f"schemas/{schema_file.name}"
            zf.write(schema_file, rel_path)
            files_in_zip.append(rel_path)
        
        # Fixtures
        fixtures_dir = ROOT_DIR / "fixtures"
        for fixture_file in fixtures_dir.glob("*.json"):
            rel_path = f"fixtures/{fixture_file.name}"
            zf.write(fixture_file, rel_path)
            files_in_zip.append(rel_path)
        
        # 回归测试
        zf.write(ROOT_DIR / "bazi" / "regress.py", "bazi/regress.py")
        files_in_zip.append("bazi/regress.py")
        
        zf.write(ROOT_DIR / "REGRESS_REPORT.txt", "REGRESS_REPORT.txt")
        files_in_zip.append("REGRESS_REPORT.txt")
        
        # CHANGELOG
        zf.write(ROOT_DIR / "CHANGELOG.md", "CHANGELOG.md")
        files_in_zip.append("CHANGELOG.md")
        
        # MANIFEST（需要在最后添加，因为 files_in_zip 需要包含它）
        # 注意：MANIFEST.json 本身不包含在 files_in_zip 中（避免循环）
        manifest = create_manifest(version, git_sha, files_in_zip)
        manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
        zf.writestr("MANIFEST.json", manifest_json)
    
    # 10. 生成 EMAIL_TO_PARTNER.md
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_content = create_email_to_partner(version, git_sha, build_time)
    email_path = DIST_DIR / "EMAIL_TO_PARTNER.md"
    email_path.write_text(email_content, encoding="utf-8")
    print("[OK] 已生成 EMAIL_TO_PARTNER.md")
    
    print(f"\n[SUCCESS] 发布包已生成：{pack_path}")
    print(f"   大小：{pack_path.stat().st_size / 1024:.1f} KB")
    print(f"   版本：{version}")
    print(f"   Git SHA：{git_sha}")
    print(f"\n包含文件：")
    with zipfile.ZipFile(pack_path, "r") as zf:
        for name in sorted(zf.namelist()):
            print(f"   - {name}")
    
    return str(pack_path), version, git_sha


if __name__ == "__main__":
    build_pack()
