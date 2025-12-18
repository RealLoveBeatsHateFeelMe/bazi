.PHONY: partner-release build-pack validate verify

# 一键发布（推荐）
partner-release:
	@python scripts/verify_pack.py

# 仅构建发布包
build-pack:
	@python scripts/build_partner_pack.py

# 仅校验 fixtures
validate:
	@python scripts/validate_fixtures.py

# 仅验证发布包结构
verify:
	@python -c "from scripts.verify_pack import verify_pack_structure; from pathlib import Path; import sys; dist = Path('dist'); packs = list(dist.glob('partner_pack_*.zip')); sys.exit(0 if packs and verify_pack_structure(max(packs, key=lambda p: p.stat().st_mtime)) else 1)"
