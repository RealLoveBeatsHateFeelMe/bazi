# Partner 发包说明

## Contract Version

**1.0.0** (Git SHA: `unknown`, Build Time: 2025-12-17 17:08:42)

## 本次新增/变更字段列表

### Schema 文件
- `schemas/analyze_basic.schema.json`
- `schemas/analyze_luck.schema.json`
- `schemas/api_response.schema.json`

### 新增字段
- 请查看 `API_CONTRACT.md` 和 `CHANGELOG.md` 获取详细变更

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
