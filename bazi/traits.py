# -*- coding: utf-8 -*-
"""主要性格 dominant_traits 计算：只看原局，按五大十神 + 子类拆分。"""

from typing import Dict, Any, List, Set, Optional

from .config import POSITION_WEIGHTS, GAN_WUXING, ZHI_WUXING
from .shishen import get_shishen, get_branch_main_gan, classify_shishen_category, WUXING_KE, WUXING_SHENG


# 五大类固定顺序，便于前端展示
CATEGORIES = ["印星", "财星", "官杀", "食伤", "比劫"]

# 每个大类下的具体十神子类
CATEGORY_SUBS: Dict[str, tuple[str, str]] = {
    "印星": ("正印", "偏印"),
    "财星": ("正财", "偏财"),
    "官杀": ("正官", "七杀"),
    "食伤": ("食神", "伤官"),
    "比劫": ("比肩", "劫财"),
}

# 凶神集合（硬编码）：偏印、七杀、伤官、劫财
# 注意：偏财不算凶神
XIONGSHEN_SET: Set[str] = {"偏印", "七杀", "伤官", "劫财"}


def _group_label(cat: str) -> str:
    if cat == "印星":
        return "印"
    if cat == "财星":
        return "财"
    return cat


def _get_category_element_by_definition(cat: str, day_gan: str) -> Optional[str]:
    """根据十神定义计算大类对应的五行，即使该大类在八字中没有出现。
    
    规则：
    - 官杀：他克我 -> 克日主的五行
    - 财星：我克他 -> 日主克的五行
    - 印星：他生我 -> 生日主的五行
    - 食伤：我生他 -> 日主生的五行
    - 比劫：同我 -> 日主的五行
    """
    if day_gan not in GAN_WUXING:
        return None
    
    day_element = GAN_WUXING[day_gan]
    
    if cat == "官杀":
        # 他克我：找到克日主的五行
        # WUXING_KE: key 克 value
        for ke_element, be_ke_element in WUXING_KE.items():
            if be_ke_element == day_element:
                return ke_element
    elif cat == "财星":
        # 我克他：日主克的五行
        return WUXING_KE.get(day_element)
    elif cat == "印星":
        # 他生我：生日主的五行
        # WUXING_SHENG: key 生 value
        for sheng_element, be_sheng_element in WUXING_SHENG.items():
            if be_sheng_element == day_element:
                return sheng_element
    elif cat == "食伤":
        # 我生他：日主生的五行
        return WUXING_SHENG.get(day_element)
    elif cat == "比劫":
        # 同我：日主的五行
        return day_element
    
    return None


def _mix_label(cat: str, present_subs: List[str]) -> str:
    if len(present_subs) >= 2:
        if cat == "印星":
            return "正偏印混杂"
        if cat == "财星":
            return "正偏财混杂"
        if cat == "官杀":
            return "官杀混杂"
        if cat == "食伤":
            return "食伤混杂"
        if cat == "比劫":
            return "比劫混杂"
        return "混杂"
    if len(present_subs) == 1:
        only = present_subs[0]
        return f"纯{only}"
    return cat


def compute_dominant_traits(bazi: Dict[str, Dict[str, str]], day_gan: str) -> List[Dict[str, Any]]:
    """按业务口径计算主要性格 dominant_traits。

    只看原局（natal），不看大运/流年。

    - 统计位置：
      - 年干 / 月干 / 时干（排除日干）；
      - 四柱地支主气（年支 / 月支 / 日支 / 时支，通过主气代表天干计算十神）。
    - 权重使用 POSITION_WEIGHTS；
    - 输出：
      - 每个五大类的 total_percent；
      - 每个子类（正印/偏印、正财/偏财等）的 percent；
      - 每个子类的 stems_visible_count（年/月/时三干中透出的次数）；
      - breakdown: {"stems_percent","branches_percent"}；
      - 每个大类的 mix_label（“正偏财混杂” / “官杀混杂” / “纯偏印”等）。
    """
    # 初始化累加器
    total_weight = 0.0
    cat_weight: Dict[str, float] = {c: 0.0 for c in CATEGORIES}

    # 子类在“天干 / 地支”两部分的权重
    sub_stem_weight: Dict[str, Dict[str, float]] = {
        c: {sub: 0.0 for sub in CATEGORY_SUBS[c]} for c in CATEGORIES
    }
    sub_branch_weight: Dict[str, Dict[str, float]] = {
        c: {sub: 0.0 for sub in CATEGORY_SUBS[c]} for c in CATEGORIES
    }

    stems_visible_count: Dict[str, int] = {}
    # 记录每个子类在哪些柱位透出（用于打印）
    sub_stem_pillars: Dict[str, List[str]] = {}
    # 记录每个大类对应的五行（用于判断用神）
    cat_elements: Dict[str, Set[str]] = {c: set() for c in CATEGORIES}

    # 1. 年干 / 月干 / 时干（排除日干）
    for pillar in ("year", "month", "hour"):
        gan = bazi[pillar]["gan"]
        key = f"{pillar}_gan"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        ss = get_shishen(day_gan, gan)
        if not ss:
            continue

        cat = classify_shishen_category(ss)
        if not cat or cat not in CATEGORY_SUBS:
            continue

        total_weight += w
        cat_weight[cat] += w
        if ss in sub_stem_weight[cat]:
            sub_stem_weight[cat][ss] += w

        # 头上透出的次数（只看三天干）
        stems_visible_count[ss] = stems_visible_count.get(ss, 0) + 1
        
        # 记录透出柱位
        if ss not in sub_stem_pillars:
            sub_stem_pillars[ss] = []
        sub_stem_pillars[ss].append(pillar)
        
        # 记录该大类对应的五行（从天干）
        gan_element = GAN_WUXING.get(gan)
        if gan_element:
            cat_elements[cat].add(gan_element)

    # 2. 四柱地支主气
    for pillar in ("year", "month", "day", "hour"):
        zhi = bazi[pillar]["zhi"]
        key = f"{pillar}_zhi"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        main_gan = get_branch_main_gan(zhi)
        if not main_gan:
            continue

        ss = get_shishen(day_gan, main_gan)
        if not ss:
            continue

        cat = classify_shishen_category(ss)
        if not cat or cat not in CATEGORY_SUBS:
            continue

        total_weight += w
        cat_weight[cat] += w
        if ss in sub_branch_weight[cat]:
            sub_branch_weight[cat][ss] += w
        
        # 记录该大类对应的五行（从地支主气）
        zhi_element = ZHI_WUXING.get(zhi)
        if zhi_element:
            cat_elements[cat].add(zhi_element)

    # 若完全没有有效权重，直接返回空列表
    if total_weight <= 0:
        return []

    traits: List[Dict[str, Any]] = []

    for cat in CATEGORIES:
        cat_w = cat_weight.get(cat, 0.0)
        # 即使权重为0，也要计算并返回该大类的信息（包括五行）
        # if cat_w <= 0:
        #     continue

        total_percent = round((cat_w / total_weight) * 100.0, 1)

        subs = CATEGORY_SUBS[cat]
        present_subs: List[str] = []
        detail_items: List[Dict[str, Any]] = []

        for sub in subs:
            stem_w = sub_stem_weight[cat].get(sub, 0.0)
            branch_w = sub_branch_weight[cat].get(sub, 0.0)
            sub_total_w = stem_w + branch_w
            if sub_total_w > 0:
                present_subs.append(sub)

            percent = round((sub_total_w / total_weight) * 100.0, 1)
            stems_percent = round((stem_w / total_weight) * 100.0, 1)
            branches_percent = round((branch_w / total_weight) * 100.0, 1)

            # 获取该子类透出的柱位列表
            stem_pillars = sub_stem_pillars.get(sub, [])
            # 转换为中文柱位名，按固定顺序：年柱→月柱→时柱
            pillar_labels = {"year": "年柱", "month": "月柱", "hour": "时柱"}
            stem_pillar_names = [pillar_labels[p] for p in ("year", "month", "hour") if p in stem_pillars]
            
            detail_items.append(
                {
                    "name": sub,
                    "percent": percent,
                    "stems_visible_count": stems_visible_count.get(sub, 0),
                    "stem_pillars": stem_pillar_names,  # 新增：透出柱位列表
                    "breakdown": {
                        "stems_percent": stems_percent,
                        "branches_percent": branches_percent,
                    },
                }
            )

        # 计算子类标签（取占比更高的子类，但混杂情况特殊处理）
        # 如果两个子类都>0，则显示混杂标签
        if len(present_subs) >= 2:
            if cat == "官杀":
                sub_label = "官杀混杂"
            elif cat == "财星":
                sub_label = "正偏财混杂"
            elif cat == "印星":
                sub_label = "正偏印混杂"
            elif cat == "食伤":
                sub_label = "食伤混杂"
            elif cat == "比劫":
                sub_label = "比劫混杂"
            else:
                sub_label = "混杂"
        else:
            # 取占比更高的子类（从 detail_items 中找）
            if present_subs:
                max_sub = None
                max_percent = -1.0
                for d in detail_items:
                    if d.get("percent", 0.0) > max_percent:
                        max_percent = d.get("percent", 0.0)
                        max_sub = d.get("name")
                sub_label = max_sub if max_sub else present_subs[0]
            else:
                sub_label = ""
        
        # 保留旧的 mix_label 用于兼容
        old_mix_label = _mix_label(cat, present_subs)
        
        # 计算 xiongshen_status（4态枚举）
        # 需要先计算：是否 split、dominant_ten_god
        xiongshen_status = "none"  # 默认值
        dominant_ten_god = None  # 主导十神
        is_split = False  # 是否命中 split 区间
        
        # 获取正/偏两个子类的占比
        subs_tuple = CATEGORY_SUBS[cat]
        zheng_shishen = subs_tuple[0]  # 正印、正财、正官、食神、比肩
        pian_shishen = subs_tuple[1]   # 偏印、偏财、七杀、伤官、劫财
        
        zheng_percent = 0.0
        pian_percent = 0.0
        for d in detail_items:
            name = d.get("name")
            pct = d.get("percent", 0.0)
            if name == zheng_shishen:
                zheng_percent = pct
            elif name == pian_shishen:
                pian_percent = pct
        
        # 计算 pian_ratio（偏占多少，仅在并存时有意义）
        pian_ratio = None
        if zheng_percent > 0.0 and pian_percent > 0.0:
            total_sub_percent = zheng_percent + pian_percent
            if total_sub_percent > 0.0:
                pian_ratio = pian_percent / total_sub_percent
                pian_ratio = round(pian_ratio + 0.0001, 1)  # 加小量避免浮点误差
                if pian_ratio > 1.0:
                    pian_ratio = 1.0
        
        # 判定顺序（严格）：先判 split，再判 dominant
        if pian_ratio is not None and 0.30 < pian_ratio <= 0.60:
            # split 区间命中
            is_split = True
            xiongshen_status = "split"
            dominant_ten_god = None  # split 时不设 dominant
        else:
            # 不是 split，确定 dominant_ten_god
            if pian_ratio is not None:
                if pian_ratio > 0.60:
                    dominant_ten_god = pian_shishen
                else:  # pian_ratio <= 0.30
                    dominant_ten_god = zheng_shishen
            elif zheng_percent > 0.0 and pian_percent == 0.0:
                # 纯正
                dominant_ten_god = zheng_shishen
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                # 纯偏
                dominant_ten_god = pian_shishen
            
            # 判定 xiongshen_status
            if dominant_ten_god and dominant_ten_god in XIONGSHEN_SET:
                # dominant 是凶神
                is_pure = (zheng_percent == 0.0 or pian_percent == 0.0)
                if is_pure:
                    xiongshen_status = "pure_xiongshen"
                else:
                    xiongshen_status = "xiongshen_majority"
            else:
                xiongshen_status = "none"
        
        # 计算得月令：月支本气归类到十神子类，若该子类属于当前大类，则"得月令"
        month_zhi = bazi["month"]["zhi"]
        month_main_gan = get_branch_main_gan(month_zhi)
        de_yueling = None
        if month_main_gan:
            month_ss = get_shishen(day_gan, month_main_gan)
            if month_ss:
                month_ss_cat = classify_shishen_category(month_ss)
                if month_ss_cat == cat:
                    # 得月令
                    if cat == "官杀" and len(present_subs) >= 2:
                        # 官杀混杂时，显示到子类级
                        de_yueling = f"{month_ss}得月令"
                    else:
                        de_yueling = "得月令"
        
        # 获取大类对应的五行：根据占比最高的子类对应的五行来确定
        cat_element = None
        if present_subs:
            # 找到占比最高的子类
            max_sub = None
            max_percent = -1.0
            for d in detail_items:
                if d.get("percent", 0.0) > max_percent:
                    max_percent = d.get("percent", 0.0)
                    max_sub = d.get("name")
            
            if max_sub:
                # 找到该子类对应的五行（从天干/地支中找）
                # 优先取权重最高的位置对应的五行（月支权重最高）
                element_weights = {}  # element -> total_weight
                
                for pillar in ("year", "month", "day", "hour"):
                    gan = bazi[pillar]["gan"]
                    zhi = bazi[pillar]["zhi"]
                    gan_key = f"{pillar}_gan"
                    zhi_key = f"{pillar}_zhi"
                    gan_weight = POSITION_WEIGHTS.get(gan_key, 0.0)
                    zhi_weight = POSITION_WEIGHTS.get(zhi_key, 0.0)
                    
                    # 检查天干
                    ss_gan = get_shishen(day_gan, gan)
                    if ss_gan == max_sub:
                        gan_element = GAN_WUXING.get(gan)
                        if gan_element and gan_weight > 0:
                            element_weights[gan_element] = element_weights.get(gan_element, 0.0) + gan_weight
                    
                    # 检查地支主气
                    main_gan = get_branch_main_gan(zhi)
                    if main_gan:
                        ss_zhi = get_shishen(day_gan, main_gan)
                        if ss_zhi == max_sub:
                            zhi_element = ZHI_WUXING.get(zhi)
                            if zhi_element and zhi_weight > 0:
                                element_weights[zhi_element] = element_weights.get(zhi_element, 0.0) + zhi_weight
                
                # 取权重最高的五行
                if element_weights:
                    cat_element = max(element_weights.items(), key=lambda x: x[1])[0]
                else:
                    # 如果还没找到，从 cat_elements 中取第一个
                    cat_element_list = sorted(list(cat_elements.get(cat, set())))
                    cat_element = cat_element_list[0] if cat_element_list else None
        else:
            # 如果没有子类，从 cat_elements 中取第一个
            cat_element_list = sorted(list(cat_elements.get(cat, set())))
            cat_element = cat_element_list[0] if cat_element_list else None
        
        # 如果还是没有找到五行，根据十神定义计算
        if not cat_element:
            cat_element = _get_category_element_by_definition(cat, day_gan)

        traits.append(
            {
                "group": _group_label(cat),
                "total_percent": total_percent,
                "mix_label": old_mix_label,  # 保留旧字段用于兼容
                "sub_label": sub_label,  # 新增：子类标签（取占比更高的）
                "detail": detail_items,
                "de_yueling": de_yueling,  # 新增：得月令信息
                "element": cat_element,  # 新增：大类对应的五行
                "xiongshen_status": xiongshen_status,  # 新增：凶神状态（4态枚举）
                "dominant_ten_god": dominant_ten_god,  # 新增：主导十神（split 时为 None）
            }
        )

    # 按 total_percent 降序排序，便于展示
    traits.sort(key=lambda t: t.get("total_percent", 0.0), reverse=True)
    return traits


