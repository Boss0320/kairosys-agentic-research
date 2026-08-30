# 一條工程 lineage，以 trust 為中心重建

Kairosys 在 **April 2025** 從 persistent-assistant 探索開始。它是一條帶有 **domain pivot** 與 **greenfield rewrite** 的工程 lineage，不是一個未曾中斷的 production runtime。

![Kairosys 五階段 lineage](../assets/evolution.svg)

## 五個階段

1. **Persistent assistant。** 最早的問題是：助理如何隨時間保留 context、rules、routing 與 traces。
2. **Finance-domain architecture。** 問題轉向金融研究，將資料工作、研究判斷、協調與 independent oversight 視為設計關切。
3. **Executable layered runtime。** 架構成為可執行系統，讓長時間存在的責任邊界與 specialist state 更難被理解。
4. **2026 greenfield rewrite。** 新 runtime 圍繞更清楚的 delegation、bounded execution 與 independent checking 設計，而不是把前一階段說成 seamless upgrade。
5. **Trust-first research。** 成功準則從「系統能不能生成報告？」改為「can every important claim survive an independent audit?」

## 為何重寫重要

這不是一次品牌更新。轉變重新界定了 authority：什麼能提供 evidence、什麼財務 state 能授權 valuation、以及最終 rendered report 可以說什麼。這些是貫穿 lineage 的線索，即使 runtime 本身已重建。

## 接著閱讀

請看[公開架構](architecture.zh-TW.md)的五個控制點，或閱讀[報告 attack surface](report-is-the-attack-surface.zh-TW.md)，理解促成 trust-first 準則的失敗模式。
