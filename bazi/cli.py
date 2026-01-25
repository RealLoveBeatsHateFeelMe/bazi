# -*- coding: utf-8 -*-
"""命令行交互：输入生日 → 八字 + 日主 + 用神 + 大运/流年好运 + 冲的信息。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .compute_facts import compute_facts
from .config import ZHI_WUXING


# ============================================================
# 印星天赋卡（新版：只有性格画像 + 提高方向，仅主要性格使用）
# ============================================================

# 正印（新版2行）
_ZHENGYIN_CARD_V2 = [
    "- 性格画像：善良仁慈，守规矩、讲原则，给人可靠、有信用、值得信任的感觉；更偏主流与体系化的路子。",
    "- 提高方向：不要过分墨守成规，不要过分善良，太容易相信别人，与人相处注意边界感。",
]

# 偏印（新版2行）
_PIANYIN_CARD_V2 = [
    "- 性格画像：偏独处，容易被小众非主流吸引；对他人情绪与状态变化更敏感；在自己真正喜欢的领域，往往有独特的天分与研究劲。",
    "- 提高方向：多做事、少空想；先做后看，用行动校准；在不确定中保持坚定信念与节奏感。",
]

# 正偏印混杂（新版2行）
_YINXING_BLEND_CARD_V2 = [
    "- 性格画像：心思缜密、学习能力强，既守规矩也爱探索；对小众事物兴趣强，做事看意义驱动，脑子里常在「求稳」和「理想乌托邦」之间摇摆。",
    "- 提高方向：多做事、少空想，用行动校准，不要过分善良，与人相处注意边界感。",
]

# ============================================================
# 印星快速汇总文案（新版：只用性格画像，不区分思维/社交）
# ============================================================
_YINXING_QUICK_SUMMARY_V2 = {
    "正印": "善良仁慈，守规矩、讲原则，给人可靠、有信用、值得信任的感觉；更偏主流与体系化的路子。",
    "偏印": "偏独处，容易被小众非主流吸引；对他人情绪与状态变化更敏感；在自己真正喜欢的领域，往往有独特的天分与研究劲。",
    "正偏印": "心思缜密、学习能力强，既守规矩也爱探索；对小众事物兴趣强，做事看意义驱动，脑子里常在「求稳」和「理想乌托邦」之间摇摆。",
}

# ============================================================
# 财星天赋卡（新版：只有性格画像 + 提高方向，仅主要性格使用）
# ============================================================

# 正财（新版2行）
_ZHENGCAI_CARD_V2 = [
    "- 性格画像：务实、稳健，勤俭节约，讲信用，工作能力强，做事踏实肯干、一步一步把结果做出来。更喜欢稳定、可预期的收入来源，愿意靠持续投入换长期的确定回报。",
    "- 提高方向：在稳的基础上保留弹性；适当允许享受与试错，不要因为过度谨慎错过窗口，同时别把压力全揽在自己身上。",
]

# 偏财（新版2行）
_PIANCAI_CARD_V2 = [
    "- 性格画像：行动力强，有想法往往会立刻付诸行动。社交能力强，出手阔绰，浪漫。更容易对钱、资源、机会、交易这些现实结果上心，也更吃「新鲜感」和反馈。",
    "- 提高方向：防止花钱大手大脚，注意欲望与比较心，防止欲望太多而不知足。",
]

# 正偏财混杂（新版2行）
_CAIXING_BLEND_CARD_V2 = [
    "- 性格画像：对钱、资源、机会、交易这些现实结果上心。容易同时保持两份工作，或在主要工作之外有其他的收入。工作能力，社交能力强。既能踏实做事，也擅长跑合作，开辟新的机会和渠道。",
    "- 提高方向：防止欲望太多而不知足，注意不同工作之间的精力调配。",
]

# ============================================================
# 财星快速汇总文案（新版：只用性格汇总，不区分思维/社交）
# ============================================================
_CAIXING_QUICK_SUMMARY_V2 = {
    "正财": "务实、稳健，勤俭节约，工作能力强；喜欢稳定、可预期的收入来源，愿意靠持续投入换长期的确定回报。",
    "偏财": "行动力强、社交能力强；对钱、资源、机会、交易这些现实结果上心，有想法往往会立刻付诸行动。",
    "正偏财": "务实，工作能力强、社交能力强；对钱、资源、机会、交易这些现实结果上心，容易同时保持两份工作。",
}

# ============================================================
# 财星天赋卡（旧版5档，保留供其他地方使用）
# ============================================================

# 财星共性（所有档位都打印）
_CAIXING_COMMON = "- 财星共性：重现实回报与资源分配，重价值交换与结果；对「钱、成本、性价比、生活质感」更敏感，也更在意体面与边界。"

# 正财主卡 5 栏
_ZHENGCAI_CARD = [
    "- 思维天赋：务实、稳健，适合长期积累的财富；更偏向「确定性与可持续」的路径，做事踏实肯干、一步一步把结果做出来。",
    "- 社交天赋：偏可靠、讲信用、守边界；不靠花哨取胜，更擅长用稳定兑现与责任感建立信任，给人踏实感。",
    "- 兴趣取向：更偏向稳定收益与看得见的成果（资产、技能、家庭责任、长期建设）；对规则与成本意识更强。",
    "- 生活方式：勤俭节约，重预算与秩序感；日常更踏实肯干，愿意靠持续投入换稳定回报，但容易把自己绷得太紧。",
    "- 提高方向：在稳的基础上保留弹性；适当允许享受与试错，不要因为过度谨慎错过窗口，同时别把压力全揽在自己身上。",
]

# 偏财主卡 5 栏
_PIANCAI_CARD = [
    "- 思维天赋：对机会、资源、交换关系很敏感，反应快、会算「值不值」；行动力强，有想法往往会立刻付诸行动，擅长在变化里抓窗口与优先级。",
    "- 社交天赋：社交面更广，氛围感强，会表达、浪漫、大方；更擅长用互动与体面把关系推顺，让人感觉被照顾到。",
    "- 兴趣取向：更容易对「钱、资源、交易、市场、人情世故、好东西」上心；对新鲜事物与现实结果反馈更敏感。",
    "- 生活方式：更愿意把生活过得有质感、有效率，出手相对爽快；欲望与比较心一旦失控，容易变成「越想要越焦虑」，现实压力随之放大。",
    "- 提高方向：把大方与热情放在「值得的人和事」上；注意开销与预算边界，先定原则与节奏，再谈投入与回报，避免被外界节奏牵着走。",
]

# 融合版 5 栏（正偏各半）
_CAI_BLEND_CARD = [
    "- 思维天赋：既会算长期账、能稳步积累，也能抓机会窗口、快速行动；「稳的规划」和「快的试错」并存。",
    "- 社交天赋：既讲信用与边界，也有氛围感与表达力；能靠可靠赢信任，也能靠体面与互动推动关系。",
    "- 兴趣取向：一边在意稳定与可持续，一边对市场、交易与新机会敏感；既要「长期价值」，也要「当下反馈」。",
    "- 生活方式：既想把钱花出质感与效率，也需要预算与秩序感来托底；容易在「享受投入」和「控制开销」之间拉扯；必有两份工作/兼职的状态。",
    "- 提高方向：先定预算与底线，再留一部分弹性用于体验与机会；用规则管住欲望，用行动抓住窗口。",
]

# 补充句（仅正财主导时追加）
_PIANCAI_SUPPLEMENT = "- 偏财补充：同时带一点机会嗅觉与社交氛围感，出手更爽快、也更讲体面。"

# ============================================================
# 比劫天赋卡（比肩/劫财共用同一张卡）
# ============================================================

# 比劫新版2行（比肩/劫财完全相同，只有性格画像+提高方向）
_BIJIE_CARD_V2 = [
    "- 性格画像：主见强、反应快，对自己认定的事意志非常坚定；遇事更倾向自己拍板，自我立场优先。讨厌被安排和管制，喜欢自由，不爱被人指挥。",
    "- 提高方向：不要太自我、不要太固执，学会听劝，控制情绪，先冷静后决定。",
]

# 比劫快速汇总文案（新版：只用性格汇总，不区分思维/社交）
_BIJIE_QUICK_SUMMARY_V2 = "主见强、反应快，喜欢自己做主；讨厌被安排和管制，偏爱自由。"

# ============================================================
# 官杀天赋卡（正官/七杀/官杀混杂）- 新版2行
# ============================================================

# 正官（新版2行）
_ZHENGGUAN_CARD_V2 = [
    "- 性格画像：稳重、有条理，领导能力强，守信用，靠谱有底线。更习惯按规矩和流程做事；对「有没有越界、有没有踩线」比较敏感。更喜欢有标准、有评判体系的环境；更认可主流路径与权威规则，重秩序与节奏，做事偏稳。",
    "- 提高方向：在守规矩的同时允许灵活调整，不被主流、社会眼光过分裹挟。",
]

# 七杀（新版2行）
_QISHA_CARD_V2 = [
    "- 性格画像：反应快、决断力强，遇事能快速做决定并承担后果；抗压能力强，行动导向明显，更习惯用结果说话。自我管控能力强，目标感很强，不达目标不轻易停下。强调效率，精神容易紧绷，但也更能扛住压力。",
    "- 提高方向：学会用合适的方式缓解压力，控制脾气。",
]

# 官杀混杂（新版2行）
_GUANSHA_BLEND_CARD_V2 = [
    "- 性格画像：自我管控能力强，领导能力强，目标感很强，不达目标不轻易停下。遇事更敢做决定，也更敢承担后果，强调效率。",
    "- 提高方向：精神容易紧绷，适当学会放松，控制脾气；允许犯错与调整，一次失误不代表全盘失败。",
]

# ============================================================
# 官杀快速汇总文案（新版：只用性格汇总，不区分思维/社交）
# ============================================================
_GUANSHA_QUICK_SUMMARY_V2 = {
    "正官": "稳重、有条理，领导能力强；守信用、有底线，重规矩与秩序，做事偏稳。",
    "七杀": "领导能力强，反应快、决断强；抗压行动导向，目标感强，重效率与结果。",
    "正官七杀": "自我管控和领导力强，目标感很强；敢决策敢担责，强调效率。",
}

# ============================================================
# 食伤天赋卡（食神/伤官 + 食伤混杂）- 新版2段
# ============================================================

# 食神（新版2段）
_SHISHEN_CARD_V2 = [
    "- 性格画像：亲和、好相处，口才表达好，习惯用温和的方式表达，不爱冲突也不爱争论，临场表现、发挥好。遇到压力时不太容易被压垮，更容易保持状态。更偏享受当下，喜欢轻松舒服的生活，不喜欢把自己逼太紧。容易满足，但也容易懒散。",
    "- 提高方向：在生活中定一个具体的目标，学习一份具体的技能，少沉浸在文艺幻想里。",
]

# 伤官（新版2段）
_SHANGGUAN_CARD_V2 = [
    "- 性格画像：创意强、表达欲旺，口才好，临场表现能力强。遇到压力时不太容易被压垮，更容易保持状态。喜欢打破常规、追求与众不同；习惯质疑权威与既有规则。不服管、不服输，强调自我表达与存在感。",
    "- 提高方向：把锋芒转化成作品；学会在表达观点时兼顾对方感受，把「叛逆」变成「创造」。",
]

# 食伤混杂（新版2段）
_SHISHANG_BLEND_CARD_V2 = [
    "- 性格画像：亲和好相处，也个性鲜明、敢说敢表达，口才非常好。临场表现能力强，追求轻松愉快，也追求现实成功。遇到压力时不太容易被压垮，更容易保持状态。",
    "- 提高方向：在生活中定一个具体的目标，学习一份具体的技能，不要三分钟热度。",
]

# ============================================================
# 食伤快速汇总文案（新版：只用性格汇总，不区分思维/社交）
# ============================================================
_SHISHANG_QUICK_SUMMARY_V2 = {
    "食神": "亲和好相处，表达温和，口才好、临场发挥强；更偏享受当下，喜欢轻松舒服的节奏。",
    "伤官": "创意强、表达欲旺，口才好、临场表现强；敢质疑规则，追求与众不同，重自我表达。",
    "食神伤官": "又亲和好相处、又敢说敢表达，口才强、临场稳；既追求轻松愉快，也追求现实成功。",
}

# ============================================================
# 食伤天赋卡（旧版5栏，保留供其他地方使用）
# ============================================================

# 食伤共性（所有档位都打印）
_SHISHANG_COMMON = "- 食伤共性：重表达与呈现，喜欢让想法落地成型；对「好不好玩、有没有意思、能不能展示」更敏感，也更在意生活的趣味与质感。"

# 食神主卡 5 栏
_SHISHEN_CARD = [
    "- 思维天赋：轻松自然、注重感受，擅长把事情做得舒服、让过程愉快；对「享受当下」有天然敏感度，做事不太喜欢逼太紧。",
    "- 社交天赋：亲和、好相处，给人放松、没压力的感觉；习惯用温和的方式表达，不爱冲突也不爱争论。",
    "- 兴趣取向：偏好轻松愉快、感官友好的领域；对美食、休闲、娱乐、生活美学容易有兴趣，讨厌紧绷和苦行。",
    "- 生活方式：重舒适与节奏感，追求「过得好」多于「跑得快」；容易满足但也容易懒散，需要外力推一把。",
    "- 提高方向：在舒适区之外找一点挑战；保持享受生活的能力的同时，不让「舒服」变成「不想动」。",
]

# 伤官主卡 5 栏
_SHANGGUAN_CARD = [
    "- 思维天赋：创意强、表达欲旺，喜欢打破常规、追求与众不同；习惯质疑权威与既有规则，对「有没有新意」特别敏感。",
    "- 社交天赋：个性鲜明、锋芒外露，给人「有想法、有态度」的印象；敢说敢表达，但容易因直言惹争议。",
    "- 兴趣取向：偏好创意型、表现型、颠覆型的领域；对艺术、写作、技术创新容易有兴趣，讨厌循规蹈矩和无趣。",
    "- 生活方式：强调自我表达与存在感，讨厌被压制或被同质化；容易不服管、不服输，情绪起伏也更明显。",
    "- 提高方向：把锋芒转化成作品；学会在表达观点时兼顾对方感受，把「叛逆」变成「创造」。",
]

# 融合版 5 栏（食神伤官各半）
_SHISHANG_BLEND_CARD = [
    "- 思维天赋：既追求轻松愉快，也追求创意表达；「舒服」和「出彩」两种做事风格并存，随场景切换。",
    "- 社交天赋：既亲和好相处，也个性鲜明、敢说敢表达；能用温和方式建立关系，也能用态度赢得关注。",
    "- 兴趣取向：一边喜欢轻松休闲、感官享受，一边对创意与表现有追求；既要「好玩」，也要「有意思」。",
    "- 生活方式：既重舒适与节奏，也强调自我表达；容易在「享受当下」和「想要更多」之间来回。",
    "- 提高方向：用舒适托住表达；在保持生活趣味的同时，把创意落地成可被看见的成果。",
]

# 各半提醒句（食伤各半时追加）
_SHISHANG_BLEND_REMINDER = "- 食伤各半提醒：两种能量都想要出口——享受的时候想表达，表达完又想放松；重点是找到一个「既舒服又能展示」的节奏。"

# 补充句（仅食神主导时追加）
_SHANGGUAN_SUPPLEMENT = "- 伤官补充：同时带一点表达欲与锋芒，在舒服之余也想「亮一下」，偶尔会有点小叛逆。"
# 补充句（仅伤官主导时追加）
_SHISHEN_SUPPLEMENT = "- 食神补充：同时带一点轻松与柔和的底色，锋芒之外也懂得享受生活，不会一直绷着。"


def _get_bijie_talent_card() -> List[str]:
    """返回比劫天赋卡行列表（新版：标题行+性格画像+提高方向，比肩/劫财共用）。"""
    lines = ["比劫："]
    lines.extend(_BIJIE_CARD_V2)
    lines.append("")  # 空行，方便阅读
    return lines


def _get_caixing_talent_card(is_pure: bool, pure_shishen: Optional[str], pian_ratio: Optional[float]) -> List[str]:
    """根据财星档位返回对应的天赋卡行列表（新版：标题行+性格画像+提高方向）。

    新版规则（不再区分5档，简化为3种情况）：
    - 纯正财 / 正财主导（pian_ratio <= 0.30）：正财卡
    - 纯偏财 / 偏财主导（pian_ratio > 0.60）：偏财卡
    - 正偏财混杂（0.30 < pian_ratio <= 0.60）：混杂卡

    输出格式：
    - 标题行（十神名字 + 冒号）
    - 性格画像
    - 提高方向
    """
    lines = []

    if is_pure:
        if pure_shishen == "正财":
            lines.append("正财：")
            lines.extend(_ZHENGCAI_CARD_V2)
        else:
            lines.append("偏财：")
            lines.extend(_PIANCAI_CARD_V2)
    elif pian_ratio is not None:
        if pian_ratio <= 0.30:
            # 正财主导：用正财卡
            lines.append("正财：")
            lines.extend(_ZHENGCAI_CARD_V2)
        elif pian_ratio <= 0.60:
            # 正偏财混杂：用混杂卡
            lines.append("正偏财混杂：")
            lines.extend(_CAIXING_BLEND_CARD_V2)
        else:
            # 偏财主导：用偏财卡
            lines.append("偏财：")
            lines.extend(_PIANCAI_CARD_V2)

    if lines:
        lines.append("")  # 空行，方便阅读
    return lines


def _get_yinxing_talent_card(is_pure: bool, pure_shishen: Optional[str], pian_ratio: Optional[float]) -> List[str]:
    """根据印星档位返回对应的天赋卡行列表（新版：标题行+性格画像+提高方向）。

    新版规则（不再区分5档，简化为3种情况）：
    - 纯正印 / 正印主导（pian_ratio <= 0.30）：正印卡
    - 纯偏印 / 偏印主导（pian_ratio > 0.60）：偏印卡
    - 正偏印混杂（0.30 < pian_ratio <= 0.60）：混杂卡

    输出格式：
    - 标题行（十神名字 + 冒号）
    - 性格画像
    - 提高方向
    """
    lines = []

    if is_pure:
        if pure_shishen == "正印":
            lines.append("正印：")
            lines.extend(_ZHENGYIN_CARD_V2)
        else:
            lines.append("偏印：")
            lines.extend(_PIANYIN_CARD_V2)
    elif pian_ratio is not None:
        if pian_ratio <= 0.30:
            # 正印主导：用正印卡
            lines.append("正印：")
            lines.extend(_ZHENGYIN_CARD_V2)
        elif pian_ratio <= 0.60:
            # 正偏印混杂：用混杂卡
            lines.append("正偏印混杂：")
            lines.extend(_YINXING_BLEND_CARD_V2)
        else:
            # 偏印主导：用偏印卡
            lines.append("偏印：")
            lines.extend(_PIANYIN_CARD_V2)

    if lines:
        lines.append("")  # 空行，方便阅读
    return lines


def _get_guansha_talent_card(is_pure: bool, pure_shishen: Optional[str], pian_ratio: Optional[float]) -> List[str]:
    """根据官杀档位返回对应的天赋卡行列表（新版：标题行+性格画像+提高方向）。

    新版规则（简化为3种情况）：
    - 纯正官 / 正官主导（pian_ratio <= 0.30）：正官卡
    - 纯七杀 / 七杀主导（pian_ratio > 0.60）：七杀卡
    - 官杀混杂（0.30 < pian_ratio <= 0.60）：混杂卡
    """
    lines = []

    if is_pure:
        if pure_shishen == "正官":
            lines.append("正官：")
            lines.extend(_ZHENGGUAN_CARD_V2)
        else:
            lines.append("七杀：")
            lines.extend(_QISHA_CARD_V2)
    elif pian_ratio is not None:
        if pian_ratio <= 0.30:
            lines.append("正官：")
            lines.extend(_ZHENGGUAN_CARD_V2)
        elif pian_ratio <= 0.60:
            lines.append("官杀混杂：")
            lines.extend(_GUANSHA_BLEND_CARD_V2)
        else:
            lines.append("七杀：")
            lines.extend(_QISHA_CARD_V2)

    if lines:
        lines.append("")  # 空行，方便阅读
    return lines


def _get_shishang_talent_card(is_pure: bool, pure_shishen: Optional[str], pian_ratio: Optional[float]) -> List[str]:
    """根据食伤档位返回对应的天赋卡行列表（新版：标题行+性格画像+提高方向）。

    3 档规则（注：食伤组中食神="正"，伤官="偏"）：
    - 纯食神/食神主导（pian_ratio ≤ 0.30 或 伤官%=0）：食神 2 段卡
    - 食伤混杂（0.30 < pian_ratio ≤ 0.60）：混杂 2 段卡
    - 纯伤官/伤官主导（pian_ratio > 0.60 或 食神%=0）：伤官 2 段卡
    """
    lines = []

    if is_pure:
        if pure_shishen == "食神":
            lines.append("食神：")
            lines.extend(_SHISHEN_CARD_V2)
        else:
            lines.append("伤官：")
            lines.extend(_SHANGGUAN_CARD_V2)
    elif pian_ratio is not None:
        if pian_ratio <= 0.30:
            lines.append("食神：")
            lines.extend(_SHISHEN_CARD_V2)
        elif pian_ratio <= 0.60:
            lines.append("食伤混杂：")
            lines.extend(_SHISHANG_BLEND_CARD_V2)
        else:
            lines.append("伤官：")
            lines.extend(_SHANGGUAN_CARD_V2)

    if lines:
        lines.append("")  # 空行，方便阅读
    return lines


def _generate_marriage_suggestion(yongshen_elements: list[str]) -> str:
    """根据用神五行生成婚配倾向。

    参数:
        yongshen_elements: 用神五行列表，例如 ["木", "火"]

    返回:
        婚配倾向字符串，例如 "【婚配倾向】更容易匹配：虎兔蛇马；或 木，火旺的人。"
    """
    if not yongshen_elements:
        return ""
    
    # 地支到生肖的映射
    zhi_to_zodiac = {
        "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
        "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
        "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
    }
    
    # 五行到地支的映射（只用主五行）
    element_to_zhi = {
        "水": ["亥", "子"],
        "金": ["申", "酉"],
        "木": ["寅", "卯"],
        "火": ["巳", "午"],
        "土": ["辰", "戌", "丑", "未"],
    }
    
    # 收集每个五行对应的生肖
    zodiac_blocks = {
        "水": [],  # 猪鼠
        "金": [],  # 猴鸡
        "木": [],  # 虎兔
        "火": [],  # 蛇马
        "土": [],  # 龙狗牛羊
    }
    
    for elem in yongshen_elements:
        if elem in element_to_zhi:
            for zhi in element_to_zhi[elem]:
                zodiac = zhi_to_zodiac.get(zhi, "")
                if zodiac and zodiac not in zodiac_blocks[elem]:
                    zodiac_blocks[elem].append(zodiac)
    
    # 按顺序拼接生肖块
    result_parts = []
    
    # 1. 先拼 水块(猪鼠) + 金块(猴鸡)
    if zodiac_blocks["水"]:
        result_parts.extend(zodiac_blocks["水"])
    if zodiac_blocks["金"]:
        result_parts.extend(zodiac_blocks["金"])
    
    # 2. 再拼 木块(虎兔) + 火块(蛇马)
    if zodiac_blocks["木"]:
        result_parts.extend(zodiac_blocks["木"])
    if zodiac_blocks["火"]:
        result_parts.extend(zodiac_blocks["火"])
    
    # 3. 最后拼 土块(龙狗牛羊)
    if zodiac_blocks["土"]:
        result_parts.extend(zodiac_blocks["土"])
    
    # 构建推荐生肖串
    zodiac_str = "".join(result_parts) if result_parts else ""
    
    # 构建"旺的人"文案：按候选五行顺序，用中文顿号分隔
    wang_str = "，".join(yongshen_elements)
    
    if zodiac_str:
        return f"【婚配倾向】更容易匹配：{zodiac_str}；或 {wang_str}旺的人。"
    else:
        return f"【婚配倾向】更容易匹配：{wang_str}旺的人。"


def _calc_half_year_label(risk: float, is_yongshen: bool) -> str:
    """计算半年判词。
    
    参数:
        risk: 半年危险系数（H1 或 H2）
        is_yongshen: 是否是用神
    
    返回:
        判词：好运、一般、有轻微变动、凶（棘手/意外）
    """
    if risk <= 10.0:
        return "好运" if is_yongshen else "一般"
    elif risk < 20.0:
        return "有轻微变动"
    else:  # risk >= 20.0
        return "凶（棘手/意外）"


def _calc_year_title_line(
    total_risk: float,
    risk_from_gan: float,
    risk_from_zhi: float,
    is_gan_yongshen: bool,
    is_zhi_yongshen: bool,
) -> tuple[str, bool]:
    """计算年度标题行。

    参数:
        total_risk: 总危险系数 Y
        risk_from_gan: 开始危险系数 H1（原"上半年"）
        risk_from_zhi: 后来危险系数 H2（原"下半年"）
        is_gan_yongshen: 天干是否用神
        is_zhi_yongshen: 地支是否用神

    返回:
        (title_line, should_print_suggestion)
        title_line: 年度标题行文本
        should_print_suggestion: 是否打印建议行（Y >= 40）
    """
    Y = total_risk

    # A) 若 Y >= 40：全年 凶（棘手/意外）
    if Y >= 40.0:
        return ("全年 凶（棘手/意外）", True)

    # B) 若 25 <= Y < 40：全年 明显变动（可克服）
    if Y >= 25.0:
        return ("全年 明显变动（可克服）", False)

    # C) 若 Y < 25：才允许输出开始/后来
    H1 = risk_from_gan
    H2 = risk_from_zhi

    S1 = _calc_half_year_label(H1, is_gan_yongshen)
    S2 = _calc_half_year_label(H2, is_zhi_yongshen)

    return (f"开始 {S1}，后来 {S2}", False)


def _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev: dict) -> None:
    """打印三合/三会逢冲额外加分信息。
    
    打印顺序：
    1. 哪个字属于哪个三合/三会、哪个是单独字
    2. 单独字是不是用神（如果有单独字）
    3. 本规则本年额外加分是多少（+15 或 +35），并声明本年封顶已用掉
    """
    bonus_percent = sanhe_sanhui_bonus_ev.get("risk_percent", 0.0)
    if bonus_percent <= 0.0:
        return
    
    flow_branch = sanhe_sanhui_bonus_ev.get("flow_branch", "")
    target_branch = sanhe_sanhui_bonus_ev.get("target_branch", "")
    group_type = sanhe_sanhui_bonus_ev.get("group_type", "")  # "sanhe" or "sanhui"
    group_name = sanhe_sanhui_bonus_ev.get("group_name", "")  # 例如"火局"、"木会"
    group_members = sanhe_sanhui_bonus_ev.get("group_members", [])  # 三合/三会的三个成员字
    flow_in_group = sanhe_sanhui_bonus_ev.get("flow_in_group", False)
    target_in_group = sanhe_sanhui_bonus_ev.get("target_in_group", False)
    standalone_zhi = sanhe_sanhui_bonus_ev.get("standalone_zhi")
    standalone_is_yongshen = sanhe_sanhui_bonus_ev.get("standalone_is_yongshen")
    
    # 构建三合/三会名称（例如"寅午戌三合火局"或"巳午未三会火会"）
    group_members_str = "".join(group_members)
    if group_type == "sanhe":
        group_full_name = f"{group_members_str}三合{group_name}"
    else:  # sanhui
        group_full_name = f"{group_members_str}三会{group_name}"
    
    # 打印：哪个字属于哪个三合/三会、哪个是单独字
    if flow_in_group and target_in_group:
        # 两个字都属于局/会
        print(f"          {group_full_name}被冲到：冲对中'{flow_branch}'和'{target_branch}'都属于{group_full_name}")
    elif flow_in_group:
        # flow_branch属于局/会，target_branch是单独字
        print(f"          {group_full_name}被冲到：冲对中'{flow_branch}'属于{group_full_name}；'{target_branch}'是单独字")
    else:  # target_in_group
        # target_branch属于局/会，flow_branch是单独字
        print(f"          {group_full_name}被冲到：冲对中'{target_branch}'属于{group_full_name}；'{flow_branch}'是单独字")
    
    # 打印：单独字是不是用神（如果有单独字）
    if standalone_zhi:
        yongshen_status = "是用神" if standalone_is_yongshen else "不是用神"
        print(f"          单独字{standalone_zhi}：{yongshen_status}")
    
    # 打印：本规则本年额外加分是多少（+15 或 +35），并声明本年封顶已用掉
    print(f"          三合/三会逢冲额外：+{bonus_percent:.0f}%（本年只加一次）")


# ============================================================
# 模式提示文案（伤官见官 / 枭神夺食）
# ============================================================
_HURT_OFFICER_HINT = "主特征｜外部对抗：更容易出现来自外部的人/权威/规则的正面冲突与摩擦。表现形式（仅类别）：口舌是非/名声受损；合同/合规/官非；意外与身体伤害；（女性）伴侣关系不佳或伴侣受伤。"
_PIANYIN_EATGOD_HINT = "主特征｜突发意外：更容易出现突如其来的变故与波折，打乱节奏。表现形式（仅类别）：判断失误/信息偏差→麻烦与灾祸；钱财损失；犯小人/被拖累；意外的身体伤害风险上升。"

# ============================================================
# 天克地冲提示文案
# ============================================================
_TKDC_HINT = "可能出现意外、生活环境剧变，少数情况下牵动亲缘离别。"

# 时柱天克地冲专用提示（搬家/换工作）
_HOUR_TKDC_HINT = "可能搬家/换工作。"

# ============================================================
# 时支被流年冲提示文案
# ============================================================
_HOUR_CLASH_HINT = "可能搬家/换工作。"


def _format_position_string(pos: dict) -> str:
    """把位置信息格式化为可读字符串。

    参数:
        pos: 位置字典，包含 source, pillar, kind, char 等字段

    返回:
        格式化的位置字符串，如 "天干甲"、"月支巳"、"流年亥"
    """
    kind = pos.get("kind", "")
    char = pos.get("char", "")
    pillar = pos.get("pillar", "")
    source = pos.get("source", "")

    if kind == "gan":
        # 天干
        return f"天干{char}"
    else:
        # 地支：需要标注是哪个支位
        if source == "liunian" or pillar == "liunian":
            return f"流年{char}"
        elif source == "dayun" or pillar == "dayun":
            return f"大运{char}"
        else:
            # 命局地支
            pillar_map = {"year": "年支", "month": "月支", "day": "日支", "hour": "时支"}
            pillar_label = pillar_map.get(pillar, pillar)
            return f"{pillar_label}{char}"


def _collect_pattern_evidences(all_events: list, static_events: list, clashes_natal: list) -> dict:
    """收集某年份的所有模式 evidence（包括动态模式、静态模式激活、与冲重叠的模式）。

    返回:
        {
            "hurt_officer": [evidence1, evidence2, ...],
            "pianyin_eatgod": [evidence1, evidence2, ...],
        }
        每个 evidence 是一个包含位置信息的字典
    """
    result = {"hurt_officer": [], "pianyin_eatgod": []}

    # 1. 收集动态模式事件
    for ev in all_events:
        if ev.get("type") == "pattern":
            pattern_type = ev.get("pattern_type", "")
            if pattern_type in result:
                pos1 = ev.get("pos1", {})
                pos2 = ev.get("pos2", {})
                result[pattern_type].append({
                    "type": "dynamic",
                    "kind": ev.get("kind", ""),
                    "positions": [pos1, pos2],
                })

    # 2. 收集静态模式激活事件
    for ev in static_events:
        if ev.get("type") == "pattern_static_activation":
            pattern_type = ev.get("pattern_type", "")
            if pattern_type in result:
                # 静态模式激活可能有多个 pairs
                for pairs_key in ["activated_natal_gan_pairs", "activated_dayun_gan_pairs",
                                  "activated_natal_zhi_pairs", "activated_dayun_zhi_pairs"]:
                    for pair in ev.get(pairs_key, []):
                        pos1 = pair.get("pos1", {})
                        pos2 = pair.get("pos2", {})
                        result[pattern_type].append({
                            "type": "static_activation",
                            "kind": "gan" if "gan" in pairs_key else "zhi",
                            "positions": [pos1, pos2],
                        })

    # 3. 收集与冲重叠的模式（从 clashes_natal 中读取 is_pattern_overlap）
    for clash in clashes_natal:
        if clash and clash.get("is_pattern_overlap"):
            pattern_type = clash.get("overlap_pattern_type", "")
            if pattern_type in result:
                # 与冲重叠的模式，位置是冲的两个地支
                flow_branch = clash.get("flow_branch", "")
                target_branch = clash.get("target_branch", "")
                # 获取被冲的目标柱位
                targets = clash.get("targets", [])
                for target in targets:
                    target_pillar = target.get("pillar", "")
                    result[pattern_type].append({
                        "type": "clash_overlap",
                        "kind": "zhi",
                        "positions": [
                            {"kind": "zhi", "char": flow_branch, "source": "liunian", "pillar": "liunian"},
                            {"kind": "zhi", "char": target_branch, "source": "natal", "pillar": target_pillar},
                        ],
                    })

    return result


def _generate_pattern_hints(all_events: list, static_events: list, clashes_natal: list) -> list:
    """生成模式提示行（伤官见官、枭神夺食）。

    返回提示行列表，每行格式：
    - 多次：引发多次伤官见官：{文案}
    - 单次：（{位置串}）引动伤官见官：{文案}
    """
    hints = []
    evidences = _collect_pattern_evidences(all_events, static_events, clashes_natal)

    # 按固定顺序处理：先伤官见官，后枭神夺食
    for pattern_type, hint_text in [("hurt_officer", _HURT_OFFICER_HINT),
                                     ("pianyin_eatgod", _PIANYIN_EATGOD_HINT)]:
        pattern_evidences = evidences.get(pattern_type, [])
        if not pattern_evidences:
            continue

        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食"

        if len(pattern_evidences) > 1:
            # 多次：不列位置
            hints.append(f"引发多次{pattern_name}：{hint_text}")
        else:
            # 单次：列出位置
            evidence = pattern_evidences[0]
            positions = evidence.get("positions", [])
            pos_strs = []
            for pos in positions:
                if pos:
                    pos_strs.append(_format_position_string(pos))
            pos_str = "/".join(pos_strs) if pos_strs else ""
            if pos_str:
                hints.append(f"（{pos_str}）引动{pattern_name}：{hint_text}")
            else:
                hints.append(f"引动{pattern_name}：{hint_text}")

    return hints


def _check_hour_clash_by_liunian(bazi: dict, liunian_zhi: str) -> tuple:
    """检查流年地支是否冲时支。

    参数:
        bazi: 八字命局
        liunian_zhi: 流年地支

    返回:
        (是否冲时支, 时支字符) 或 (False, None)
    """
    from .config import ZHI_CHONG

    hour_zhi = bazi.get("hour", {}).get("zhi", "")
    if not hour_zhi or not liunian_zhi:
        return False, None

    # 检查是否构成六冲
    clash_target = ZHI_CHONG.get(liunian_zhi)
    if clash_target == hour_zhi:
        return True, hour_zhi

    return False, None


def _generate_hour_clash_hint(bazi: dict, liunian_zhi: str) -> str:
    """生成时支被流年冲的提示行。

    返回:
        提示行字符串，或空字符串（如果不冲）
    """
    is_clash, hour_zhi = _check_hour_clash_by_liunian(bazi, liunian_zhi)
    if not is_clash:
        return ""

    return f"（时支{hour_zhi}/流年{liunian_zhi}）时支被流年冲：{_HOUR_CLASH_HINT}"


def _collect_tkdc_evidences(clashes_natal: list, clashes_dayun: list, static_events: list) -> dict:
    """收集某年份的所有天克地冲 evidence，分类为普通和时柱。

    参数:
        clashes_natal: 流年与命局的冲事件列表
        clashes_dayun: 流年与大运的冲事件列表（含运年天克地冲）
        static_events: 静态事件列表（含静态天克地冲激活）

    返回:
        {
            "general": [...],      # 普通天克地冲（排除年柱、时柱）
            "hour_tkdc": [...],    # 时柱天克地冲
        }
    """
    general_evidences = []
    hour_tkdc_evidences = []

    # 1. 流年与命局的天克地冲
    for clash in clashes_natal or []:
        if not clash:
            continue
        tkdc_targets = clash.get("tkdc_targets", [])
        if tkdc_targets:
            flow_gan = clash.get("flow_gan", "")
            flow_branch = clash.get("flow_branch", "")
            for target in tkdc_targets:
                target_pillar = target.get("pillar", "")
                target_gan = target.get("gan", "")
                target_zhi = clash.get("target_branch", "")

                evidence = {
                    "type": "liunian_natal_tkdc",
                    "pillar": target_pillar,
                    "positions": [
                        {"kind": "ganzhi", "gan": flow_gan, "zhi": flow_branch, "source": "liunian"},
                        {"kind": "ganzhi", "gan": target_gan, "zhi": target_zhi, "source": "natal", "pillar": target_pillar},
                    ],
                }

                # 按柱位分类
                if target_pillar == "hour":
                    # 时柱天克地冲
                    hour_tkdc_evidences.append(evidence)
                elif target_pillar == "year":
                    # 年柱天克地冲：完全不算，跳过
                    pass
                else:
                    # 月柱/日柱：普通天克地冲
                    general_evidences.append(evidence)

    # 2. 运年天克地冲（大运与流年）- 归入普通天克地冲
    for clash in clashes_dayun or []:
        if not clash:
            continue
        if clash.get("is_tian_ke_di_chong", False):
            dayun_gan = clash.get("dayun_gan", "")
            dayun_branch = clash.get("dayun_branch", "")
            liunian_gan = clash.get("liunian_gan", "")
            liunian_branch = clash.get("liunian_branch", "")
            general_evidences.append({
                "type": "dayun_liunian_tkdc",
                "pillar": None,  # 运年没有柱位
                "positions": [
                    {"kind": "ganzhi", "gan": dayun_gan, "zhi": dayun_branch, "source": "dayun"},
                    {"kind": "ganzhi", "gan": liunian_gan, "zhi": liunian_branch, "source": "liunian"},
                ],
            })

    # 3. 静态天克地冲激活 - 归入普通天克地冲
    for ev in static_events or []:
        if ev.get("type") == "static_tkdc_activation":
            # 静态天克地冲激活，位置信息可能在事件中
            general_evidences.append({
                "type": "static_tkdc_activation",
                "pillar": None,
                "positions": [],  # 静态激活不列位置
            })

    return {
        "general": general_evidences,
        "hour_tkdc": hour_tkdc_evidences,
    }


def _format_tkdc_position_string(pos: dict) -> str:
    """把天克地冲的位置信息格式化为可读字符串。"""
    source = pos.get("source", "")
    pillar = pos.get("pillar", "")
    gan = pos.get("gan", "")
    zhi = pos.get("zhi", "")
    ganzhi = f"{gan}{zhi}"

    if source == "liunian":
        return f"流年{ganzhi}"
    elif source == "dayun":
        return f"大运{ganzhi}"
    else:
        # 命局
        pillar_map = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
        pillar_label = pillar_map.get(pillar, pillar)
        return f"{pillar_label}{ganzhi}"


def _generate_tkdc_hint(clashes_natal: list, clashes_dayun: list, static_events: list) -> str:
    """生成普通天克地冲的提示行（排除年柱、时柱）。

    规则：
    - 年柱天克地冲：完全不算
    - 时柱天克地冲：不在此函数处理（由 _generate_hour_tkdc_hint 处理）
    - 只有月柱/日柱/运年天克地冲才输出通用 hint

    返回:
        提示行字符串，或空字符串（如果没有普通天克地冲）
    """
    tkdc_data = _collect_tkdc_evidences(clashes_natal, clashes_dayun, static_events)
    evidences = tkdc_data.get("general", [])

    if not evidences:
        return ""

    if len(evidences) > 1:
        # 多次：不列位置
        return f"引发多次天克地冲：{_TKDC_HINT}"
    else:
        # 单次：列出位置
        evidence = evidences[0]
        positions = evidence.get("positions", [])
        if positions:
            pos_strs = [_format_tkdc_position_string(pos) for pos in positions if pos]
            pos_str = "/".join(pos_strs) if pos_strs else ""
            if pos_str:
                return f"（{pos_str}）引动天克地冲：{_TKDC_HINT}"
        return f"引动天克地冲：{_TKDC_HINT}"


def _generate_hour_tkdc_hint(clashes_natal: list) -> str:
    """生成时柱天克地冲的提示行。

    规则：
    - 只检测时柱天克地冲
    - 输出格式：（流年XX/时柱XX）时柱天克地冲：可能搬家/换工作。

    返回:
        提示行字符串，或空字符串（如果没有时柱天克地冲）
    """
    for clash in clashes_natal or []:
        if not clash:
            continue
        tkdc_targets = clash.get("tkdc_targets", [])
        for target in tkdc_targets:
            if target.get("pillar") == "hour":
                flow_gan = clash.get("flow_gan", "")
                flow_branch = clash.get("flow_branch", "")
                target_gan = target.get("gan", "")
                target_zhi = clash.get("target_branch", "")
                liunian_ganzhi = f"{flow_gan}{flow_branch}"
                hour_ganzhi = f"{target_gan}{target_zhi}"
                return f"（流年{liunian_ganzhi}/时柱{hour_ganzhi}）时柱天克地冲：{_HOUR_TKDC_HINT}"
    return ""


def _check_has_hour_tkdc(clashes_natal: list) -> bool:
    """检查是否存在时柱天克地冲。

    用于互斥判断：时柱天克地冲 > 时支被冲。
    """
    for clash in clashes_natal or []:
        if not clash:
            continue
        tkdc_targets = clash.get("tkdc_targets", [])
        for target in tkdc_targets:
            if target.get("pillar") == "hour":
                return True
    return False


def _format_clash_natal(ev: dict) -> str:
    """把命局冲的信息整理成一行文字。

    打印顺序：基础冲 → 墓库加成 → 天克地冲 → 总影响
    """
    palaces = sorted(
        {t["palace"] for t in ev.get("targets", []) if t.get("palace")}
    )
    palaces_str = "、".join(palaces) if palaces else "—"

    level = ev.get("impact_level", "unknown")
    level_map = {
        "minor": "轻微变化",
        "moderate": "较大变化",
        "major": "重大变化",
    }
    level_label = level_map.get(level, level)

    # 从 breakdown 或直接字段获取数值
    breakdown = ev.get("breakdown", {})
    base = breakdown.get("base_percent", ev.get("base_power_percent", ev.get("power_percent", 0.0)))
    grave_bonus = breakdown.get("grave_bonus_percent", ev.get("grave_bonus_percent", 0.0))
    tkdc_bonus = breakdown.get("tkdc_bonus_percent", ev.get("tkdc_bonus_percent", ev.get("tian_ke_di_chong_bonus_percent", 0.0)))
    risk = ev.get("risk_percent", base + grave_bonus + tkdc_bonus)

    # 十神信息
    tg = ev.get("shishens", {}) or {}
    flow_tg = tg.get("flow_branch") or {}
    target_tg = tg.get("target_branch") or {}

    flow_ss = flow_tg.get("shishen")
    target_ss = target_tg.get("shishen")

    if flow_ss or target_ss:
        shishen_part = f" 十神：流年 {flow_ss or '-'} / 命局 {target_ss or '-'}"
    else:
        shishen_part = ""

    # 构建一行总览：总冲影响：{total}%（基础冲 {base} + 墓库 {grave} + TKDC {tkdc}）
    clash_detail_parts = [f"基础冲 {base:.2f}"]
    if grave_bonus > 0:
        clash_detail_parts.append(f"墓库 {grave_bonus:.2f}")
    if tkdc_bonus > 0:
        clash_detail_parts.append(f"TKDC {tkdc_bonus:.2f}")
    
    clash_detail_str = " + ".join(clash_detail_parts)
    clash_summary = f"总冲影响：{risk:.2f}%（{clash_detail_str}）"
    
    return (
        f"冲：{ev['flow_branch']}{ev['target_branch']}冲，"
        f"{clash_summary}，"
        f"等级：{level_label}，"
        f"宫位：{palaces_str}"
        f"{shishen_part}"
    )





def run_cli(birth_dt: datetime = None, is_male: bool = None) -> None:
    """运行CLI，可以接受参数（用于测试）或从输入获取（用于交互）。
    
    参数:
        birth_dt: 出生日期时间（可选，如果不提供则从输入获取）
        is_male: 是否为男性（可选，如果不提供则从输入获取）
    """
    if birth_dt is None or is_male is None:
        # 交互模式
        print("=== Hayyy 八字 · 日主强弱 + 用神 + 大运流年 MVP ===")
        print("当前版本：")
        print("  - 只支持【阳历】输入")
        print("  - 时间默认按【出生地当地时间 / 北京时间】理解")
        print("")

        date_str = input("请输入阳历生日 (YYYY-MM-DD)：").strip()
        time_str = input("请输入出生时间 (HH:MM，例如 09:30，未知可写 00:00)：").strip()

        if not date_str:
            print("日期不能为空。")
            return
        if not time_str:
            time_str = "00:00"

        try:
            birth_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            print("日期或时间格式错误，请按 YYYY-MM-DD 和 HH:MM 格式输入。")
            return

        sex_str = input("请输入性别 (M/F)：").strip().upper()
        is_male = True if sex_str != "F" else False

    # ===== 完整分析（使用新的 analyze_complete 函数） =====
    # facts（唯一真相源）：打印层只读该对象
    complete_result = compute_facts(birth_dt, is_male, max_dayun=10)
    result = complete_result["natal"]  # 原局数据
    luck = complete_result["luck"]  # 大运/流年数据
    turning_points = complete_result["turning_points"]  # 转折点
    bazi = result["bazi"]

    print("\n—— 四柱八字 ——")
    print(f"年柱：{bazi['year']['gan']}{bazi['year']['zhi']}")
    print(f"月柱：{bazi['month']['gan']}{bazi['month']['zhi']}")
    print(f"日柱：{bazi['day']['gan']}{bazi['day']['zhi']}  （日主）")
    print(f"时柱：{bazi['hour']['gan']}{bazi['hour']['zhi']}")

    print("\n—— 日主信息 ——")
    print(f"日主：{bazi['day']['gan']} 日（五行：{result['day_master_element']}）")
    print(f"日主综合强弱：{result['strength_percent']:.2f}%")
    print(f"（内部原始得分：{result['strength_score_raw']:.4f}）")
    print(f"生扶力量占比：{result['support_percent']:.2f}%")
    print(f"消耗力量占比：{result['drain_percent']:.2f}%")

    # 主要性格 / 其他性格
    dominant_traits = result.get("dominant_traits") or []
    yongshen_elements = result.get("yongshen_elements", [])

    # 获取日干和八字，用于计算透干和得月令
    day_gan = bazi["day"]["gan"]
    
    if dominant_traits:
        # 辅助：按 group 索引
        trait_by_group = {t.get("group"): t for t in dominant_traits}

        def _stem_hits(trait: dict) -> int:
            """计算该大类总透干次数（所有子类透干次数之和）"""
            detail = trait.get("detail") or []
            hits = sum(d.get("stems_visible_count", 0) for d in detail)
            return min(hits, 3)

        def _get_trait_tougan_info(trait: dict) -> List[tuple]:
            """获取该组的透干信息（具体十神 + 柱位），返回 [(柱位, 具体十神), ...]"""
            tougan_list = []
            detail = trait.get("detail") or []
            
            # 从detail中获取每个子类的透出柱位
            for d in detail:
                shishen_name = d.get("name", "")
                stem_pillars = d.get("stem_pillars", [])  # 已经是中文柱位名列表
                for pillar in stem_pillars:
                    tougan_list.append((pillar, shishen_name))
            
            # 按固定顺序排序：年柱；月柱；时柱
            pillar_order = {"年柱": 0, "月柱": 1, "时柱": 2}
            tougan_list.sort(key=lambda x: (pillar_order.get(x[0], 99), x[0]))
            
            return tougan_list
        
        def _get_trait_yueling_shishen(trait: dict, bazi: dict, day_gan: str) -> Optional[str]:
            """获取该组得月令的具体十神"""
            from .shishen import get_shishen, get_branch_main_gan
            
            # 先检查trait中是否有de_yueling字段
            de_yueling = trait.get("de_yueling")
            if de_yueling:
                # 如果de_yueling是"得月令"，需要从月支计算具体十神
                if de_yueling == "得月令":
                    month_zhi = bazi["month"]["zhi"]
                    month_main_gan = get_branch_main_gan(month_zhi)
                    if month_main_gan:
                        month_ss = get_shishen(day_gan, month_main_gan)
                        return month_ss
                # 如果de_yueling是"{具体十神}得月令"，提取具体十神
                elif "得月令" in de_yueling:
                    # 例如"正官得月令" -> "正官"
                    shishen = de_yueling.replace("得月令", "")
                    return shishen
            
            return None

        def _format_trait_new(trait: dict, bazi: dict, day_gan: str, yongshen_elements: list, is_major: bool = False) -> List[str]:
            """新的格式化函数，返回多行输出

            参数:
                is_major: 是否在主要性格中输出（只有主要性格才输出天赋卡）
            """
            from .shishen import get_shishen
            
            group = trait.get("group", "")
            total_percent = trait.get("total_percent", 0.0)
            detail = trait.get("detail") or []
            
            # 1.1 组是否打印：若该组 正% + 偏% == 0，整组不打印
            zheng_percent = 0.0
            pian_percent = 0.0
            zheng_shishen = None
            pian_shishen = None
            
            # 定义组到具体十神的映射（正/偏）
            # 注意：对于食伤组，食神是"正"，伤官是"偏"
            # 对于比劫组，比肩是"正"，劫财是"偏"
            group_to_shishens = {
                "印": ("正印", "偏印"),
                "官杀": ("正官", "七杀"),
                "食伤": ("食神", "伤官"),  # 食神=正，伤官=偏
                "比劫": ("比肩", "劫财"),  # 比肩=正，劫财=偏
                "财": ("正财", "偏财"),
            }
            
            zheng_name, pian_name = group_to_shishens.get(group, ("", ""))
            
            for d in detail:
                name = d.get("name", "")
                percent = d.get("percent", 0.0)
                if name == zheng_name:
                    zheng_percent = percent
                    zheng_shishen = name
                elif name == pian_name:
                    pian_percent = percent
                    pian_shishen = name
            
            if zheng_percent == 0.0 and pian_percent == 0.0:
                # 原局没有该类十神，打印"原局没有XXX"
                return [f"{group}：原局没有{group}"]
            
            # 1.2 偏占比计算（仅在并存时）
            pian_ratio = None
            if zheng_percent > 0.0 and pian_percent > 0.0:
                total_sub_percent = zheng_percent + pian_percent
                if total_sub_percent > 0.0:
                    pian_ratio = pian_percent / total_sub_percent
                    # 保留1位小数，四舍五入（使用round，但注意0.75应该变成0.8）
                    pian_ratio = round(pian_ratio + 0.0001, 1)  # 加小量避免浮点误差
                    if pian_ratio > 1.0:
                        pian_ratio = 1.0
            
            # 1.3 口径阈值
            koujing = None
            if pian_ratio is not None:
                if pian_ratio <= 0.30:
                    koujing = f"{zheng_shishen}明显更多（{pian_shishen}只算一点）"
                elif pian_ratio <= 0.60:
                    koujing = f"{zheng_shishen}与{pian_shishen}并存"
                else:  # pian_ratio > 0.60
                    koujing = f"{pian_shishen}明显更多（{zheng_shishen}只算一点）"
            
            # 1.4 "纯"判定
            is_pure = False
            pure_shishen = None
            pure_percent = 0.0
            if zheng_percent > 0.0 and pian_percent == 0.0:
                is_pure = True
                pure_shishen = zheng_shishen
                pure_percent = zheng_percent
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                is_pure = True
                pure_shishen = pian_shishen
                pure_percent = pian_percent
            
            # 2. 透干信息（具体十神 + 柱位）
            tougan_list = _get_trait_tougan_info(trait)
            
            # 3. 得月令信息（具体十神）
            yueling_shishen = _get_trait_yueling_shishen(trait, bazi, day_gan)
            
            # 4. 主标签
            if is_pure:
                main_label = pure_shishen
            else:
                if pian_ratio is not None:
                    if pian_ratio > 0.60:
                        main_label = pian_shishen
                    elif pian_ratio <= 0.30:
                        main_label = zheng_shishen
                    else:  # 0.30 < pian_ratio <= 0.60
                        main_label = f"{zheng_shishen}与{pian_shishen}"
                else:
                    main_label = group
            
            # 4.1 第一行构建
            line1_parts = [f"{group}（{total_percent:.1f}%）：{main_label}"]
            
            # 得月令段
            if yueling_shishen:
                line1_parts.append(f"得月令：{yueling_shishen}")
            
            # 透干段（用全角分号连接）
            if tougan_list:
                tougan_strs = [f"{pillar}{shishen}透干×1" for pillar, shishen in tougan_list]
                line1_parts.append("；".join(tougan_strs))
            
            # 结构段
            if is_pure:
                struct_str = f"纯{pure_shishen}{pure_percent:.1f}%"
            else:
                struct_str = f"{zheng_shishen}{zheng_percent:.1f}%，{pian_shishen}{pian_percent:.1f}%"
            line1_parts.append(struct_str)
            
            line1 = "；".join(line1_parts)
            
            # 4.2 后续行（Bullet行）
            lines = [line1]
            
            # 获取 xiongshen_status 并映射为展示短语
            xiongshen_status = trait.get("xiongshen_status", "none")
            xiongshen_display_map = {
                "pure_xiongshen": "纯凶神",
                "xiongshen_majority": "凶神占多数",
                "split": "凶/非各半",
                "none": "非凶神",
            }
            xiongshen_display = xiongshen_display_map.get(xiongshen_status, "非凶神")
            
            if not is_pure and pian_ratio is not None:
                # 并存：打印三行
                lines.append(f"- 偏占多少：{pian_ratio:.1f}")
                lines.append(f"- 混杂口径：{koujing} | 神性：{xiongshen_display}")
            elif is_pure:
                # 纯：打印混杂口径（新增）
                lines.append(f"- 混杂口径：纯{pure_shishen}，只有{pure_shishen}心性。 | 神性：{xiongshen_display}")
            
            # 最后一行：五行和用神
            element = trait.get("element", "")
            if not element:
                element = "None"
            is_yongshen = element in yongshen_elements if element and element != "None" else False
            yongshen_status = "为用神" if is_yongshen else "不为用神"
            lines.append(f"- {group}的五行：{element}；{group}{yongshen_status}")

            # ============================================================
            # 天赋卡（只在主要性格中输出）
            # ============================================================
            if is_major:
                if group == "印":
                    lines.extend(_get_yinxing_talent_card(is_pure, pure_shishen, pian_ratio))
                elif group == "财":
                    lines.extend(_get_caixing_talent_card(is_pure, pure_shishen, pian_ratio))
                elif group == "比劫":
                    lines.extend(_get_bijie_talent_card())
                elif group == "官杀":
                    lines.extend(_get_guansha_talent_card(is_pure, pure_shishen, pian_ratio))
                elif group == "食伤":
                    lines.extend(_get_shishang_talent_card(is_pure, pure_shishen, pian_ratio))

            return lines

        def _format_trait_line1(trait: dict, is_major_by_rule3: bool = False) -> str:
            """格式化第1行：{大类}（{total_percent:.1f}%）：{子类标签}；{透干柱位列表}透干×{n}；{得月令字段}；{子类百分比摘要}"""
            group = trait.get("group", "-")
            total_percent = trait.get("total_percent", 0.0)
            sub_label = trait.get("sub_label", trait.get("mix_label", ""))
            detail = trait.get("detail") or []
            de_yueling = trait.get("de_yueling")
            
            # 如果力量为0，显示"八字中没有{大类}星"
            if total_percent == 0.0:
                # 根据大类名称生成对应的星名
                star_name_map = {
                    "财": "财星",
                    "印": "印星",
                    "官杀": "官杀星",
                    "食伤": "食伤星",
                    "比劫": "比劫星",
                }
                star_name = star_name_map.get(group, f"{group}星")
                sub_label = f"八字中没有{star_name}"
            
            # 收集所有透出的柱位（合并所有子类的透出柱位）
            all_stem_pillars = []
            total_stem_hits = 0
            for d in detail:
                stem_pillars = d.get("stem_pillars", [])
                all_stem_pillars.extend(stem_pillars)
                total_stem_hits += d.get("stems_visible_count", 0)
            
            # 去重并保持顺序（年柱→月柱→时柱）
            pillar_order = ["年柱", "月柱", "时柱"]
            seen = set()
            ordered_pillars = []
            for p in pillar_order:
                if p in all_stem_pillars and p not in seen:
                    ordered_pillars.append(p)
                    seen.add(p)
            
            # 构建透干信息
            stem_part = ""
            if total_stem_hits >= 1:
                pillars_str = "，".join(ordered_pillars)
                stem_part = f"；{pillars_str}透干×{total_stem_hits}"
                if is_major_by_rule3:
                    stem_part += "，且为用神"
            
            # 得月令字段
            de_yueling_part = ""
            if de_yueling:
                de_yueling_part = f"；{de_yueling}"
            
            # 子类百分比摘要
            present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
            if len(present_subs) == 1:
                # 纯：纯{子类}{percent:.1f}%
                sub_name = present_subs[0].get("name", "")
                sub_percent = present_subs[0].get("percent", 0.0)
                subs_summary = f"纯{sub_name}{sub_percent:.1f}%"
            elif len(present_subs) >= 2:
                # 混：两个子类的百分比，用逗号分隔
                # 固定顺序：正/偏、正官/七杀、食神/伤官、比肩/劫财、正印/偏印
                sub_pairs = []
                for d in detail:
                    if d.get("percent", 0.0) > 0.0:
                        sub_pairs.append((d.get("name", ""), d.get("percent", 0.0)))
                # 按固定顺序排序（正/偏、正官/七杀等，正在前，偏/杀在后）
                # 但用户期望输出显示"偏财20.0%，正财15.0%"，说明应该按占比降序
                # 重新理解：用户说"固定顺序：正/偏、正官/七杀、食神/伤官、比肩/劫财、正印/偏印"
                # 但实际期望输出是"偏财20.0%，正财15.0%"，说明应该按占比从高到低排序
                sub_pairs.sort(key=lambda x: -x[1])  # 按占比降序排序
                subs_summary = "，".join(f"{name}{percent:.1f}%" for name, percent in sub_pairs)
            else:
                subs_summary = "—"
            
            return f"{group}（{total_percent:.1f}%）：{sub_label}{stem_part}{de_yueling_part}；{subs_summary}"
        
        def _format_trait_line2(trait: dict) -> str:
            """格式化第2行：{大类}的五行：{element}；{大类}{为/不为}用神"""
            group = trait.get("group", "-")
            element = trait.get("element", "")
            # 即使 element 为 None 或空，也要显示（当力量为0时，element 应该已经通过定义计算出来了）
            if not element:
                element = "None"  # 如果还是没有，显示 None（但理论上不应该出现）
            is_yongshen = element in yongshen_elements if element and element != "None" else False
            yongshen_status = "为用神" if is_yongshen else "不为用神"
            return f"- {group}的五行：{element}；{group}{yongshen_status}"

        # 主要性格：满足 total_percent>=35 或 stem_hits>=2 或 (stem_hits>=1 且为用神)
        major = []
        major_by_rule3 = set()  # 记录因为规则3（透干>=1且为用神）而晋级的主要性格
        
        for t in dominant_traits:
            total_percent = t.get("total_percent", 0.0)
            hits = _stem_hits(t)
            element = t.get("element", "")
            is_yongshen = element in yongshen_elements if element else False
            
            is_major = False
            if total_percent >= 35.0 or hits >= 2:
                is_major = True
            elif hits >= 1 and is_yongshen:
                is_major = True
                major_by_rule3.add(t.get("group"))
            
            if is_major:
                major.append(t)

        # 收集已经在"主要性格"里打印过的性格大类，用于"其他性格"去重
        main_groups = {t.get("group") for t in major} if major else set()

        if major:
            print("\n—— 主要性格 ——")
            for trait in major:
                lines = _format_trait_new(trait, bazi, day_gan, yongshen_elements, is_major=True)
                for line in lines:
                    print(line)

        # 其他性格：五大类全量（含 0%）
        print("\n—— 其他性格 ——")
        all_groups = ["财", "印", "官杀", "食伤", "比劫"]
        for g in all_groups:
            # 已经在"主要性格"中打印过的性格大类，这里跳过，避免重复
            if g in main_groups:
                continue
            trait = trait_by_group.get(g, {})
            if not trait:
                # 如果该大类不存在，创建一个空的
                trait = {
                    "group": g,
                    "total_percent": 0.0,
                    "sub_label": "无",
                    "detail": [],
                    "de_yueling": None,
                    "element": None,
                }

            lines = _format_trait_new(trait, bazi, day_gan, yongshen_elements)
            for line in lines:
                print(line)

    # ============================================================
    # 性格快速汇总
    # ============================================================

    # 一句版常量定义（印星/财星使用新版汇总，其他十神保持原有思维/社交分开）
    # 注意：印星使用 _YINXING_QUICK_SUMMARY_V2，财星使用 _CAIXING_QUICK_SUMMARY_V2
    QUICK_SUMMARY_MIND = {
        # 官杀一句版（思维）
        "正官": "规则感强，重秩序与标准，做决策更看合规与稳定性，倾向把事情流程化、长期化地跑稳。",
        "七杀": "反应快、决断力强，遇事敢拍板、敢承压；行动导向明显，更习惯用结果说话。",
        "正官七杀": "既讲章法与规矩，也有决断力与行动力；「稳」和「狠」的两种处事方式并存。",
        # 比劫一句版（思维）- 比肩/劫财统一使用
        "比肩劫财": "不服输、自我驱动强，认准方向就能长期坚持、扛压力推进；立场很稳，但有时也会更坚持己见。",
        # 食伤一句版（思维）
        "食神": "想到就做、顺势而为；即使在压力里也能把状态稳住，反而更容易进入发挥区，能说会道、口才好，临场表现感往往更强。",
        "伤官": "创意强、表达欲旺，喜欢打破常规追求新意；更敢试错走差异化路线，擅长把点子与观点做成可被看见的成果，从而打开机会与资源。",
        "食神伤官": "更偏伤官：创意与表达驱动，敢突破常规、走差异化换机会；同时带点食神的随性与松弛感，想到就做，临场更容易发挥。",
    }

    QUICK_SUMMARY_SOCIAL = {
        # 官杀一句版（社交）
        "正官": "端正、有分寸、重礼节；给人靠谱、守信、有底线的印象，擅长用可预期的方式建立信任。",
        "七杀": "存在感强，做事直接、效率优先；更容易让人相信「你能扛事/能解决问题」，但不爱反复解释。",
        "正官七杀": "既端正有分寸，也气场硬、边界感强；能靠靠谱建立信任，也能靠果断赢得尊重。",
        # 比劫一句版（社交）- 比肩/劫财统一使用
        "比肩劫财": "社交覆盖面广，擅长在不同圈层建立连接并把关系落到合作与行动上；对深度关系更谨慎投入，更看重尊重、边界与长期的互相成就，深交偏少而精。",
        # 食伤一句版（社交）
        "食神": "亲和、好相处，给人放松、没压力的感觉；习惯用温和的方式表达，不爱冲突也不爱争论。",
        "伤官": "逻辑表达直接且清晰，容易给人「有想法有态度」的印象；有号召力与领导能力，能团结很多人、推动行动。",
        "食神伤官": "更偏伤官：表达直接清晰、观点鲜明，容易让人信服并形成号召力；同时有食神的亲和与不压迫感，更容易把人聚拢起来、推动行动。",
    }

    def _get_shishen_summary_name(trait: dict) -> Optional[str]:
        """根据trait获取快速汇总中使用的十神名称

        返回规则：
        - 财星：纯偏财→偏财，纯正财→正财，混杂→正偏财
        - 印星：纯偏印→偏印，纯正印→正印，混杂→正偏印
        - 其他十神：命中一个就列该名，两个都命中列"正偏"形式
        """
        group = trait.get("group", "")
        detail = trait.get("detail") or []

        # 定义组到具体十神的映射
        group_to_shishens = {
            "印": ("正印", "偏印"),
            "官杀": ("正官", "七杀"),
            "食伤": ("食神", "伤官"),
            "比劫": ("比肩", "劫财"),
            "财": ("正财", "偏财"),
        }

        zheng_name, pian_name = group_to_shishens.get(group, ("", ""))

        zheng_percent = 0.0
        pian_percent = 0.0
        for d in detail:
            name = d.get("name", "")
            percent = d.get("percent", 0.0)
            if name == zheng_name:
                zheng_percent = percent
            elif name == pian_name:
                pian_percent = percent

        if zheng_percent == 0.0 and pian_percent == 0.0:
            return None

        # 财星和印星的命名规则
        if group == "财":
            if zheng_percent > 0.0 and pian_percent == 0.0:
                return "正财"
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                return "偏财"
            else:
                return "正偏财"
        elif group == "印":
            if zheng_percent > 0.0 and pian_percent == 0.0:
                return "正印"
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                return "偏印"
            else:
                return "正偏印"
        # 其他十神：食伤/比劫/官杀
        elif group == "食伤":
            if zheng_percent > 0.0 and pian_percent == 0.0:
                return "食神"
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                return "伤官"
            else:
                return "食神伤官"
        elif group == "比劫":
            # 比劫统一使用"比劫"（不区分纯比肩/纯劫财/混杂）
            return "比劫"
        elif group == "官杀":
            if zheng_percent > 0.0 and pian_percent == 0.0:
                return "正官"
            elif pian_percent > 0.0 and zheng_percent == 0.0:
                return "七杀"
            else:
                return "正官七杀"

        return None

    def build_personality_quick_summary(major_traits: List[dict], trait_by_group: dict) -> dict:
        """构建性格快速汇总结构

        返回: {
            "overview": ["偏财", "偏印", ...],  # 主要性格列表，按固定顺序
            "mind": [("偏财", "..."), ("偏印", "...")],  # 思维天赋（印星/财星使用汇总文案）
            "social": [("正官", "..."), ...]],  # 社交天赋（印星/财星不输出）
            "pending": ["食神", "劫财", ...]  # 暂未纳入快速汇总的其他十神
        }

        注意：
        - 印星使用新版「性格画像」文案，不再区分思维/社交天赋
        - 财星使用新版「汇总」文案，不再区分思维/社交天赋
        """
        # 固定顺序：财 → 印 → 食伤 → 比劫 → 官杀
        GROUP_ORDER = ["财", "印", "食伤", "比劫", "官杀"]

        overview = []
        mind = []
        social = []
        pending = []

        # 收集主要性格中的各类十神
        major_groups = {t.get("group") for t in major_traits}

        for group in GROUP_ORDER:
            if group not in major_groups:
                continue

            trait = trait_by_group.get(group, {})
            if not trait:
                continue

            name = _get_shishen_summary_name(trait)
            if not name:
                continue

            overview.append(name)

            # 印星：使用新版性格画像，只加入 mind（不加入 social）
            if group == "印":
                portrait_text = _YINXING_QUICK_SUMMARY_V2.get(name)
                if portrait_text:
                    mind.append((name, portrait_text))
                # 印星不再输出 social
            # 财星：使用新版汇总文案，只加入 mind（不加入 social）
            elif group == "财":
                summary_text = _CAIXING_QUICK_SUMMARY_V2.get(name)
                if summary_text:
                    mind.append((name, summary_text))
                # 财星不再输出 social
            # 比劫：使用新版汇总文案，只加入 mind（不加入 social）
            elif group == "比劫":
                # 比劫统一使用"比劫"作为显示名称
                mind.append(("比劫", _BIJIE_QUICK_SUMMARY_V2))
                # 比劫不再输出 social
            # 官杀：使用新版汇总文案，只加入 mind（不加入 social）
            elif group == "官杀":
                summary_text = _GUANSHA_QUICK_SUMMARY_V2.get(name)
                if summary_text:
                    mind.append((name, summary_text))
                # 官杀不再输出 social
            # 食伤：使用新版汇总文案，只加入 mind（不加入 social）
            elif group == "食伤":
                summary_text = _SHISHANG_QUICK_SUMMARY_V2.get(name)
                if summary_text:
                    mind.append((name, summary_text))
                # 食伤不再输出 social

        return {
            "overview": overview,
            "mind": mind,
            "social": social,
            "pending": pending,
        }

    # 构建快速汇总
    if dominant_traits:
        summary = build_personality_quick_summary(major, trait_by_group)

        # 打印性格快速汇总板块
        print("\n—— 性格快速汇总 ——")

        # 1. 总览（永远打印）
        if summary["overview"]:
            overview_str = "、".join(summary["overview"])
            print(f"总览：本命局主要性格包含：{overview_str}。")
            print()  # 总览后空一行

        # 2. 思维天赋（只输出印星与财星）
        if summary["mind"]:
            print("思维天赋：")
            for name, text in summary["mind"]:
                print(f"- {name}：{text}")

        # 3. 社交天赋（只输出印星与财星）
        if summary["social"]:
            print("社交天赋：")
            for name, text in summary["social"]:
                print(f"- {name}：{text}")

        # 4. 备注（如果有其他十神）
        if summary["pending"]:
            pending_str = "、".join(summary["pending"])
            print(f"备注：已识别但暂未纳入快速汇总：{pending_str}。")

    # 六亲助力：只输出用神十神大类（从结构化结果读取）
    print("\n—— 六亲助力 ——")
    
    # 从结构化结果读取 liuqin_zhuli
    liuqin_traits = result.get("liuqin_zhuli", [])
    
    def _get_liuqin_source(group: str, detail: List[Dict[str, Any]], total_percent: float, is_male: bool) -> str:
        """获取六亲助力的来源清单"""
        present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
        
        if group == "印":
            if total_percent == 0:
                # 原局没有印星：合并输出
                return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系，技术型/非传统学习与灵感路径（偏印）"
            else:
                zhengyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正印"), 0.0)
                pianyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏印"), 0.0)
                
                if zhengyin_percent > 0 and pianyin_percent == 0:
                    # 纯正印
                    return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系"
                elif pianyin_percent > 0 and zhengyin_percent == 0:
                    # 纯偏印
                    return "母亲/长辈/贵人/老师，技术型/非传统学习与灵感路径（偏印）"
                else:
                    # 混杂
                    return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系 ＋ 技术型/非传统学习与灵感路径（偏印）"
        
        elif group == "比劫":
            # 比肩/劫财/比劫混杂，都用统一来源（不再区分）
            if total_percent == 0:
                # 原局没有比劫星（去掉末尾逗号）
                return "兄弟姐妹/同辈朋友/同学同事，自我/独立/同行合伙/同类支持"
            else:
                # 比肩/劫财/混杂，都用统一来源
                return "兄弟姐妹/同辈朋友/同学同事，自我/独立/同行合伙/同类支持"
        
        elif group == "食伤":
            if total_percent == 0:
                # 原局没有食伤星：统一新文案
                return "子女/晚辈/技术，合理宣泄/才艺产出，表达/创新/输出型技术，考试发挥/即兴发挥/临场表现"
            else:
                shishen_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "食神"), 0.0)
                shangguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "伤官"), 0.0)
                
                if shishen_percent > 0 and shangguan_percent == 0:
                    # 纯食神：保留原来的更细分来源
                    return "子女/晚辈，享受/口福/温和表达/才艺产出/疗愈与松弛"
                elif shangguan_percent > 0 and shishen_percent == 0:
                    # 纯伤官：保留原来的更细分来源
                    return "子女/晚辈，表达欲/叛逆/创新/挑规则/锋芒与口舌是非/输出型技术"
                else:
                    # 混杂：统一新文案
                    return "子女/晚辈/技术，合理宣泄/才艺产出，表达/创新/输出型技术，考试发挥/即兴发挥/临场表现"
        
        elif group == "财":
            if total_percent == 0:
                # 原局没有财星
                if is_male:
                    return "父亲/爸爸，妻子/老婆/伴侣，钱与资源/收入/项目机会/交换"
                else:
                    return "父亲/爸爸，钱与资源/收入/项目机会/交换"
            else:
                zhengcai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正财"), 0.0)
                piancai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏财"), 0.0)
                
                if zhengcai_percent > 0 and piancai_percent == 0:
                    # 纯正财
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报"
                    else:
                        return "父亲/爸爸，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报"
                elif piancai_percent > 0 and zhengcai_percent == 0:
                    # 纯偏财
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，外财/机会财/项目/做生意/社交资源/流动性/投机"
                    else:
                        return "父亲/爸爸，外财/机会财/项目/做生意/社交资源/流动性/投机"
                else:
                    # 混杂（合并输出）
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报，外财/机会财/项目/做生意/社交资源/流动性/投机"
                    else:
                        return "父亲/爸爸，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报，外财/机会财/项目/做生意/社交资源/流动性/投机"
        
        elif group == "官杀":
            if total_percent == 0:
                # 原局没有官杀星
                if is_male:
                    return "领导/上司/官职/体制/规则/名气/声望"
                else:
                    return "老公/丈夫/男友，领导/上司/官职/体制/规则/名气/声望"
            else:
                zhengguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正官"), 0.0)
                qisha_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "七杀"), 0.0)
                
                if zhengguan_percent > 0 and qisha_percent == 0:
                    # 纯正官
                    if is_male:
                        return "领导/上司/官职/职位/体制/规则/名气/声望/责任与自我约束"
                    else:
                        return "老公/丈夫/男友，领导/上司/官职/职位/体制/规则/名气/声望/责任与自我约束"
                elif qisha_percent > 0 and zhengguan_percent == 0:
                    # 纯七杀
                    if is_male:
                        return "领导/上司/强权压力/竞争与执行/风险与突破，官职/体制/规则/名气"
                    else:
                        return "老公/丈夫/男友，领导/上司/强权压力/竞争与执行/风险与突破，官职/体制/规则/名气"
                else:
                    # 混杂（合并输出）
                    if is_male:
                        return "领导/上司/强权压力/竞争与执行/风险与突破，官职/职位/体制/规则/名气/声望/责任与自我约束"
                    else:
                        return "老公/丈夫/男友，领导/上司/强权压力/竞争与执行/风险与突破，官职/职位/体制/规则/名气/声望/责任与自我约束"
        
        return ""
    
    def _get_liuqin_status(group: str, detail: List[Dict[str, Any]], total_percent: float) -> str:
        """获取六亲助力的括号状态"""
        if total_percent == 0:
            star_name_map = {
                "财": "财星",
                "印": "印星",
                "官杀": "官杀星",
                "食伤": "食伤星",
                "比劫": "比劫星",
            }
            star_name = star_name_map.get(group, f"{group}星")
            return f"（原局没有{star_name}）"
        
        present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
        
        if group == "印":
            zhengyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正印"), 0.0)
            pianyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏印"), 0.0)
            if zhengyin_percent > 0 and pianyin_percent == 0:
                return "（正印）"
            elif pianyin_percent > 0 and zhengyin_percent == 0:
                return "（偏印）"
            else:
                return "（正偏印混杂）"
        
        elif group == "财":
            zhengcai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正财"), 0.0)
            piancai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏财"), 0.0)
            if zhengcai_percent > 0 and piancai_percent == 0:
                return "（正财）"
            elif piancai_percent > 0 and zhengcai_percent == 0:
                return "（偏财）"
            else:
                return "（正偏财混杂）"
        
        elif group == "官杀":
            zhengguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正官"), 0.0)
            qisha_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "七杀"), 0.0)
            if zhengguan_percent > 0 and qisha_percent == 0:
                return "（正官）"
            elif qisha_percent > 0 and zhengguan_percent == 0:
                return "（七杀）"
            else:
                return "（官杀混杂）"
        
        elif group == "食伤":
            shishen_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "食神"), 0.0)
            shangguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "伤官"), 0.0)
            if shishen_percent > 0 and shangguan_percent == 0:
                return "（食神）"
            elif shangguan_percent > 0 and shishen_percent == 0:
                return "（伤官）"
            else:
                return "（食伤混杂）"
        
        elif group == "比劫":
            bijian_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "比肩"), 0.0)
            jiecai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "劫财"), 0.0)
            if bijian_percent > 0 and jiecai_percent == 0:
                return "（比肩）"
            elif jiecai_percent > 0 and bijian_percent == 0:
                return "（劫财）"
            elif bijian_percent > 0 and jiecai_percent > 0:
                return "（比劫混杂）"
            else:
                return ""
        
        return ""
    
    def _get_strength_text(total_percent: float, group: str) -> str:
        """获取强度话术"""
        if total_percent == 0:
            return f"该助力有心帮助但能力一般；走到{group}运/年会有额外帮助。"
        elif total_percent < 30:
            return "用神有力，助力较多。"
        else:
            return "用神力量很大，助力非常非常大。"
    
    # 获取所有五大类，检查哪些是用神
    all_categories = ["印", "财", "官杀", "食伤", "比劫"]
    liuqin_traits = []
    
    for cat in all_categories:
        trait = trait_by_group.get(cat, {})
        if not trait:
            # 如果该大类不存在，创建一个空的
            trait = {
                "group": cat,
                "total_percent": 0.0,
                "sub_label": "无",
                "detail": [],
                "de_yueling": None,
                "element": None,
            }
            # 需要计算该大类的五行（通过定义）
            from .traits import _get_category_element_by_definition
            bazi = result.get("bazi", {})
            day_gan = bazi.get("day", {}).get("gan", "")
            if day_gan:
                # 将显示名称转换为内部类别名称
                cat_internal = "印星" if cat == "印" else "财星" if cat == "财" else cat
                trait["element"] = _get_category_element_by_definition(cat_internal, day_gan)
        
        element = trait.get("element", "")
        if element and element in yongshen_elements:
            # 该大类是用神，加入六亲助力
            liuqin_traits.append(trait)
    
    # 打印六亲助力
    for trait in liuqin_traits:
        group = trait.get("group", "")
        total_percent = trait.get("total_percent", 0.0)
        detail = trait.get("detail", [])
        
        # 名称字段：比劫在原局有星时显示"比肩"，否则显示"比劫"
        display_name = group
        if group == "比劫" and total_percent > 0:
            # 只要原局有比劫星（total_percent > 0），就显示"比肩"
            display_name = "比肩"
        
        # 括号状态
        status = _get_liuqin_status(group, detail, total_percent)
        
        # 强度话术
        strength_text = _get_strength_text(total_percent, group)
        
        # 第1行
        print(f"{display_name}{status}：{strength_text}")
        
        # 第2行（缩进两个空格）
        source = _get_liuqin_source(group, detail, total_percent, is_male)
        print(f"  来源：{source}")

    print("\n—— 全局五行占比（八个字）——")
    global_dist = result["global_element_percentages"]
    for e in ["木", "火", "土", "金", "水"]:
        print(f"{e}：{global_dist.get(e, 0.0):.2f}%")

    # 合并用神信息打印
    print("\n—— 用神信息 ——")
    yong = result["yongshen_elements"]
    yong_str = "、".join(yong)
    # 用神五行（候选）只保留用神五行，不再夹带婚配倾向
    print(f"用神五行（候选）： {yong_str}")
    
    # 用神（五行→十神）
    yong_ss = result.get("yongshen_shishen") or []
    if yong_ss:
        ss_parts = []
        for entry in yong_ss:
            elem = entry.get("element", "-")
            cats = entry.get("categories") or []
            specifics = entry.get("shishens") or []
            cats_str = "、".join(cats) if cats else "-"
            specs_str = "、".join(specifics) if specifics else "-"
            ss_parts.append(f"{elem}：{cats_str}（{specs_str}）")
        print("用神（五行→十神）：" + "，".join(ss_parts))
    
    # 用神落点
    yong_tokens = result.get("yongshen_tokens") or []
    pillar_label = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    kind_label = {"gan": "干", "zhi": "支"}
    tokens_by_elem = {e.get("element"): e.get("positions", []) for e in yong_tokens}
    
    luodian_parts = []
    for elem in yong:
        positions = tokens_by_elem.get(elem, [])
        if not positions:
            luodian_parts.append(f"{elem}：原局没有")
            continue
        parts = []
        for pos in positions:
            pillar = pillar_label.get(pos.get("pillar", ""), pos.get("pillar", ""))
            kind = kind_label.get(pos.get("kind", ""), pos.get("kind", ""))
            char = pos.get("char", "?")
            ss = pos.get("shishen", "-")
            parts.append(f"{pillar}{kind} {char}({ss})")
        luodian_parts.append(f"{elem}：" + "，".join(parts))
    if luodian_parts:
        print("用神落点：" + "，".join(luodian_parts))
    
    # ===== 原局六合（只解释，不计分） =====
    from .config import PILLAR_PALACE_CN
    natal_harmonies = result.get("natal_harmonies", []) or []
    # 原局六合
    natal_liuhe_lines = []
    for ev in natal_harmonies:
        if ev.get("type") != "branch_harmony":
            continue
        if ev.get("subtype") != "liuhe":
            continue
        targets = ev.get("targets", [])
        if len(targets) < 2:
            continue
        t1, t2 = targets[0], targets[1]
        palace1 = t1.get("palace", "")
        palace2 = t2.get("palace", "")
        members = ev.get("members") or ev.get("matched_branches") or []
        if len(members) >= 2:
            pair_str = f"{members[0]}{members[1]}合"
        else:
            pair_str = f"{t1.get('target_branch', '')}{t2.get('target_branch', '')}合"
        if palace1 and palace2:
            natal_liuhe_lines.append(f"{palace1}和{palace2}合（{pair_str}）")
    if natal_liuhe_lines:
        # 只去掉完全重复的，同一宫位组合要保留
        uniq_lines = sorted(set(natal_liuhe_lines))
        print("原局六合：" + "，".join(uniq_lines))

    # 原局半合
    natal_banhe_lines = []
    for ev in natal_harmonies:
        if ev.get("type") != "branch_harmony":
            continue
        if ev.get("subtype") != "banhe":
            continue
        targets = ev.get("targets", [])
        if len(targets) < 2:
            continue
        t1, t2 = targets[0], targets[1]
        palace1 = t1.get("palace", "")
        palace2 = t2.get("palace", "")
        matched = ev.get("matched_branches", [])
        if len(matched) >= 2:
            pair_str = f"{matched[0]}{matched[1]}半合"
        else:
            pair_str = f"{t1.get('target_branch', '')}{t2.get('target_branch', '')}半合"
        if palace1 and palace2:
            natal_banhe_lines.append(f"{palace1} 与 {palace2} 半合（{pair_str}）")
    if natal_banhe_lines:
        uniq_banhe = sorted(set(natal_banhe_lines))
        print("原局半合：" + "，".join(uniq_banhe))
    
    # ===== 原局天干五合（只识别+打印，不影响风险） =====
    from .gan_wuhe import GanPosition, detect_gan_wuhe, format_gan_wuhe_event
    from .shishen import get_shishen
    
    day_gan = bazi["day"]["gan"]
    natal_gan_positions = []
    # 原局入口使用"年柱天干"格式
    pillar_labels = {"year": "年柱天干", "month": "月柱天干", "day": "日柱天干", "hour": "时柱天干"}
    for pillar in ["year", "month", "day", "hour"]:
        gan = bazi[pillar]["gan"]
        shishen = get_shishen(day_gan, gan) or "-"
        natal_gan_positions.append(GanPosition(
            source="natal",
            label=pillar_labels[pillar],
            gan=gan,
            shishen=shishen
        ))
    
    natal_wuhe_events = detect_gan_wuhe(natal_gan_positions)
    if natal_wuhe_events:
        for ev in natal_wuhe_events:
            # 原局入口不再带“原局”前缀，只打印柱位+字+五合+十神关系
            line = format_gan_wuhe_event(ev, incoming_shishen=None)
            print(f"原局天干五合：{line}")
    
    # ===== 婚配倾向（独立 section，只包含匹配倾向） =====
    marriage_hint = result.get("marriage_hint", "")
    if marriage_hint:
        print("\n—— 婚配倾向 ——")
        print(marriage_hint)
    
    # 原局问题打印
    from .clash import detect_natal_tian_ke_di_chong
    
    natal_conflicts = result.get("natal_conflicts", {})
    natal_clashes = natal_conflicts.get("clashes", [])
    natal_punishments = natal_conflicts.get("punishments", [])
    natal_tkdc = detect_natal_tian_ke_di_chong(bazi)
    natal_patterns = result.get("natal_patterns", [])
    
    def _get_clash_explanation(palace1: str, palace2: str) -> str:
        """获取特定冲的解释文本"""
        # 标准化宫位名称（处理"事业家庭宫"和"家庭事业宫"的差异）
        def normalize_palace(p: str) -> str:
            if p == "事业家庭宫":
                return "家庭事业宫"
            return p
        
        p1 = normalize_palace(palace1)
        p2 = normalize_palace(palace2)
        
        # 创建宫位对（不区分顺序）
        palace_pair = frozenset([p1, p2])
        
        # 4种特定冲的解释
        clash_explanations = {
            frozenset(["祖上宫", "婚姻宫"]): "少年时期成长坎坷，家庭变故多",
            frozenset(["婚姻宫", "夫妻宫"]): "感情、婚姻矛盾多，变故频频",
            frozenset(["夫妻宫", "家庭事业宫"]): "中年后家庭生活不和谐，和子女关系不好或者没有子女",
            frozenset(["祖上宫", "夫妻宫"]): "婚姻生活易受上一辈、早年经历影响",
        }
        
        return clash_explanations.get(palace_pair, "")
    
    issues = []
    
    # 打印原局冲
    for clash in natal_clashes:
        targets = clash.get("targets", [])
        flow_branch = clash.get("flow_branch", "")
        target_branch = clash.get("target_branch", "")
        
        if targets and flow_branch and target_branch:
            # 获取被冲的宫位（targets中的）
            target_palaces = sorted({PILLAR_PALACE_CN.get(t.get("pillar", ""), "") for t in targets if t.get("pillar")})
            
            # 获取主动冲的宫位（flow_branch对应的柱）
            flow_palace = None
            for pillar in ("year", "month", "day", "hour"):
                if bazi[pillar]["zhi"] == flow_branch:
                    flow_palace = PILLAR_PALACE_CN.get(pillar, "")
                    break
            
            # 收集所有涉及的宫位
            all_palaces = set(target_palaces)
            if flow_palace:
                all_palaces.add(flow_palace)
            palaces = sorted(list(all_palaces))
            
            if len(palaces) >= 2:
                # 多个宫位被冲，两两组合打印
                for i in range(len(palaces)):
                    for j in range(i + 1, len(palaces)):
                        palace1 = palaces[i]
                        palace2 = palaces[j]
                        explanation = _get_clash_explanation(palace1, palace2)
                        # 格式：宫位A-宫位B 地支字冲 解释（如果有）
                        clash_text = f"{palace1}-{palace2} {flow_branch}{target_branch}冲"
                        if explanation:
                            issues.append(f"{clash_text} {explanation}")
                        else:
                            issues.append(clash_text)
            elif len(palaces) == 1:
                # 只有一个宫位（理论上不应该出现，但保留兼容）
                issues.append(f"{palaces[0]} {flow_branch}{target_branch}冲")
    
    # 打印原局刑
    # 对于自刑，需要收集所有自刑地支，然后两两组合打印
    self_punish_processed = set()  # 记录已处理的自刑地支，避免重复打印
    
    for punish in natal_punishments:
        targets = punish.get("targets", [])
        if targets:
            flow_branch = punish.get("flow_branch", "")
            target_branch = punish.get("target_branch", "")
            # 不再检查risk，只要存在就打印
            # 如果是自刑（flow_branch == target_branch），需要找到所有包含该地支的柱，然后两两组合打印
            if flow_branch == target_branch:
                # 检查是否已经处理过这个自刑地支
                if flow_branch in self_punish_processed:
                    continue  # 跳过，已经处理过
                self_punish_processed.add(flow_branch)
                
                # 自刑：找到所有包含该地支的柱
                involved_pillars = []
                for pillar in ("year", "month", "day", "hour"):
                    if bazi[pillar]["zhi"] == flow_branch:
                        involved_pillars.append(pillar)
                
                # 自刑应该至少有两个柱，两两组合打印
                if len(involved_pillars) >= 2:
                    # 两两组合：年-月、年-日、年-时、月-日、月-时、日-时
                    for i in range(len(involved_pillars)):
                        for j in range(i + 1, len(involved_pillars)):
                            pillar1 = involved_pillars[i]
                            pillar2 = involved_pillars[j]
                            palace1 = PILLAR_PALACE_CN.get(pillar1, "")
                            palace2 = PILLAR_PALACE_CN.get(pillar2, "")
                            # 检查是否是祖上宫-婚姻宫 刑（不区分顺序）
                            palace_pair = frozenset([palace1, palace2])
                            is_zu_shang_marriage = palace_pair == frozenset(["祖上宫", "婚姻宫"])
                            # 格式：宫位A-宫位B 地支字自刑 [解释]
                            punish_text = f"{palace1}-{palace2} {flow_branch}{target_branch}自刑"
                            if is_zu_shang_marriage:
                                punish_text += " 成长过程中波折较多，压力偏大"
                            issues.append(punish_text)
                else:
                    # 如果只找到一个柱，使用原来的逻辑
                    target_palace = PILLAR_PALACE_CN.get(targets[0].get("pillar", ""), "")
                    issues.append(f"{target_palace} {flow_branch}{target_branch}自刑")
            else:
                # 非自刑：使用原来的逻辑
                target_palace = PILLAR_PALACE_CN.get(targets[0].get("pillar", ""), "")
                # 找到flow_branch对应的柱
                flow_pillar = None
                target_pillar = targets[0].get("pillar", "")
                for pillar in ("year", "month", "day", "hour"):
                    if bazi[pillar]["zhi"] == flow_branch and pillar != target_pillar:
                        flow_pillar = pillar
                        break
                flow_palace = PILLAR_PALACE_CN.get(flow_pillar, "") if flow_pillar else ""
                # 检查是否是祖上宫-婚姻宫 刑（不区分顺序）
                palace_pair = frozenset([flow_palace, target_palace])
                is_zu_shang_marriage = palace_pair == frozenset(["祖上宫", "婚姻宫"])
                # 格式：宫位A-宫位B 地支字刑 [解释]
                punish_text = f"{flow_palace}-{target_palace} {flow_branch}{target_branch}刑"
                if is_zu_shang_marriage:
                    punish_text += " 成长过程中波折较多，压力偏大"
                issues.append(punish_text)
    
    # 打印原局天克地冲（不再打印，因为天克地冲已经包含在冲里了）
    # 注释掉，因为用户要求只打印冲和刑，天克地冲应该已经包含在冲里了
    # for tkdc in natal_tkdc:
    #     palace1 = PILLAR_PALACE_CN.get(tkdc.get("pillar1", ""), "")
    #     palace2 = PILLAR_PALACE_CN.get(tkdc.get("pillar2", ""), "")
    #     issues.append(f"{palace1}-{palace2} 天克地冲")
    
    # 打印原局模式（不再打印，用户要求只打印冲和刑）
    # for pattern_group in natal_patterns:
    #     ...
    
    if issues:
        print("\n—— 原局问题 ——")
        for issue in issues:
            print(issue)
    
    # ===== 大运转折点汇总 =====
    # 使用 analyze_complete 返回的 turning_points（已结构化，无需重复计算）
    # 打印大运转折点汇总
    print("\n— 大运转折点 —")
    if turning_points:
        for tp in turning_points:
            print(f"{tp['year']} 年：{tp['from_state']} → {tp['to_state']}（{tp['change_type']}）")
    else:
        print("无转折点")
    
    # ===== 用神互换区间汇总 =====
    # 收集用神互换信息（复用现有判断逻辑）
    from .yongshen_swap import should_print_yongshen_swap_hint
    
    # 获取 strength_percent 和 support_percent（从 result 中获取）
    strength_percent_for_swap = result.get("strength_percent", 50.0)
    support_percent_for_swap = result.get("support_percent", 0.0)
    
    swap_events: List[Dict[str, Any]] = []
    for idx, group in enumerate(luck["groups"]):
        dy = group.get("dayun")
        # 大运开始之前的流年组，dayun 为 None，跳过互换判断
        if dy is None:
            continue
        
        dayun_zhi = dy.get("zhi", "")
        start_year = dy.get("start_year")
        
        # 复用现有的互换判断逻辑
        hint_info = should_print_yongshen_swap_hint(
            day_gan=day_gan,
            strength_percent=strength_percent_for_swap,
            support_percent=support_percent_for_swap,
            yongshen_elements=yong,
            dayun_zhi=dayun_zhi,
        )
        
        if hint_info:
            # 获取下一步大运的起运年份（用于计算区间终点）
            next_start_year = None
            if idx + 1 < len(luck["groups"]):
                next_group = luck["groups"][idx + 1]
                next_dy = next_group.get("dayun")
                if next_dy:
                    next_start_year = next_dy.get("start_year")
            
            swap_events.append({
                "start_year": start_year,
                "next_start_year": next_start_year,
                "target_industry": hint_info.get("target_industry", ""),  # 例如 "金、水" 或 "木、火"
            })
    
    # 合并连续触发的大运成区间
    merged_intervals: List[Dict[str, Any]] = []
    if swap_events:
        # 按顺序遍历，合并连续触发的大运
        current_interval_start = None
        current_interval_target = None
        last_swap_event = None
        
        for swap in swap_events:
            if current_interval_start is None:
                # 开始新区间
                current_interval_start = swap["start_year"]
                current_interval_target = swap["target_industry"]
                last_swap_event = swap
            else:
                # 检查是否连续（当前大运的起运年应该等于前一个大运的下一步起运年）
                if last_swap_event["next_start_year"] and swap["start_year"] == last_swap_event["next_start_year"]:
                    # 连续触发，继续当前区间
                    last_swap_event = swap
                else:
                    # 不连续，结束当前区间，开始新区间
                    # 计算当前区间的终点
                    end_year = None
                    if last_swap_event["next_start_year"]:
                        end_year = last_swap_event["next_start_year"] - 1
                    else:
                        # 最后一步大运，使用 start_year + 9 兜底
                        end_year = last_swap_event["start_year"] + 9
                    
                    merged_intervals.append({
                        "start_year": current_interval_start,
                        "end_year": end_year,
                        "target_industry": current_interval_target,
                    })
                    
                    # 开始新区间
                    current_interval_start = swap["start_year"]
                    current_interval_target = swap["target_industry"]
                    last_swap_event = swap
        
        # 处理最后一个区间
        if current_interval_start is not None:
            end_year = None
            if last_swap_event["next_start_year"]:
                end_year = last_swap_event["next_start_year"] - 1
            else:
                # 最后一步大运，使用 start_year + 9 兜底
                end_year = last_swap_event["start_year"] + 9
            
            merged_intervals.append({
                "start_year": current_interval_start,
                "end_year": end_year,
                "target_industry": current_interval_target,
            })
    
    # 打印用神互换区间汇总（只有当存在至少一段触发区间时才打印）
    if merged_intervals:
        print("\n—— 用神互换 ——")
        for interval in merged_intervals:
            start_year = interval["start_year"]
            end_year = interval["end_year"]
            target_industry = interval["target_industry"]
            print(f"{start_year}-{end_year}年：{target_industry}")
    
    # ===== 婚恋结构提示 =====
    from .shishen import get_shishen, get_branch_main_gan, get_shishen_label, get_branch_shishen
    
    day_gan = bazi["day"]["gan"]
    marriage_hint = None
    
    if not is_male:
        # 女命：检查官杀混杂
        gan_shishens = []  # 天干十神列表
        zhi_shishens = []  # 地支主气十神列表
        
        # 检查天干（年/月/日/时干，不包括日干自己）
        for pillar in ("year", "month", "hour"):
            gan = bazi[pillar]["gan"]
            ss = get_shishen(day_gan, gan)
            if ss:
                gan_shishens.append(ss)
        
        # 检查地支主气（年/月/日/时支）
        for pillar in ("year", "month", "day", "hour"):
            zhi = bazi[pillar]["zhi"]
            main_gan = get_branch_main_gan(zhi)
            if main_gan:
                ss = get_shishen(day_gan, main_gan)
                if ss:
                    zhi_shishens.append(ss)
        
        # 检查天干中是否同时出现正官和七杀
        gan_has_zhengguan = "正官" in gan_shishens
        gan_has_qisha = "七杀" in gan_shishens
        if gan_has_zhengguan and gan_has_qisha:
            marriage_hint = "官杀混杂"
        
        # 检查地支主气中是否同时出现正官和七杀
        zhi_has_zhengguan = "正官" in zhi_shishens
        zhi_has_qisha = "七杀" in zhi_shishens
        if zhi_has_zhengguan and zhi_has_qisha:
            marriage_hint = "官杀混杂"
    else:
        # 男命：检查正偏财混杂
        gan_shishens = []  # 天干十神列表
        zhi_shishens = []  # 地支主气十神列表
        
        # 检查天干（年/月/日/时干，不包括日干自己）
        for pillar in ("year", "month", "hour"):
            gan = bazi[pillar]["gan"]
            ss = get_shishen(day_gan, gan)
            if ss:
                gan_shishens.append(ss)
        
        # 检查地支主气（年/月/日/时支）
        for pillar in ("year", "month", "day", "hour"):
            zhi = bazi[pillar]["zhi"]
            main_gan = get_branch_main_gan(zhi)
            if main_gan:
                ss = get_shishen(day_gan, main_gan)
                if ss:
                    zhi_shishens.append(ss)
        
        # 检查天干中是否同时出现正财和偏财
        gan_has_zhengcai = "正财" in gan_shishens
        gan_has_piancai = "偏财" in gan_shishens
        if gan_has_zhengcai and gan_has_piancai:
            marriage_hint = "正偏财混杂"
        
        # 检查地支主气中是否同时出现正财和偏财
        zhi_has_zhengcai = "正财" in zhi_shishens
        zhi_has_piancai = "偏财" in zhi_shishens
        if zhi_has_zhengcai and zhi_has_piancai:
            marriage_hint = "正偏财混杂"
    
    # ===== 婚恋结构（独立 section，板块 + 列表） =====
    marriage_structure_list = []
    
    # 1. 混杂提示（如果有）
    if marriage_hint:
        marriage_structure_list.append(f"{marriage_hint}，桃花多，易再婚，找不对配偶难走下去")
    
    # 2. 从 natal 的 hints 中读取五合提醒（原局层），去掉"婚恋结构提示："前缀
    natal_hints = result.get("hints", [])
    for hint in natal_hints:
        if "婚恋结构提示：" in hint:
            # 去掉前缀，只保留内容
            content = hint.replace("婚恋结构提示：", "").strip()
            if content:
                marriage_structure_list.append(content)
    
    # 打印婚恋结构 section
    if marriage_structure_list:
        print("\n—— 婚恋结构 ——")
        for line in marriage_structure_list:
            print(line)

    # ===== 大运 / 流年 运势 + 冲信息 =====
    # 使用 analyze_complete 返回的 luck 数据（已结构化）

    print("\n======== 大运 & 流年（按大运分组） ========\n")

    # 获取生扶力量和身强/身弱信息（用于用神互换提示）
    support_percent = result.get("support_percent", 0.0)
    strength_percent = result.get("strength_percent", 50.0)
    day_gan = bazi["day"]["gan"]
    
    # 用于标记“转折点大运”（只看大运地支的好运/一般变化）
    prev_dayun_zhi_good: Optional[bool] = None

    # ===== 打印所有大运信息 =====
    for group in luck["groups"]:
        dy = group.get("dayun")
        lns = group.get("liunian", [])

        # 初始化缓冲区
        header_lines: List[str] = []
        fact_lines: List[str] = []
        axis_lines: List[str] = []  # 主轴/天干区（原tone_lines）
        tip_lines: List[str] = []

        # ===== 处理大运开始之前的流年 =====
        if dy is None:
            # 大运开始之前，只打印流年，不打印大运信息
            print("    —— 大运开始之前的流年 ——")
            for ln in lns:
                # 计算年度标题行（新逻辑）
                total_risk = ln.get("total_risk_percent", 0.0)
                risk_from_gan = ln.get("risk_from_gan", 0.0)
                risk_from_zhi = ln.get("risk_from_zhi", 0.0)
                gan_element = ln.get("gan_element", "")
                zhi_element = ln.get("zhi_element", "")
                is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
                is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
                
                title_line, should_print_suggestion = _calc_year_title_line(
                    total_risk, risk_from_gan, risk_from_zhi,
                    is_gan_yongshen, is_zhi_yongshen
                )
                
                print(
                    f"    {ln['year']} 年 {ln['gan']}{ln['zhi']}（虚龄 {ln['age']} 岁）：{title_line}"
                )
                
                # 打印流年事件（与大运下的流年相同的逻辑，但没有大运相关信息）
                # 流年六合 / 半合
                liunian_lines = []
                for ev in ln.get("harmonies_natal", []) or []:
                    if ev.get("type") != "branch_harmony":
                        continue
                    subtype = ev.get("subtype")
                    if subtype not in ("liuhe", "banhe"):
                        continue
                    flow_branch = ev.get("flow_branch", ln.get("zhi", ""))
                    for t in ev.get("targets", []):
                        palace = t.get("palace", "")
                        target_branch = t.get("target_branch", "")
                        if not palace or not target_branch:
                            continue
                        if subtype == "liuhe":
                            pair_str = f"{flow_branch}{target_branch}合"
                            line = f"        流年和{palace}合（{pair_str}）"
                        else:
                            matched = ev.get("matched_branches", [])
                            if len(matched) >= 2:
                                pair_str = f"{matched[0]}{matched[1]}半合"
                            else:
                                pair_str = f"{flow_branch}{target_branch}半合"
                            line = f"        流年 与 {palace} 半合（{pair_str}）"
                        liunian_lines.append((line, palace))
                
                if liunian_lines:
                    seen_lines = {}
                    for line, palace in liunian_lines:
                        key = (line, palace)
                        if key not in seen_lines:
                            seen_lines[key] = palace
                    sorted_items = sorted(seen_lines.items(), key=lambda x: x[0])
                    for (line, _), palace in sorted_items:
                        print(line)
                
                # 流年完整三合局（没有大运参与）
                for ev in ln.get("sanhe_complete", []) or []:
                    if ev.get("subtype") != "sanhe":
                        continue
                    sources = ev.get("sources", [])
                    if not sources:
                        continue
                    parts = []
                    matched_branches = ev.get("matched_branches", [])
                    for zhi in matched_branches:
                        zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                        zhi_parts = []
                        for src in zhi_sources:
                            src_type = src.get("source_type")
                            if src_type == "liunian":
                                zhi_parts.append(f"流年 {zhi}")
                            elif src_type == "natal":
                                pillar_name = src.get("pillar_name", "")
                                palace = src.get("palace", "")
                                if pillar_name and palace:
                                    zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                                elif pillar_name:
                                    zhi_parts.append(f"{pillar_name}{zhi}")
                        if zhi_parts:
                            for zp in zhi_parts:
                                parts.append(zp)
                    group = ev.get("group", "")
                    matched_str = "".join(matched_branches)
                    parts.append(f"{matched_str}三合{group}")
                    result = "，".join(parts)
                    print(f"        {result}。")
                
                # 流年完整三会局（没有大运参与）
                for ev in ln.get("sanhui_complete", []) or []:
                    if ev.get("subtype") != "sanhui":
                        continue
                    sources = ev.get("sources", [])
                    if not sources:
                        continue
                    parts = []
                    matched_branches = ev.get("matched_branches", [])
                    for zhi in matched_branches:
                        zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                        zhi_parts = []
                        for src in zhi_sources:
                            src_type = src.get("source_type")
                            if src_type == "liunian":
                                zhi_parts.append(f"流年 {zhi}")
                            elif src_type == "natal":
                                pillar_name = src.get("pillar_name", "")
                                palace = src.get("palace", "")
                                if pillar_name and palace:
                                    zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                                elif pillar_name:
                                    zhi_parts.append(f"{pillar_name}{zhi}")
                        if zhi_parts:
                            for zp in zhi_parts:
                                parts.append(zp)
                    group = ev.get("group", "")
                    matched_str = "".join(matched_branches)
                    parts.append(f"{matched_str}三会{group.replace('会', '局')}")
                    result = " ".join(parts)
                    print(f"        {result}。")
                
                # 流年天干五合（没有大运参与）
                liunian_gan = ln.get("gan", "")
                if liunian_gan:
                    from .gan_wuhe import GanPosition, detect_gan_wuhe, format_gan_wuhe_event
                    gan_shishen = get_shishen(day_gan, liunian_gan) if liunian_gan else None
                    liunian_shishen = gan_shishen or "-"
                    liunian_gan_positions = []
                    pillar_labels_liunian = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
                    for pillar in ["year", "month", "day", "hour"]:
                        gan = bazi[pillar]["gan"]
                        shishen = get_shishen(day_gan, gan) or "-"
                        liunian_gan_positions.append(GanPosition(
                            source="natal",
                            label=pillar_labels_liunian[pillar],
                            gan=gan,
                            shishen=shishen
                        ))
                    # 大运开始之前，没有大运天干
                    liunian_gan_positions.append(GanPosition(
                        source="liunian",
                        label="流年天干",
                        gan=liunian_gan,
                        shishen=liunian_shishen
                    ))
                    liunian_wuhe_events = detect_gan_wuhe(liunian_gan_positions)
                    if liunian_wuhe_events:
                        for ev in liunian_wuhe_events:
                            liunian_involved = any(pos.source == "liunian" for pos in ev["many_side"] + ev["few_side"])
                            if liunian_involved:
                                line = format_gan_wuhe_event(ev, incoming_shishen=liunian_shishen)
                                print(f"        {line}")
                
                # 冲摘要
                allowed_palaces = {"婚姻宫", "夫妻宫", "事业家庭宫（工作 / 子女 / 后期家庭）"}
                palace_name_map = {
                    "婚姻宫": "婚姻宫",
                    "夫妻宫": "夫妻宫",
                    "事业家庭宫（工作 / 子女 / 后期家庭）": "事业家庭宫"
                }
                clash_summary_lines = []
                for ev in ln.get("clashes_natal", []) or []:
                    if not ev:
                        continue
                    flow_branch = ev.get("flow_branch", "")
                    target_branch = ev.get("target_branch", "")
                    if not flow_branch or not target_branch:
                        continue
                    hit_palaces = []
                    targets = ev.get("targets", [])
                    for target in targets:
                        palace = target.get("palace", "")
                        if palace in allowed_palaces:
                            simple_palace = palace_name_map.get(palace, palace)
                            hit_palaces.append(simple_palace)
                    if hit_palaces:
                        palace_order = {"婚姻宫": 0, "夫妻宫": 1, "事业家庭宫": 2}
                        hit_palaces_sorted = sorted(hit_palaces, key=lambda p: palace_order.get(p, 99))
                        palace_str = "/".join(hit_palaces_sorted)
                        clash_name = f"{flow_branch}{target_branch}冲"
                        clash_summary_lines.append((clash_name, palace_str))
                
                if clash_summary_lines:
                    clash_groups = {}
                    for clash_name, palace_str in clash_summary_lines:
                        if clash_name not in clash_groups:
                            clash_groups[clash_name] = set()
                        clash_groups[clash_name].add(palace_str)
                    for clash_name in sorted(clash_groups.keys()):
                        all_palaces = set()
                        for palace_str in clash_groups[clash_name]:
                            all_palaces.update(palace_str.split("/"))
                        palace_order = {"婚姻宫": 0, "夫妻宫": 1, "事业家庭宫": 2}
                        sorted_palaces = sorted(all_palaces, key=lambda p: palace_order.get(p, 99))
                        palace_str = "/".join(sorted_palaces)
                        print(f"        冲：{clash_name}（{palace_str}）")
                
                # 检查时柱天克地冲
                has_hour_tkdc = False
                hour_tkdc_info = None
                for ev_clash in ln.get("clashes_natal", []) or []:
                    if not ev_clash:
                        continue
                    tkdc_targets = ev_clash.get("tkdc_targets", [])
                    if tkdc_targets:
                        flow_branch = ev_clash.get("flow_branch", "")
                        flow_gan = ev_clash.get("flow_gan", "")
                        for target in tkdc_targets:
                            if target.get("pillar") == "hour":
                                has_hour_tkdc = True
                                target_gan = target.get("target_gan", "")
                                target_branch = ev_clash.get("target_branch", "")
                                hour_tkdc_info = {
                                    "liunian_ganzhi": f"{flow_gan}{flow_branch}",
                                    "hour_ganzhi": f"{target_gan}{target_branch}"
                                }
                                break
                    if has_hour_tkdc:
                        break
                
                if has_hour_tkdc and hour_tkdc_info:
                    print(f"        天克地冲：流年 {hour_tkdc_info['liunian_ganzhi']} ↔ 时柱 {hour_tkdc_info['hour_ganzhi']}")
                
                print()
                
                # 提示汇总区
                liunian_hints = ln.get("hints", [])

                # 收集模式提示（伤官见官/枭神夺食）
                all_events_for_hints = ln.get("all_events", [])
                static_events_for_hints = [ev for ev in all_events_for_hints if ev.get("type") in (
                    "static_clash_activation", "static_punish_activation", "pattern_static_activation", "static_tkdc_activation"
                )]
                clashes_natal_for_hints = ln.get("clashes_natal", []) or []
                pattern_hints = _generate_pattern_hints(all_events_for_hints, static_events_for_hints, clashes_natal_for_hints)

                # 收集天克地冲提示（排除年柱、时柱）
                clashes_dayun_for_hints = ln.get("clashes_dayun", []) or []
                tkdc_hint = _generate_tkdc_hint(clashes_natal_for_hints, clashes_dayun_for_hints, static_events_for_hints)

                # 收集时柱天克地冲提示
                hour_tkdc_hint = _generate_hour_tkdc_hint(clashes_natal_for_hints)

                # 收集时支冲提示
                liunian_zhi_for_hints = ln.get("zhi", "")
                hour_clash_hint = _generate_hour_clash_hint(bazi, liunian_zhi_for_hints)

                # 互斥规则：时柱天克地冲 > 时支被冲
                # 如果有时柱天克地冲，则不输出时支被冲
                if hour_tkdc_hint:
                    hour_clash_hint = ""  # 抑制时支被冲

                # 合并所有提示（顺序：伤官见官、枭神夺食、天克地冲、时柱天克地冲、时支被流年冲）
                all_hints = list(liunian_hints)
                all_hints.extend(pattern_hints)
                if tkdc_hint:
                    all_hints.append(tkdc_hint)
                if hour_tkdc_hint:
                    all_hints.append(hour_tkdc_hint)
                if hour_clash_hint:
                    all_hints.append(hour_clash_hint)

                if all_hints:
                    print("        提示汇总：")
                    for hint in all_hints:
                        print(f"        - {hint}")
                    print()

                # 危险系数块
                total_risk = ln.get("total_risk_percent", 0.0)
                risk_from_gan = ln.get("risk_from_gan", 0.0)
                risk_from_zhi = ln.get("risk_from_zhi", 0.0)
                tkdc_risk = ln.get("tkdc_risk_percent", 0.0)
                
                liunian_gan = ln.get("gan", "")
                liunian_zhi = ln.get("zhi", "")
                gan_shishen = get_shishen(day_gan, liunian_gan) if liunian_gan else None
                zhi_main_gan = get_branch_main_gan(liunian_zhi) if liunian_zhi else None
                zhi_shishen = get_shishen(day_gan, zhi_main_gan) if zhi_main_gan else None
                gan_label = get_shishen_label(gan_shishen, is_gan_yongshen) if gan_shishen else ""
                zhi_label = get_shishen_label(zhi_shishen, is_zhi_yongshen) if zhi_shishen else ""
                
                print(f"        --- 总危险系数：{total_risk:.1f}% ---")
                
                gan_yongshen_str = "是" if is_gan_yongshen else "否"
                if gan_shishen:
                    label_str = f"｜标签：{gan_label}" if gan_label else ""
                    print(f"        天干 {liunian_gan}｜十神 {gan_shishen}｜用神 {gan_yongshen_str}{label_str}")
                else:
                    print(f"        天干 {liunian_gan}｜十神 -｜用神 {gan_yongshen_str}")
                
                zhi_yongshen_str = "是" if is_zhi_yongshen else "否"
                if zhi_shishen:
                    label_str = f"｜标签：{zhi_label}" if zhi_label else ""
                    print(f"        地支 {liunian_zhi}｜十神 {zhi_shishen}｜用神 {zhi_yongshen_str}{label_str}")
                else:
                    print(f"        地支 {liunian_zhi}｜十神 -｜用神 {zhi_yongshen_str}")
                
                # 打印开始危险系数
                print(f"        - 开始危险系数（天干引起）：{risk_from_gan:.1f}%")

                # 打印后来危险系数
                print(f"        - 后来危险系数（地支引起）：{risk_from_zhi:.1f}%")
                
                # 打印天克地冲危险系数
                print(f"        - 天克地冲危险系数：{tkdc_risk:.1f}%")
                print("")
                
                # 组织所有事件
                all_events = ln.get("all_events", [])
                gan_events = []
                zhi_events = []
                static_events = []
                
                for ev in all_events:
                    ev_type = ev.get("type", "")
                    if ev_type in ("static_clash_activation", "static_punish_activation", "pattern_static_activation", "static_tkdc_activation"):
                        static_events.append(ev)
                    elif ev_type == "pattern":
                        kind = ev.get("kind", "")
                        if kind == "gan":
                            gan_events.append(ev)
                        elif kind == "zhi":
                            zhi_events.append(ev)
                    elif ev_type == "lineyun_bonus":
                        lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                        lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                        if lineyun_bonus_gan > 0.0:
                            gan_events.append(ev)
                        if lineyun_bonus_zhi > 0.0:
                            zhi_events.append(ev)
                    elif ev_type in ("branch_clash", "punishment"):
                        zhi_events.append(ev)
                
                # 打印开始事件（天干相关）
                has_gan_events = gan_events or any(ev.get("type") == "pattern_static_activation" and (ev.get("risk_from_gan", 0.0) > 0.0) for ev in static_events)

                if has_gan_events:
                    print("        开始事件（天干引起）：")
                    
                    # 收集所有动态天干模式，按类型分组
                    pattern_gan_dynamic = {}  # {pattern_type: [events]}
                    for ev in gan_events:
                        ev_type = ev.get("type", "")
                        if ev_type == "pattern":
                            pattern_type = ev.get("pattern_type", "")
                            if pattern_type not in pattern_gan_dynamic:
                                pattern_gan_dynamic[pattern_type] = []
                            pattern_gan_dynamic[pattern_type].append(ev)
                    
                    # 打印所有动态天干模式
                    for pattern_type, events in pattern_gan_dynamic.items():
                        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                        total_dynamic_risk = 0.0
                        for ev in events:
                            risk = ev.get("risk_percent", 0.0)
                            total_dynamic_risk += risk
                            print(f"          模式（天干层）：{pattern_name}，风险 {risk:.1f}%")
                        
                        # 打印对应的静态模式激活（如果有）
                        static_risk_gan = 0.0
                        for static_ev in static_events:
                            if static_ev.get("type") == "pattern_static_activation":
                                static_pattern_type = static_ev.get("pattern_type", "")
                                if static_pattern_type == pattern_type:
                                    static_risk_gan = static_ev.get("risk_from_gan", 0.0)
                                    if static_risk_gan > 0.0:
                                        print(f"          静态模式激活（天干）：{pattern_name}，风险 {static_risk_gan:.1f}%")
                                        break
                        
                        # 打印总和
                        total_pattern_risk = total_dynamic_risk + static_risk_gan
                        if total_pattern_risk > 0.0:
                            print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_gan:.1f}% = {total_pattern_risk:.1f}%")
                    
                    # 打印天干线运加成
                    for ev in gan_events:
                        ev_type = ev.get("type", "")
                        if ev_type == "lineyun_bonus":
                            lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                            if lineyun_bonus_gan > 0.0:
                                print(f"          线运加成（天干）：{lineyun_bonus_gan:.1f}%")
                    
                    print("")
                
                # 打印后来事件（地支相关）
                has_zhi_events = zhi_events or any(ev.get("type") in ("static_clash_activation", "static_punish_activation") or (ev.get("type") == "pattern_static_activation" and ev.get("risk_from_zhi", 0.0) > 0.0) for ev in static_events)
                # 检查是否有冲或刑（大运开始之前，只有流年与命局的冲）
                if ln.get("clashes_natal"):
                    has_zhi_events = True

                if has_zhi_events:
                    print("        后来事件（地支引起）：")
                    
                    # 先打印所有动态冲
                    total_clash_dynamic = 0.0
                    from .config import PILLAR_PALACE
                    sanhe_sanhui_bonus_printed = False  # 标记是否已打印三合/三会逢冲额外加分
                    
                    # 流年与命局的冲（大运开始之前，没有运年相冲）
                    for ev in ln.get("clashes_natal", []):
                        if not ev:
                            continue
                        flow_branch = ev.get("flow_branch", "")
                        target_branch = ev.get("target_branch", "")
                        base_power = ev.get("base_power_percent", 0.0)
                        grave_bonus = ev.get("grave_bonus_percent", 0.0)
                        clash_risk_zhi = base_power + grave_bonus
                        if clash_risk_zhi > 0.0:
                            total_clash_dynamic += clash_risk_zhi
                            targets = ev.get("targets", [])
                            target_info = []
                            for target in targets:
                                target_pillar = target.get("pillar", "")
                                palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                                pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                                target_info.append(f"{pillar_name}（{palace}）")
                            target_str = "、".join(target_info)
                            print(f"          冲：流年 {flow_branch} 冲 命局{target_str} {target_branch}，风险 {clash_risk_zhi:.1f}%")
                            
                            # 检查这个冲是否触发三合/三会逢冲额外加分（只打印一次）
                            if not sanhe_sanhui_bonus_printed:
                                sanhe_sanhui_bonus_ev = ln.get("sanhe_sanhui_clash_bonus_event")
                                if sanhe_sanhui_bonus_ev:
                                    bonus_flow = sanhe_sanhui_bonus_ev.get("flow_branch", "")
                                    bonus_target = sanhe_sanhui_bonus_ev.get("target_branch", "")
                                    # 检查是否匹配当前冲
                                    if (bonus_flow == flow_branch and bonus_target == target_branch) or \
                                       (bonus_flow == target_branch and bonus_target == flow_branch):
                                        _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev)
                                        sanhe_sanhui_bonus_printed = True

                            # 检查这个冲是否与模式重叠（伤官见官/枭神夺食）
                            if ev.get("is_pattern_overlap"):
                                overlap_pattern = ev.get("overlap_pattern_type", "")
                                pattern_bonus = ev.get("pattern_bonus_percent", 0.0)
                                if overlap_pattern == "hurt_officer":
                                    print(f"          伤官见官（地支层）：与冲同时出现，风险 {pattern_bonus:.1f}%")
                                elif overlap_pattern == "pianyin_eatgod":
                                    print(f"          枭神夺食（地支层）：与冲同时出现，风险 {pattern_bonus:.1f}%")

                    # 打印静态冲激活（如果有）
                    static_clash_risk = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "static_clash_activation":
                            static_clash_risk = static_ev.get("risk_percent", 0.0)
                            if static_clash_risk > 0.0:
                                print(f"          静态冲激活：风险 {static_clash_risk:.1f}%")
                                break
                    
                    # 打印冲的总和（包含三合/三会逢冲额外加分）
                    sanhe_sanhui_bonus_for_clash = ln.get("sanhe_sanhui_clash_bonus", 0.0)
                    if total_clash_dynamic > 0.0 or static_clash_risk > 0.0 or sanhe_sanhui_bonus_for_clash > 0.0:
                        total_clash = total_clash_dynamic + static_clash_risk + sanhe_sanhui_bonus_for_clash
                        parts = []
                        if total_clash_dynamic > 0.0:
                            parts.append(f"动态 {total_clash_dynamic:.1f}%")
                        if static_clash_risk > 0.0:
                            parts.append(f"静态 {static_clash_risk:.1f}%")
                        if sanhe_sanhui_bonus_for_clash > 0.0:
                            parts.append(f"三合/三会逢冲 {sanhe_sanhui_bonus_for_clash:.1f}%")
                        parts_str = " + ".join(parts)
                        print(f"          冲总影响：{parts_str} = {total_clash:.1f}%")
                    
                    # 先打印所有动态刑
                    total_punish_dynamic = 0.0
                    for ev in zhi_events:
                        ev_type = ev.get("type", "")
                        if ev_type == "punishment":
                            risk = ev.get("risk_percent", 0.0)
                            total_punish_dynamic += risk
                            flow_branch = ev.get("flow_branch", "")
                            target_branch = ev.get("target_branch", "")
                            targets = ev.get("targets", [])
                            target_info = []
                            for target in targets:
                                target_pillar = target.get("pillar", "")
                                palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                                pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                                target_info.append(f"{pillar_name}（{palace}）")
                            target_str = "、".join(target_info)
                            print(f"          刑：{flow_branch} 刑 {target_str} {target_branch}，风险 {risk:.1f}%")
                    
                    # 打印静态刑激活（如果有）
                    static_punish_risk = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "static_punish_activation":
                            static_punish_risk = static_ev.get("risk_percent", 0.0)
                            if static_punish_risk > 0.0:
                                print(f"          静态刑激活：风险 {static_punish_risk:.1f}%")
                                break
                    
                    # 打印刑的总和
                    if total_punish_dynamic > 0.0 or static_punish_risk > 0.0:
                        total_punish = total_punish_dynamic + static_punish_risk
                        print(f"          刑总影响：动态 {total_punish_dynamic:.1f}% + 静态 {static_punish_risk:.1f}% = {total_punish:.1f}%")
                    
                    # 收集所有动态地支模式，按类型分组
                    pattern_zhi_dynamic = {}  # {pattern_type: [events]}
                    for ev in zhi_events:
                        ev_type = ev.get("type", "")
                        if ev_type == "pattern":
                            pattern_type = ev.get("pattern_type", "")
                            if pattern_type not in pattern_zhi_dynamic:
                                pattern_zhi_dynamic[pattern_type] = []
                            pattern_zhi_dynamic[pattern_type].append(ev)
                    
                    # 打印所有动态地支模式
                    for pattern_type, events in pattern_zhi_dynamic.items():
                        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                        total_dynamic_risk = 0.0
                        for ev in events:
                            risk = ev.get("risk_percent", 0.0)
                            total_dynamic_risk += risk
                            print(f"          模式（地支层）：{pattern_name}，风险 {risk:.1f}%")
                        
                        # 打印对应的静态模式激活（如果有）
                        static_risk_zhi = 0.0
                        for static_ev in static_events:
                            if static_ev.get("type") == "pattern_static_activation":
                                static_pattern_type = static_ev.get("pattern_type", "")
                                if static_pattern_type == pattern_type:
                                    static_risk_zhi = static_ev.get("risk_from_zhi", 0.0)
                                    if static_risk_zhi > 0.0:
                                        print(f"          静态模式激活（地支）：{pattern_name}，风险 {static_risk_zhi:.1f}%")
                                        break
                        
                        # 打印总和
                        total_pattern_risk = total_dynamic_risk + static_risk_zhi
                        if total_pattern_risk > 0.0:
                            print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_zhi:.1f}% = {total_pattern_risk:.1f}%")
                    
                    # 打印地支线运加成
                    for ev in zhi_events:
                        ev_type = ev.get("type", "")
                        if ev_type == "lineyun_bonus":
                            lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                            if lineyun_bonus_zhi > 0.0:
                                print(f"          线运加成（地支）：{lineyun_bonus_zhi:.1f}%")
                    
                    print("")
                
                # 打印天克地冲事件（单独列出）
                if tkdc_risk > 0.0:
                    print("        天克地冲事件：")
                    
                    # 检查流年与命局的冲中的天克地冲
                    for ev_clash in ln.get("clashes_natal", []):
                        if not ev_clash:
                            continue
                        tkdc_targets = ev_clash.get("tkdc_targets", [])
                        if tkdc_targets:
                            flow_branch = ev_clash.get("flow_branch", "")
                            flow_gan = ev_clash.get("flow_gan", "")
                            for target in tkdc_targets:
                                target_pillar = target.get("pillar", "")
                                target_gan = target.get("target_gan", "")
                                palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                                pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                                # 计算该柱的天克地冲加成
                                if target_pillar == "year":
                                    tkdc_per_pillar = 0.0  # 年柱不加成
                                elif target_pillar == "day":
                                    tkdc_per_pillar = 20.0  # 日柱20%
                                else:
                                    tkdc_per_pillar = 10.0  # 其他柱10%
                                if tkdc_per_pillar > 0.0:
                                    print(f"          天克地冲：流年 {flow_gan}{flow_branch} 与 命局{pillar_name}（{palace}）{target_gan}{ev_clash.get('target_branch', '')} 天克地冲，风险 {tkdc_per_pillar:.1f}%")
                    
                    # 打印静态天克地冲激活（大运开始之前，没有运年相冲）
                    for ev in static_events:
                        if ev.get("type") == "static_tkdc_activation":
                            risk_tkdc_static = ev.get("risk_from_gan", 0.0)  # 静态天克地冲全部计入tkdc_risk
                            if risk_tkdc_static > 0.0:
                                print(f"          静态天克地冲激活：风险 {risk_tkdc_static:.1f}%")
                    
                    print("")
                
                if should_print_suggestion:
                    print("        建议：买保险/不投机/守法/不轻易辞职/控制情绪/三思后行")
            
            # 跳过大运相关打印，继续下一个 group
            continue

        # ===== Header =====
        # 确保 dy 不为 None（防御性检查，虽然理论上不应该到达这里）
        if dy is None:
            continue
        
        # 大运判词：用神=好运，非用神=一般
        if dy.get("zhi_good", False):
            label = "好运"
        else:
            label = "一般"
        gan_flag = "✓" if dy["gan_good"] else "×"
        zhi_flag = "✓" if dy["zhi_good"] else "×"

        header_lines.append(
            f"【大运 {dy['index'] + 1}】 {dy['gan']}{dy['zhi']} "
            f"(起运年份 {dy['start_year']}, 虚龄 {dy['start_age']} 岁) → {label}  "
            f"[干 {dy['gan_element'] or '-'} {gan_flag} / "
            f"支 {dy['zhi_element'] or '-'} {zhi_flag}]"
        )
        
        # ===== 大运十神打印（方案A结构层级） =====
        dayun_gan = dy.get("gan", "")
        dayun_zhi = dy.get("zhi", "")
        
        # 计算大运天干十神和用神
        dayun_gan_shishen = get_shishen(day_gan, dayun_gan) if dayun_gan else None
        dayun_gan_element = dy.get("gan_element", "")
        dayun_gan_yongshen = dayun_gan_element in yongshen_elements if dayun_gan_element else False
        dayun_gan_label = get_shishen_label(dayun_gan_shishen, dayun_gan_yongshen) if dayun_gan_shishen else ""
        
        # 计算大运地支主气十神和用神
        dayun_zhi_main_gan = get_branch_main_gan(dayun_zhi) if dayun_zhi else None
        dayun_zhi_shishen = get_shishen(day_gan, dayun_zhi_main_gan) if dayun_zhi_main_gan else None
        dayun_zhi_element = dy.get("zhi_element", "")
        dayun_zhi_yongshen = dayun_zhi_element in yongshen_elements if dayun_zhi_element else False
        dayun_zhi_label = get_shishen_label(dayun_zhi_shishen, dayun_zhi_yongshen) if dayun_zhi_shishen else ""
        
        # ===== 事实区：大运六合（只解释，不计分） =====
        dayun_liuhe_lines = []
        dayun_banhe_lines = []
        for ev in dy.get("harmonies_natal", []) or []:
            if ev.get("type") != "branch_harmony":
                continue
            subtype = ev.get("subtype")
            flow_branch = ev.get("flow_branch", dy.get("zhi", ""))
            if subtype not in ("liuhe", "banhe"):
                continue
            for t in ev.get("targets", []):
                palace = t.get("palace", "")
                target_branch = t.get("target_branch", "")
                if not palace or not target_branch:
                    continue
                if subtype == "liuhe":
                    # 例如：大运和夫妻宫合（午未合）
                    line = f"    大运和{palace}合（{flow_branch}{target_branch}合）"
                    dayun_liuhe_lines.append(line)
                elif subtype == "banhe":
                    # 例如：大运 与 夫妻宫 半合（巳酉半合）
                    line = f"    大运 与 {palace} 半合（{flow_branch}{target_branch}半合）"
                    dayun_banhe_lines.append(line)
        if dayun_liuhe_lines:
            for line in sorted(set(dayun_liuhe_lines)):
                fact_lines.append(line)
        if dayun_banhe_lines:
            for line in sorted(set(dayun_banhe_lines)):
                fact_lines.append(line)
        
        # ===== 事实区：大运完整三合局 =====
        for ev in dy.get("sanhe_complete", []) or []:
            if ev.get("subtype") != "sanhe":
                continue
            sources = ev.get("sources", [])
            if not sources:
                continue
            
            # 构建输出句子
            parts = []
            
            # 按三合局的顺序列出每个字的来源
            matched_branches = ev.get("matched_branches", [])
            for zhi in matched_branches:
                zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                zhi_parts = []
                for src in zhi_sources:
                    src_type = src.get("source_type")
                    if src_type == "dayun":
                        zhi_parts.append(f"大运 {zhi}")
                    elif src_type == "liunian":
                        zhi_parts.append(f"流年 {zhi}")
                    elif src_type == "natal":
                        pillar_name = src.get("pillar_name", "")
                        palace = src.get("palace", "")
                        if pillar_name and palace:
                            zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                        elif pillar_name:
                            zhi_parts.append(f"{pillar_name}{zhi}")
                
                if zhi_parts:
                    # 如果同一字在多个位置出现，用"和"连接
                    if len(zhi_parts) > 1:
                        parts.append("和".join(zhi_parts))
                    else:
                        parts.append(zhi_parts[0])
            
            # 结尾：三合局名称
            group = ev.get("group", "")
            matched_str = "".join(matched_branches)
            parts.append(f"{matched_str}三合{group}")
            
            # 用逗号连接各部分
            result = "，".join(parts)
            fact_lines.append(f"    {result}。")
        
        # ===== 事实区：大运完整三会局 =====
        for ev in dy.get("sanhui_complete", []) or []:
            if ev.get("subtype") != "sanhui":
                continue
            sources = ev.get("sources", [])
            if not sources:
                continue
            
            # 构建输出句子
            parts = []
            
            # 按三会局的顺序列出每个字的来源
            matched_branches = ev.get("matched_branches", [])
            for zhi in matched_branches:
                zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                zhi_parts = []
                for src in zhi_sources:
                    src_type = src.get("source_type")
                    if src_type == "dayun":
                        zhi_parts.append(f"大运 {zhi}")
                    elif src_type == "liunian":
                        zhi_parts.append(f"流年 {zhi}")
                    elif src_type == "natal":
                        pillar_name = src.get("pillar_name", "")
                        palace = src.get("palace", "")
                        if pillar_name and palace:
                            zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                        elif pillar_name:
                            zhi_parts.append(f"{pillar_name}{zhi}")
                
                if zhi_parts:
                    # 如果同一字在多个位置出现，分别列出（不合并）
                    for zp in zhi_parts:
                        parts.append(zp)
            
            # 结尾：三会局名称
            group = ev.get("group", "")
            matched_str = "".join(matched_branches)
            parts.append(f"{matched_str}三会{group.replace('会', '局')}")
            
            # 用空格连接各部分（按regression格式）
            result = " ".join(parts)
            fact_lines.append(f"    {result}。")
        
        # ===== 事实区：大运天干五合（只识别+打印，不影响风险） =====
        dayun_gan = dy.get("gan", "")
        if dayun_gan:
            from .gan_wuhe import GanPosition, detect_gan_wuhe, format_gan_wuhe_event
            dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
            # 大运入口使用"年干"格式（不是"年柱天干"），且本行不再重复打印"大运6，庚辰大运"
            dayun_gan_positions = []
            pillar_labels_dayun = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
            for pillar in ["year", "month", "day", "hour"]:
                gan = bazi[pillar]["gan"]
                shishen = get_shishen(day_gan, gan) or "-"
                dayun_gan_positions.append(GanPosition(
                    source="natal",
                    label=pillar_labels_dayun[pillar],
                    gan=gan,
                    shishen=shishen
                ))
            dayun_gan_positions.append(GanPosition(
                source="dayun",
                label="大运天干",
                gan=dayun_gan,
                shishen=dayun_shishen
            ))
            dayun_wuhe_events = detect_gan_wuhe(dayun_gan_positions)
            if dayun_wuhe_events:
                for ev in dayun_wuhe_events:
                    # 只打印涉及大运天干的五合
                    dayun_involved = any(pos.source == "dayun" for pos in ev["many_side"] + ev["few_side"])
                    if dayun_involved:
                        # 行内只保留"年干，月干，时干 乙 争合 大运天干 庚 ..."
                        line = format_gan_wuhe_event(ev, incoming_shishen=dayun_shishen)
                        fact_lines.append(f"    {line}")
        
        # ===== 事实区：大运本身与命局的冲 =====
        for ev in dy.get("clashes_natal", []):
            if not ev:
                continue
            fact_lines.append("    命局冲（大运）：" + _format_clash_natal(ev))
            
            # 打印大运与命局天克地冲详细信息
            tkdc_targets = ev.get("tkdc_targets", [])
            if tkdc_targets:
                from .config import PILLAR_PALACE
                flow_branch = ev.get("flow_branch", "")
                flow_gan = ev.get("flow_gan", "")
                for target in tkdc_targets:
                    target_pillar = target.get("pillar", "")
                    target_gan = target.get("target_gan", "")
                    palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                    pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                    fact_lines.append(f"    天克地冲：大运 {flow_gan}{flow_branch} 与 命局{pillar_name}（{palace}）{target_gan}{ev.get('target_branch', '')} 天克地冲")
        
        # ===== 主轴区：大运主轴（地支定调） =====
        axis_lines.append("    大运主轴（地支定调）：")
        dayun_zhi_yongshen_str = "是" if dayun_zhi_yongshen else "否"
        if dayun_zhi_shishen:
            dayun_zhi_label_str = f"｜标签：{dayun_zhi_label}" if dayun_zhi_label else ""
            axis_lines.append(f"    地支 {dayun_zhi}｜十神 {dayun_zhi_shishen}｜用神 {dayun_zhi_yongshen_str}{dayun_zhi_label_str}")
        else:
            axis_lines.append(f"    地支 {dayun_zhi}｜十神 -｜用神 {dayun_zhi_yongshen_str}")
        
        # ===== 主轴区：天干补充（不翻盘） =====
        axis_lines.append("    天干补充（不翻盘）：")
        dayun_gan_yongshen_str = "是" if dayun_gan_yongshen else "否"
        if dayun_gan_shishen:
            dayun_gan_label_str = f"｜标签：{dayun_gan_label}" if dayun_gan_label else ""
            axis_lines.append(f"    天干 {dayun_gan}｜十神 {dayun_gan_shishen}｜用神 {dayun_gan_yongshen_str}{dayun_gan_label_str}")
        else:
            axis_lines.append(f"    天干 {dayun_gan}｜十神 -｜用神 {dayun_gan_yongshen_str}")

        # ===== 提示汇总区：转折点 =====
        current_zhi_good = dy.get("zhi_good", False)
        if prev_dayun_zhi_good is not None and prev_dayun_zhi_good != current_zhi_good:
            start_year = dy.get("start_year")
            if prev_dayun_zhi_good and not current_zhi_good:
                from_state, to_state, change_type = "好运", "一般", "转弱"
            else:
                from_state, to_state, change_type = "一般", "好运", "转好"
            tip_lines.append(f"    这是大运转折点：{start_year} 年：{from_state} → {to_state}（{change_type}）")
        prev_dayun_zhi_good = current_zhi_good
        
        # ===== 提示汇总区：用神互换提示（从 hints 读取，唯一真相源） =====
        dayun_hints = dy.get("hints", [])
        for hint in dayun_hints:
            if "【用神互换提示】" in hint:
                tip_lines.append(f"    {hint}")
        
        # ===== 提示汇总区：天干五合争合/双合婚恋提醒（大运层，从 hints 读取） =====
        dayun_hints = dy.get("hints", [])
        for hint in dayun_hints:
            if "婚恋变化提醒" in hint:
                tip_lines.append(f"    {hint}")
        
        # ===== 按顺序打印所有内容 =====
        for line in header_lines:
            print(line)
        for line in fact_lines:
            print(line)
        # 分隔线（在事实区之后、主轴区之前）
        if fact_lines:  # 如果事实区有内容，打印分隔线
            print("    ——————————")
        for line in axis_lines:
            print(line)
        for line in tip_lines:
            print(line)

        # 该大运下面的十个流年
        print("    —— 该大运对应的流年 ——")
        for ln in lns:
            # 计算年度标题行（新逻辑）
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            gan_element = ln.get("gan_element", "")
            zhi_element = ln.get("zhi_element", "")
            is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
            is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
            
            title_line, should_print_suggestion = _calc_year_title_line(
                total_risk, risk_from_gan, risk_from_zhi,
                is_gan_yongshen, is_zhi_yongshen
            )
            
            print(
                f"    {ln['year']} 年 {ln['gan']}{ln['zhi']}（虚龄 {ln['age']} 岁）：{title_line}"
            )
            
            # 流年六合 / 半合（只解释，不计分）：流年支与原局四宫位
            liunian_lines = []
            # 记录已提示的宫位（同一年同一宫位只提示一次）
            # 提示已从 hints 读取，不再在此处生成
            
            for ev in ln.get("harmonies_natal", []) or []:
                if ev.get("type") != "branch_harmony":
                    continue
                subtype = ev.get("subtype")
                if subtype not in ("liuhe", "banhe"):
                    continue
                flow_branch = ev.get("flow_branch", ln.get("zhi", ""))
                for t in ev.get("targets", []):
                    palace = t.get("palace", "")
                    target_branch = t.get("target_branch", "")
                    if not palace or not target_branch:
                        continue
                    if subtype == "liuhe":
                        # 例如：流年和婚姻宫合（辰酉合）
                        pair_str = f"{flow_branch}{target_branch}合"
                        line = f"        流年和{palace}合（{pair_str}）"
                    else:
                        # 例如：流年 与 祖上宫 半合（巳酉半合）
                        matched = ev.get("matched_branches", [])
                        if len(matched) >= 2:
                            pair_str = f"{matched[0]}{matched[1]}半合"
                        else:
                            pair_str = f"{flow_branch}{target_branch}半合"
                        line = f"        流年 与 {palace} 半合（{pair_str}）"
                    liunian_lines.append((line, palace))
            
            # 打印事件行，并在婚姻宫/夫妻宫命中时追加提示
            if liunian_lines:
                # 去重：使用字典记录每个(line, palace)组合，保留第一次出现的
                seen_lines = {}
                for line, palace in liunian_lines:
                    key = (line, palace)
                    if key not in seen_lines:
                        seen_lines[key] = palace
                
                # 按行文本排序后打印（事件行，提示从 hints 读取）
                sorted_items = sorted(seen_lines.items(), key=lambda x: x[0])
                for (line, _), palace in sorted_items:
                    print(line)
            
            # 流年完整三合局（包括大运+流年+原局的情况）
            for ev in ln.get("sanhe_complete", []) or []:
                if ev.get("subtype") != "sanhe":
                    continue
                sources = ev.get("sources", [])
                if not sources:
                    continue
                
                # 构建输出句子
                parts = []
                
                # 按三合局的顺序列出每个字的来源
                matched_branches = ev.get("matched_branches", [])
                for zhi in matched_branches:
                    zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                    zhi_parts = []
                    for src in zhi_sources:
                        src_type = src.get("source_type")
                        if src_type == "dayun":
                            zhi_parts.append(f"大运 {zhi}")
                        elif src_type == "liunian":
                            zhi_parts.append(f"流年 {zhi}")
                        elif src_type == "natal":
                            pillar_name = src.get("pillar_name", "")
                            palace = src.get("palace", "")
                            if pillar_name and palace:
                                zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                            elif pillar_name:
                                zhi_parts.append(f"{pillar_name}{zhi}")
                    
                    if zhi_parts:
                        # 如果同一字在多个位置出现，分别列出（不合并），用逗号分隔
                        for zp in zhi_parts:
                            parts.append(zp)
                
                # 结尾：三合局名称
                group = ev.get("group", "")
                matched_str = "".join(matched_branches)
                parts.append(f"{matched_str}三合{group}")
                
                # 用逗号连接各部分
                result = "，".join(parts)
                print(f"        {result}。")
            
            # 流年完整三会局（包括大运+流年+原局的情况）
            for ev in ln.get("sanhui_complete", []) or []:
                if ev.get("subtype") != "sanhui":
                    continue
                sources = ev.get("sources", [])
                if not sources:
                    continue
                
                # 构建输出句子
                parts = []
                
                # 按三会局的顺序列出每个字的来源
                matched_branches = ev.get("matched_branches", [])
                for zhi in matched_branches:
                    zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                    zhi_parts = []
                    for src in zhi_sources:
                        src_type = src.get("source_type")
                        if src_type == "dayun":
                            zhi_parts.append(f"大运 {zhi}")
                        elif src_type == "liunian":
                            zhi_parts.append(f"流年 {zhi}")
                        elif src_type == "natal":
                            pillar_name = src.get("pillar_name", "")
                            palace = src.get("palace", "")
                            if pillar_name and palace:
                                zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                            elif pillar_name:
                                zhi_parts.append(f"{pillar_name}{zhi}")
                    
                    if zhi_parts:
                        # 如果同一字在多个位置出现，分别列出（不合并）
                        for zp in zhi_parts:
                            parts.append(zp)
                
                # 结尾：三会局名称
                group = ev.get("group", "")
                matched_str = "".join(matched_branches)
                parts.append(f"{matched_str}三会{group.replace('会', '局')}")
                
                # 用空格连接各部分
                result = " ".join(parts)
                print(f"        {result}。")
            
            # 先计算流年天干和地支十神（用于缘分提示判断和十神行打印）
            liunian_gan = ln.get("gan", "")
            liunian_zhi = ln.get("zhi", "")
            gan_shishen = get_shishen(day_gan, liunian_gan) if liunian_gan else None
            gan_element = ln.get("gan_element", "")
            is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
            
            zhi_main_gan = get_branch_main_gan(liunian_zhi) if liunian_zhi else None
            zhi_shishen = get_shishen(day_gan, zhi_main_gan) if zhi_main_gan else None
            zhi_element = ln.get("zhi_element", "")
            is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
            
            # ===== 流年天干五合（只识别+打印，不影响风险） =====
            if liunian_gan:
                liunian_shishen = gan_shishen or "-"
                # 流年入口使用"年干"格式（不是"年柱天干"），本行不再重复打印"2050年"等年份
                liunian_gan_positions = []
                pillar_labels_liunian = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
                for pillar in ["year", "month", "day", "hour"]:
                    gan = bazi[pillar]["gan"]
                    shishen = get_shishen(day_gan, gan) or "-"
                    liunian_gan_positions.append(GanPosition(
                        source="natal",
                        label=pillar_labels_liunian[pillar],
                        gan=gan,
                        shishen=shishen
                    ))
                # 添加大运天干（如果存在）
                dayun_gan = dy.get("gan", "") if dy else None
                if dayun_gan:
                    dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
                    liunian_gan_positions.append(GanPosition(
                        source="dayun",
                        label="大运天干",
                        gan=dayun_gan,
                        shishen=dayun_shishen
                    ))
                # 添加流年天干
                liunian_gan_positions.append(GanPosition(
                    source="liunian",
                    label="流年天干",
                    gan=liunian_gan,
                    shishen=liunian_shishen
                ))
                liunian_wuhe_events = detect_gan_wuhe(liunian_gan_positions)
                if liunian_wuhe_events:
                    for ev in liunian_wuhe_events:
                        # 只打印涉及流年天干的五合
                        liunian_involved = any(pos.source == "liunian" for pos in ev["many_side"] + ev["few_side"])
                        if liunian_involved:
                            # 行内只保留"年干，月干，时干 乙 争合 流年天干，大运天干 庚 ..."
                            line = format_gan_wuhe_event(ev, incoming_shishen=liunian_shishen)
                            print(f"        {line}")
            
            # 注意：婚恋变化提醒已从 hints 读取，这里不再单独检测
            
            # ===== 冲摘要（流年地支冲命局宫位） =====
            # 允许进入摘要的宫位集合（匹配PILLAR_PALACE中的值）
            allowed_palaces = {"婚姻宫", "夫妻宫", "事业家庭宫（工作 / 子女 / 后期家庭）"}
            # 宫位名称映射（用于识别提示）
            palace_name_map = {
                "婚姻宫": "婚姻宫",
                "夫妻宫": "夫妻宫",
                "事业家庭宫（工作 / 子女 / 后期家庭）": "事业家庭宫"
            }
            
            # 收集流年地支冲命局宫位的事件
            clash_summary_lines = []
            clash_palaces_hit = set()  # 记录命中的允许宫位（用于识别提示）
            
            for ev in ln.get("clashes_natal", []) or []:
                if not ev:
                    continue
                flow_branch = ev.get("flow_branch", "")
                target_branch = ev.get("target_branch", "")
                if not flow_branch or not target_branch:
                    continue
                
                # 收集该次冲命中的允许宫位
                hit_palaces = []
                targets = ev.get("targets", [])
                for target in targets:
                    palace = target.get("palace", "")
                    # 检查是否在允许的宫位集合中
                    if palace in allowed_palaces:
                        # 使用简化的宫位名称（用于摘要显示）
                        simple_palace = palace_name_map.get(palace, palace)
                        hit_palaces.append(simple_palace)
                        clash_palaces_hit.add(simple_palace)
                
                # 如果过滤后还有允许的宫位，则生成摘要行
                if hit_palaces:
                    # 按固定顺序排序：婚姻宫/夫妻宫/事业家庭宫
                    palace_order = {"婚姻宫": 0, "夫妻宫": 1, "事业家庭宫": 2}
                    hit_palaces_sorted = sorted(hit_palaces, key=lambda p: palace_order.get(p, 99))
                    palace_str = "/".join(hit_palaces_sorted)
                    clash_name = f"{flow_branch}{target_branch}冲"
                    clash_summary_lines.append((clash_name, palace_str))
            
            # 打印冲摘要行（去重同一组冲）
            if clash_summary_lines:
                # 按冲名称分组，合并同一组冲的不同宫位
                clash_groups = {}
                for clash_name, palace_str in clash_summary_lines:
                    if clash_name not in clash_groups:
                        clash_groups[clash_name] = set()
                    clash_groups[clash_name].add(palace_str)
                
                # 打印摘要行
                for clash_name in sorted(clash_groups.keys()):
                    # 合并同一组冲的所有宫位（去重并排序）
                    all_palaces = set()
                    for palace_str in clash_groups[clash_name]:
                        all_palaces.update(palace_str.split("/"))
                    palace_order = {"婚姻宫": 0, "夫妻宫": 1, "事业家庭宫": 2}
                    sorted_palaces = sorted(all_palaces, key=lambda p: palace_order.get(p, 99))
                    palace_str = "/".join(sorted_palaces)
                    print(f"        冲：{clash_name}（{palace_str}）")
            
            # 检查是否命中时柱天克地冲（用于打印事件行）
            has_hour_tkdc = False
            hour_tkdc_info = None  # 存储时柱天克地冲信息，用于后续打印
            for ev_clash in ln.get("clashes_natal", []) or []:
                if not ev_clash:
                    continue
                tkdc_targets = ev_clash.get("tkdc_targets", [])
                if tkdc_targets:
                    flow_branch = ev_clash.get("flow_branch", "")
                    flow_gan = ev_clash.get("flow_gan", "")
                    for target in tkdc_targets:
                        if target.get("pillar") == "hour":
                            has_hour_tkdc = True
                            target_gan = target.get("target_gan", "")
                            target_branch = ev_clash.get("target_branch", "")
                            hour_tkdc_info = {
                                "liunian_ganzhi": f"{flow_gan}{flow_branch}",
                                "hour_ganzhi": f"{target_gan}{target_branch}"
                            }
                            break
                if has_hour_tkdc:
                    break
            
            # ===== 运年天克地冲摘要 =====
            # 检查运年相冲中的天克地冲（只打印事件行，提示从 hints 读取）
            for ev_clash in ln.get("clashes_dayun", []) or []:
                if not ev_clash:
                    continue
                if ev_clash.get("is_tian_ke_di_chong", False):
                    dayun_gan = ev_clash.get("dayun_gan", "")
                    liunian_gan = ev_clash.get("liunian_gan", "")
                    dayun_branch = ev_clash.get("dayun_branch", "")
                    liunian_branch = ev_clash.get("liunian_branch", "")
                    dayun_ganzhi = f"{dayun_gan}{dayun_branch}"
                    liunian_ganzhi = f"{liunian_gan}{liunian_branch}"
                    print(f"        天克地冲：大运 {dayun_ganzhi} ↔ 流年 {liunian_ganzhi}")
                    break  # 每年只打印一次
            
            # ===== 时柱天克地冲摘要 =====
            # 如果命中时柱天克地冲，打印事件行（提示从 hints 读取）
            if has_hour_tkdc and hour_tkdc_info:
                print(f"        天克地冲：流年 {hour_tkdc_info['liunian_ganzhi']} ↔ 时柱 {hour_tkdc_info['hour_ganzhi']}")
            
            # 事件区结束后固定只留 1 个空行
            print()
            
            # ===== 提示汇总区（从 hints 读取，唯一真相源） =====
            liunian_hints = ln.get("hints", [])

            # 收集模式提示（伤官见官/枭神夺食）
            all_events_for_hints = ln.get("all_events", [])
            static_events_for_hints = [ev for ev in all_events_for_hints if ev.get("type") in (
                "static_clash_activation", "static_punish_activation", "pattern_static_activation", "static_tkdc_activation"
            )]
            clashes_natal_for_hints = ln.get("clashes_natal", []) or []
            pattern_hints = _generate_pattern_hints(all_events_for_hints, static_events_for_hints, clashes_natal_for_hints)

            # 收集天克地冲提示（排除年柱、时柱）
            clashes_dayun_for_hints = ln.get("clashes_dayun", []) or []
            tkdc_hint = _generate_tkdc_hint(clashes_natal_for_hints, clashes_dayun_for_hints, static_events_for_hints)

            # 收集时柱天克地冲提示
            hour_tkdc_hint = _generate_hour_tkdc_hint(clashes_natal_for_hints)

            # 收集时支冲提示
            liunian_zhi_for_hints = ln.get("zhi", "")
            hour_clash_hint = _generate_hour_clash_hint(bazi, liunian_zhi_for_hints)

            # 互斥规则：时柱天克地冲 > 时支被冲
            # 如果有时柱天克地冲，则不输出时支被冲
            if hour_tkdc_hint:
                hour_clash_hint = ""  # 抑制时支被冲

            # 合并所有提示（顺序：伤官见官、枭神夺食、天克地冲、时柱天克地冲、时支被流年冲）
            all_hints = list(liunian_hints)
            all_hints.extend(pattern_hints)
            if tkdc_hint:
                all_hints.append(tkdc_hint)
            if hour_tkdc_hint:
                all_hints.append(hour_tkdc_hint)
            if hour_clash_hint:
                all_hints.append(hour_clash_hint)

            if all_hints:
                print("        提示汇总：")
                for hint in all_hints:
                    print(f"        - {hint}")
                print()

            # ===== 危险系数块（新格式） =====
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            tkdc_risk = ln.get("tkdc_risk_percent", 0.0)
            
            # 获取标签（已在上面计算过）
            gan_label = get_shishen_label(gan_shishen, is_gan_yongshen) if gan_shishen else ""
            zhi_label = get_shishen_label(zhi_shishen, is_zhi_yongshen) if zhi_shishen else ""
            
            # 打印总危险系数（带分隔线）
            print(f"        --- 总危险系数：{total_risk:.1f}% ---")
            
            # 风险管理选项已从 hints 中读取，不再单独打印
            
            # 打印天干十神行（移除感情字段）
            gan_yongshen_str = "是" if is_gan_yongshen else "否"
            if gan_shishen:
                label_str = f"｜标签：{gan_label}" if gan_label else ""
                print(f"        天干 {liunian_gan}｜十神 {gan_shishen}｜用神 {gan_yongshen_str}{label_str}")
            else:
                print(f"        天干 {liunian_gan}｜十神 -｜用神 {gan_yongshen_str}")
            
            # 打印开始危险系数
            print(f"        - 开始危险系数（天干引起）：{risk_from_gan:.1f}%")

            # 打印地支十神行（移除感情字段）
            zhi_yongshen_str = "是" if is_zhi_yongshen else "否"
            if zhi_shishen:
                label_str = f"｜标签：{zhi_label}" if zhi_label else ""
                print(f"        地支 {liunian_zhi}｜十神 {zhi_shishen}｜用神 {zhi_yongshen_str}{label_str}")
            else:
                print(f"        地支 {liunian_zhi}｜十神 -｜用神 {zhi_yongshen_str}")

            # 打印后来危险系数
            print(f"        - 后来危险系数（地支引起）：{risk_from_zhi:.1f}%")
            
            # 打印天克地冲危险系数
            print(f"        - 天克地冲危险系数：{tkdc_risk:.1f}%")
            print("")
            
            # 组织所有事件
            all_events = ln.get("all_events", [])
            gan_events = []
            zhi_events = []
            static_events = []
            
            for ev in all_events:
                ev_type = ev.get("type", "")
                if ev_type in ("static_clash_activation", "static_punish_activation", "pattern_static_activation", "static_tkdc_activation"):
                    static_events.append(ev)
                elif ev_type == "pattern":
                    kind = ev.get("kind", "")
                    if kind == "gan":
                        gan_events.append(ev)
                    elif kind == "zhi":
                        zhi_events.append(ev)
                elif ev_type == "lineyun_bonus":
                    lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                    lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                    if lineyun_bonus_gan > 0.0:
                        gan_events.append(ev)
                    if lineyun_bonus_zhi > 0.0:
                        zhi_events.append(ev)
                elif ev_type in ("branch_clash", "dayun_liunian_branch_clash", "punishment"):
                    zhi_events.append(ev)
            
            # 打印开始事件（天干相关）
            has_gan_events = gan_events or any(ev.get("type") == "pattern_static_activation" and (ev.get("risk_from_gan", 0.0) > 0.0) for ev in static_events)

            if has_gan_events:
                print("        开始事件（天干引起）：")
                
                # 收集所有动态天干模式，按类型分组
                pattern_gan_dynamic = {}  # {pattern_type: [events]}
                for ev in gan_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        if pattern_type not in pattern_gan_dynamic:
                            pattern_gan_dynamic[pattern_type] = []
                        pattern_gan_dynamic[pattern_type].append(ev)
                
                # 打印所有动态天干模式
                for pattern_type, events in pattern_gan_dynamic.items():
                    pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                    total_dynamic_risk = 0.0
                    for ev in events:
                        risk = ev.get("risk_percent", 0.0)
                        total_dynamic_risk += risk
                        print(f"          模式（天干层）：{pattern_name}，风险 {risk:.1f}%")
                    
                    # 打印对应的静态模式激活（如果有）
                    static_risk_gan = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "pattern_static_activation":
                            static_pattern_type = static_ev.get("pattern_type", "")
                            if static_pattern_type == pattern_type:
                                static_risk_gan = static_ev.get("risk_from_gan", 0.0)
                                if static_risk_gan > 0.0:
                                    print(f"          静态模式激活（天干）：{pattern_name}，风险 {static_risk_gan:.1f}%")
                                    break
                    
                    # 打印总和
                    total_pattern_risk = total_dynamic_risk + static_risk_gan
                    if total_pattern_risk > 0.0:
                        print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_gan:.1f}% = {total_pattern_risk:.1f}%")
                
                # 打印天干线运加成
                for ev in gan_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "lineyun_bonus":
                        lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                        if lineyun_bonus_gan > 0.0:
                            print(f"          线运加成（天干）：{lineyun_bonus_gan:.1f}%")
                
                print("")
            
            # 打印后来事件（地支相关）
            has_zhi_events = zhi_events or any(ev.get("type") in ("static_clash_activation", "static_punish_activation") or (ev.get("type") == "pattern_static_activation" and ev.get("risk_from_zhi", 0.0) > 0.0) for ev in static_events)
            # 检查是否有冲或刑
            if ln.get("clashes_natal") or ln.get("clashes_dayun"):
                has_zhi_events = True

            if has_zhi_events:
                print("        后来事件（地支引起）：")
                
                # 先打印所有动态冲
                total_clash_dynamic = 0.0
                from .config import PILLAR_PALACE
                sanhe_sanhui_bonus_printed = False  # 标记是否已打印三合/三会逢冲额外加分
                
                # 流年与命局的冲
                for ev in ln.get("clashes_natal", []):
                    if not ev:
                        continue
                    flow_branch = ev.get("flow_branch", "")
                    target_branch = ev.get("target_branch", "")
                    base_power = ev.get("base_power_percent", 0.0)
                    grave_bonus = ev.get("grave_bonus_percent", 0.0)
                    clash_risk_zhi = base_power + grave_bonus
                    if clash_risk_zhi > 0.0:
                        total_clash_dynamic += clash_risk_zhi
                        targets = ev.get("targets", [])
                        target_info = []
                        for target in targets:
                            target_pillar = target.get("pillar", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            target_info.append(f"{pillar_name}（{palace}）")
                        target_str = "、".join(target_info)
                        print(f"          冲：流年 {flow_branch} 冲 命局{target_str} {target_branch}，风险 {clash_risk_zhi:.1f}%")
                        
                        # 检查这个冲是否触发三合/三会逢冲额外加分（只打印一次）
                        if not sanhe_sanhui_bonus_printed:
                            sanhe_sanhui_bonus_ev = ln.get("sanhe_sanhui_clash_bonus_event")
                            if sanhe_sanhui_bonus_ev:
                                bonus_flow = sanhe_sanhui_bonus_ev.get("flow_branch", "")
                                bonus_target = sanhe_sanhui_bonus_ev.get("target_branch", "")
                                # 检查是否匹配当前冲
                                if (bonus_flow == flow_branch and bonus_target == target_branch) or \
                                   (bonus_flow == target_branch and bonus_target == flow_branch):
                                    _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev)
                                    sanhe_sanhui_bonus_printed = True

                        # 检查这个冲是否与模式重叠（伤官见官/枭神夺食）
                        if ev.get("is_pattern_overlap"):
                            overlap_pattern = ev.get("overlap_pattern_type", "")
                            pattern_bonus = ev.get("pattern_bonus_percent", 0.0)
                            if overlap_pattern == "hurt_officer":
                                print(f"          伤官见官（地支层）：与冲同时出现，风险 {pattern_bonus:.1f}%")
                            elif overlap_pattern == "pianyin_eatgod":
                                print(f"          枭神夺食（地支层）：与冲同时出现，风险 {pattern_bonus:.1f}%")

                # 运年相冲
                for ev in ln.get("clashes_dayun", []):
                    if not ev:
                        continue
                    dayun_branch = ev.get("dayun_branch", "")
                    liunian_branch = ev.get("liunian_branch", "")
                    base_risk = ev.get("base_risk_percent", 0.0)
                    grave_bonus = ev.get("grave_bonus_percent", 0.0)
                    clash_risk_zhi = base_risk + grave_bonus
                    if clash_risk_zhi > 0.0:
                        total_clash_dynamic += clash_risk_zhi
                        dg = ev.get("dayun_shishen") or {}
                        lg = ev.get("liunian_shishen") or {}
                        dg_ss = dg.get("shishen") or "-"
                        lg_ss = lg.get("shishen") or "-"
                        print(f"          运年相冲：大运支 {dayun_branch}（{dg_ss}） 与 流年支 {liunian_branch}（{lg_ss}） 相冲，风险 {clash_risk_zhi:.1f}%")
                        
                        # 检查这个冲是否触发三合/三会逢冲额外加分（只打印一次）
                        if not sanhe_sanhui_bonus_printed:
                            sanhe_sanhui_bonus_ev = ln.get("sanhe_sanhui_clash_bonus_event")
                            if sanhe_sanhui_bonus_ev:
                                bonus_flow = sanhe_sanhui_bonus_ev.get("flow_branch", "")
                                bonus_target = sanhe_sanhui_bonus_ev.get("target_branch", "")
                                # 检查是否匹配当前冲（运年相冲中，flow_branch可能是dayun_branch，target_branch可能是liunian_branch）
                                if (bonus_flow == dayun_branch and bonus_target == liunian_branch) or \
                                   (bonus_flow == liunian_branch and bonus_target == dayun_branch):
                                    _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev)
                                    sanhe_sanhui_bonus_printed = True
                
                # 打印静态冲激活（如果有）
                static_clash_risk = 0.0
                for static_ev in static_events:
                    if static_ev.get("type") == "static_clash_activation":
                        static_clash_risk = static_ev.get("risk_percent", 0.0)
                        if static_clash_risk > 0.0:
                            print(f"          静态冲激活：风险 {static_clash_risk:.1f}%")
                            break
                
                # 打印冲的总和（包含三合/三会逢冲额外加分）
                sanhe_sanhui_bonus_for_clash = ln.get("sanhe_sanhui_clash_bonus", 0.0)
                if total_clash_dynamic > 0.0 or static_clash_risk > 0.0 or sanhe_sanhui_bonus_for_clash > 0.0:
                    total_clash = total_clash_dynamic + static_clash_risk + sanhe_sanhui_bonus_for_clash
                    parts = []
                    if total_clash_dynamic > 0.0:
                        parts.append(f"动态 {total_clash_dynamic:.1f}%")
                    if static_clash_risk > 0.0:
                        parts.append(f"静态 {static_clash_risk:.1f}%")
                    if sanhe_sanhui_bonus_for_clash > 0.0:
                        parts.append(f"三合/三会逢冲 {sanhe_sanhui_bonus_for_clash:.1f}%")
                    parts_str = " + ".join(parts)
                    print(f"          冲总影响：{parts_str} = {total_clash:.1f}%")
                
                # 先打印所有动态刑
                total_punish_dynamic = 0.0
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "punishment":
                        risk = ev.get("risk_percent", 0.0)
                        total_punish_dynamic += risk
                        flow_branch = ev.get("flow_branch", "")
                        target_branch = ev.get("target_branch", "")
                        targets = ev.get("targets", [])
                        target_info = []
                        for target in targets:
                            target_pillar = target.get("pillar", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            target_info.append(f"{pillar_name}（{palace}）")
                        target_str = "、".join(target_info)
                        print(f"          刑：{flow_branch} 刑 {target_str} {target_branch}，风险 {risk:.1f}%")
                
                # 打印静态刑激活（如果有）
                static_punish_risk = 0.0
                for static_ev in static_events:
                    if static_ev.get("type") == "static_punish_activation":
                        static_punish_risk = static_ev.get("risk_percent", 0.0)
                        if static_punish_risk > 0.0:
                            print(f"          静态刑激活：风险 {static_punish_risk:.1f}%")
                            break
                
                # 打印刑的总和
                if total_punish_dynamic > 0.0 or static_punish_risk > 0.0:
                    total_punish = total_punish_dynamic + static_punish_risk
                    print(f"          刑总影响：动态 {total_punish_dynamic:.1f}% + 静态 {static_punish_risk:.1f}% = {total_punish:.1f}%")
                
                # 收集所有动态地支模式，按类型分组
                pattern_zhi_dynamic = {}  # {pattern_type: [events]}
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        if pattern_type not in pattern_zhi_dynamic:
                            pattern_zhi_dynamic[pattern_type] = []
                        pattern_zhi_dynamic[pattern_type].append(ev)
                
                # 打印所有动态地支模式
                for pattern_type, events in pattern_zhi_dynamic.items():
                    pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                    total_dynamic_risk = 0.0
                    for ev in events:
                        risk = ev.get("risk_percent", 0.0)
                        total_dynamic_risk += risk
                        print(f"          模式（地支层）：{pattern_name}，风险 {risk:.1f}%")
                    
                    # 打印对应的静态模式激活（如果有）
                    static_risk_zhi = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "pattern_static_activation":
                            static_pattern_type = static_ev.get("pattern_type", "")
                            if static_pattern_type == pattern_type:
                                static_risk_zhi = static_ev.get("risk_from_zhi", 0.0)
                                if static_risk_zhi > 0.0:
                                    print(f"          静态模式激活（地支）：{pattern_name}，风险 {static_risk_zhi:.1f}%")
                                    break
                    
                    # 打印总和
                    total_pattern_risk = total_dynamic_risk + static_risk_zhi
                    if total_pattern_risk > 0.0:
                        print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_zhi:.1f}% = {total_pattern_risk:.1f}%")
                
                # 打印地支线运加成
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "lineyun_bonus":
                        lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                        if lineyun_bonus_zhi > 0.0:
                            print(f"          线运加成（地支）：{lineyun_bonus_zhi:.1f}%")
                
                print("")
            
            # 打印天克地冲事件（单独列出）
            if tkdc_risk > 0.0:
                print("        天克地冲事件：")
                
                # 检查流年与命局的冲中的天克地冲
                for ev_clash in ln.get("clashes_natal", []):
                    if not ev_clash:
                        continue
                    tkdc_targets = ev_clash.get("tkdc_targets", [])
                    if tkdc_targets:
                        from .config import PILLAR_PALACE
                        flow_branch = ev_clash.get("flow_branch", "")
                        flow_gan = ev_clash.get("flow_gan", "")
                        for target in tkdc_targets:
                            target_pillar = target.get("pillar", "")
                            target_gan = target.get("target_gan", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            # 计算该柱的天克地冲加成
                            if target_pillar == "year":
                                tkdc_per_pillar = 0.0  # 年柱不加成
                            elif target_pillar == "day":
                                tkdc_per_pillar = 20.0  # 日柱20%
                            else:
                                tkdc_per_pillar = 10.0  # 其他柱10%
                            if tkdc_per_pillar > 0.0:
                                print(f"          天克地冲：流年 {flow_gan}{flow_branch} 与 命局{pillar_name}（{palace}）{target_gan}{ev_clash.get('target_branch', '')} 天克地冲，风险 {tkdc_per_pillar:.1f}%")
                
                # 检查运年相冲中的天克地冲
                for ev_clash in ln.get("clashes_dayun", []):
                    if not ev_clash:
                        continue
                    if ev_clash.get("is_tian_ke_di_chong", False):
                        dayun_gan = ev_clash.get("dayun_gan", "")
                        liunian_gan = ev_clash.get("liunian_gan", "")
                        dayun_branch = ev_clash.get("dayun_branch", "")
                        liunian_branch = ev_clash.get("liunian_branch", "")
                        # 运年天克地冲总共20%（基础10% + 运年额外10%）
                        print(f"          天克地冲：大运 {dayun_gan}{dayun_branch} 与 流年 {liunian_gan}{liunian_branch} 天克地冲，风险 20.0%")
                
                # 打印静态天克地冲激活
                for ev in static_events:
                    if ev.get("type") == "static_tkdc_activation":
                        risk_tkdc_static = ev.get("risk_from_gan", 0.0)  # 静态天克地冲全部计入tkdc_risk
                        if risk_tkdc_static > 0.0:
                            print(f"          静态天克地冲激活：风险 {risk_tkdc_static:.1f}%")
                
                print("")


        print("")  # 每个大运分隔一行
