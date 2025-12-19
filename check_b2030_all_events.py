# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2030:
            print(f"例B 2030年:")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            
            # 检查所有事件
            all_events = liunian.get("all_events", [])
            print(f"\n所有事件:")
            gan_risk = 0.0
            zhi_risk = 0.0
            
            for ev in all_events:
                ev_type = ev.get("type", "")
                risk = ev.get("risk_percent", 0.0)
                
                if ev_type == "pattern":
                    kind = ev.get("kind", "")
                    if kind == "gan":
                        gan_risk += risk
                        print(f"  模式（天干）: {risk}")
                    elif kind == "zhi":
                        zhi_risk += risk
                        print(f"  模式（地支）: {risk}")
                elif ev_type == "pattern_static_activation":
                    gan_static = ev.get("risk_from_gan", 0.0)
                    zhi_static = ev.get("risk_from_zhi", 0.0)
                    gan_risk += gan_static
                    zhi_risk += zhi_static
                    print(f"  静态模式激活: gan={gan_static}, zhi={zhi_static}")
                elif ev_type in ("branch_clash", "dayun_liunian_branch_clash", "punishment", "static_clash_activation", "static_punish_activation"):
                    zhi_risk += risk
                    print(f"  {ev_type}: {risk} (计入地支)")
            
            # 检查运年相冲
            clashes_dayun = liunian.get("clashes_dayun", [])
            for clash in clashes_dayun:
                tkdc_bonus = clash.get("tkdc_bonus_percent", 0.0)
                gan_risk += tkdc_bonus
                print(f"  运年相冲tkdc: {tkdc_bonus} (计入天干)")
            
            # 检查线运
            lineyun_bonus_gan = liunian.get("lineyun_bonus_gan", 0.0)
            lineyun_bonus_zhi = liunian.get("lineyun_bonus_zhi", 0.0)
            gan_risk += lineyun_bonus_gan
            zhi_risk += lineyun_bonus_zhi
            print(f"  线运: gan={lineyun_bonus_gan}, zhi={lineyun_bonus_zhi}")
            
            print(f"\n累加结果:")
            print(f"  gan_risk: {gan_risk}")
            print(f"  zhi_risk: {zhi_risk}")
            break
