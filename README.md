# Hayyy 八字日主强弱 MVP（基于 lunar_python）

## 功能概览

- 使用 `lunar_python` 本地排盘，自动计算四柱八字（年、月、日、时）。
- 在此基础上，计算 **日主强弱百分比**（0–100%）。
- 预留了大运 / 流年的封装入口（`bazi/lunar_engine.py`），以后可以直接扩展。

> 注意：本项目 **不依赖任何在线 API**，所有排盘逻辑来自开源库 `lunar_python`。

## 安装步骤

1. 安装 Python 3.9+（3.10/3.11 也可以）

2. 安装依赖（建议在虚拟环境中）：

    ```bash
    pip install -r requirements.txt
    ```

3. 运行命令行程序：

    ```bash
    python main.py
    ```

   根据提示输入：
   - 阳历生日：YYYY-MM-DD
   - 出生时间：HH:MM（默认按出生地当地时间 / 北京时间理解）
   - 性别：M / F

## 文件结构

- `main.py`：入口脚本（CLI）
- `bazi/config.py`：权重表、五行映射等常量配置
- `bazi/strength.py`：日主强弱计算核心函数
- `bazi/lunar_engine.py`：封装 `lunar_python` 排盘 + 大运流年基础 + 完整分析入口
- `bazi/cli.py`：命令行交互逻辑
- `bazi/relationship_index.py`：Relationship Index (Index-5) 生成：感情变动窗口白名单口径
- `bazi/enrich.py`：数据丰富化：将打印层逻辑结构化回填到结果对象中
- `bazi/luck.py`：大运/流年排盘 + 好运/坏运 + 冲信息
- `bazi/clash.py`：地支冲检测
- `bazi/punishment.py`：地支刑检测
- `bazi/harmony.py`：地支合类检测（六合、三合、半合、三会）
- `bazi/gan_wuhe.py`：天干五合检测
- `bazi/marriage_wuhe.py`：天干五合争合/双合婚恋提醒检测
- `bazi/patterns.py`：十神模式检测（枭神夺食、伤官见官）
- `bazi/shishen.py`：十神计算与分类
- `bazi/yongshen.py`：用神计算
- `bazi/yongshen_swap.py`：用神互换检测
- `bazi/regress.py`：回归测试用例
- `tests/regression/samples.json`：回归样本输入文件（golden inputs）

## 关于大运 / 流年

`lunar_python` 已内置：

- 八字四柱：`lunar.getEightChar()`
- 大运：`baZi.getYun(sex).getDaYun()`
- 流年：`daYun.getLiuNian()`
- 小运：`daYun.getXiaoYun()`

本项目的 `bazi/lunar_engine.py` 里已经放了一个 `get_yun_info` 示例函数，示范如何取大运 / 流年数据。  
后续你可以在此基础上增加自己的权重和评分逻辑。
"# bazi" 
