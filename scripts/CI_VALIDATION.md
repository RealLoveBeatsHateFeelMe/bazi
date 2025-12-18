# CI 验收门禁

## 发版前必须执行的验收步骤

### 1. 回归测试

```bash
python -m bazi.regress
```

**要求**：必须全绿（ALL REGRESSION TESTS PASS）

**覆盖范围**：
- 刑规则回归（辰未不刑）
- Traits T1/T2 回归
- 用神 special_rules 回归（补木、补火）

### 2. Fixtures Schema 校验

```bash
python scripts/validate_fixtures.py
```

**要求**：所有 fixtures 必须通过 `schemas/analyze_basic.schema.json` 校验

**说明**：
- 需要安装 `jsonschema`：`pip install jsonschema`
- 校验所有 `fixtures/*.json` 文件
- 确保字段类型、required 字段、enum 值都符合 schema

### 3. 构建发布包

```bash
python scripts/build_partner_pack.py
```

**要求**：
- 自动执行步骤 1 和 2（如果失败则中断）
- 生成 `dist/partner_pack_vX.Y.Z.zip`
- 包含所有必需文件（见下方清单）

### 4. 发布包内容验证

**必需文件清单**：
- `BAZI_RULES.md`
- `CODEMAP.md`
- `API_CONTRACT.md`（顶部包含 `contract_version: X.Y.Z`）
- `schemas/analyze_basic.schema.json`
- `schemas/api_response.schema.json`
- `fixtures/traits_T1_2005.json`
- `fixtures/traits_T2_2007.json`
- `bazi/regress.py`
- `REGRESS_REPORT.txt`
- `CHANGELOG.md`

## CI 配置示例

### GitHub Actions

```yaml
name: Partner Pack Validation

on:
  push:
    tags:
      - 'v*'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt jsonschema
      - run: python -m bazi.regress
      - run: python scripts/validate_fixtures.py
      - run: python scripts/build_partner_pack.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: partner-pack
          path: dist/partner_pack_*.zip
```

### 本地验证

```bash
# 1. 安装依赖
pip install -r requirements.txt jsonschema

# 2. 运行验收
python -m bazi.regress
python scripts/validate_fixtures.py
python scripts/build_partner_pack.py

# 3. 验证发布包
unzip -l dist/partner_pack_v*.zip
```

## 验收标准

- ✅ 回归测试：6 个用例全部通过
- ✅ Schema 校验：所有 fixtures 通过校验
- ✅ 发布包：包含所有必需文件，zip 可正常解压
- ✅ 文档版本号：API_CONTRACT.md 顶部包含正确版本号
- ✅ CHANGELOG：包含本次变更的完整说明
