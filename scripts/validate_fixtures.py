# -*- coding: utf-8 -*-
"""校验 fixtures 是否符合 schema。"""

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("错误：需要安装 jsonschema 库")
    print("请运行：pip install jsonschema")
    sys.exit(1)


ROOT_DIR = Path(__file__).parent.parent
SCHEMA_DIR = ROOT_DIR / "schemas"
FIXTURES_DIR = ROOT_DIR / "fixtures"


def validate_fixtures() -> bool:
    """校验所有 fixtures 是否符合 schema。"""
    # 加载 schema
    schema_path = SCHEMA_DIR / "analyze_basic.schema.json"
    if not schema_path.exists():
        print(f"[FAIL] Schema 文件不存在: {schema_path}", file=sys.stderr)
        return False
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    validator = Draft7Validator(schema)
    
    # 校验所有 fixtures
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    if not fixture_files:
        print(f"[FAIL] 未找到 fixtures 文件", file=sys.stderr)
        return False
    
    all_valid = True
    passed_count = 0
    failed_count = 0
    
    for fixture_path in fixture_files:
        with open(fixture_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[FAIL] {fixture_path.name}: JSON 解析失败 - {e}", file=sys.stderr)
                all_valid = False
                failed_count += 1
                continue
        
        errors = list(validator.iter_errors(data))
        if errors:
            print(f"[FAIL] {fixture_path.name}: 校验失败")
            for error in errors[:5]:  # 最多显示 5 个错误
                print(f"   路径: {'.'.join(str(p) for p in error.path)}")
                print(f"   错误: {error.message}")
            if len(errors) > 5:
                print(f"   ... 还有 {len(errors) - 5} 个错误")
            all_valid = False
            failed_count += 1
        else:
            print(f"[OK] {fixture_path.name}: 校验通过")
            passed_count += 1
    
    # 输出摘要
    print(f"\n摘要: 通过 {passed_count}/{len(fixture_files)}, 失败 {failed_count}/{len(fixture_files)}")
    
    return all_valid


if __name__ == "__main__":
    success = validate_fixtures()
    sys.exit(0 if success else 1)
