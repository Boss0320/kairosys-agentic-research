# Kairosys — Agentic 金融研究系統

> 我獨立打造 Kairosys：一套 agentic 金融研究系統，協調證據與專業分析，產出可追溯、供研究員判斷與編輯的研究初稿。

Kairosys 本體是 agentic 系統；這份精選公開案例將其中的准入與稽核切片做成可執行示範，更完整的 agent 協調則呈現在[架構說明](docs/architecture.zh-TW.md)中。

自 2025 年 4 月起，我持續重建它的架構，圍繞一個愈來愈嚴格的目標：**can every important claim survive an audit?**

**15 秒。** Kairosys 是研究作業系統，不是單一報告產生器。它把研究問題拆到不同分析視角，保存工作背後的證據與決策，再將符合相應標示的草稿交給人類研究員。

**它協調的研究面向：**

- **基本面與財務建模**——理解公司表現、會計語意與預測結構。
- **產業、同業與供應鏈**——建立公司的競爭位置與營運脈絡。
- **市場脈絡與輔助技術訊號**——把市場行為當成輔助證據，而不是拿來取代投資論點。
- **估值與情境分析**——只有在財務狀態允許時，才選擇相應方法與假設。
- **催化劑、反證與分析師下一步**——指出什麼會改變或推翻論點，以及接下來要查什麼。
- **持續研究脈絡與決策軌跡**——讓先前證據與推理在研究過程中仍可被追溯。

**60 秒。** 它的差異化是一套兩層准入模型。第一層完整性門檻先判斷草稿是否有資格流向下一步；第二層效用分數再判斷研究是否夠廣、夠有用。內容再完整，也不能平均掉致命的證據或算術錯誤；內容正確但太淺，也不能把自己包裝成可直接使用的研究稿。

## Evidence

### 六個固定情境

| 情境 | 壓力測試 | 交付意義 |
| --- | --- | --- |
| `ready_report` | 證據、狀態與報告數學一致 | 可編輯的研究員初稿 |
| `spoofed_provenance` | 模型嘗試抬升自己的來源主張 | 需複核且受上限限制的初稿 |
| `incomplete_financials` | 缺少一季資料使目標值失去授權 | 僅保留脈絡的初稿 |
| `contradictory_financials` | 財務事實彼此矛盾 | 不交付 |
| `rendered_math_conflict` | 最終文字與顯示的數學矛盾 | 保留且需複核的草稿；在修正完成前，最終使用仍受阻擋。 |
| `shallow_but_sound` | 事實有支持，但只完成兩個研究面向 | 因效用不足而需複核的初稿 |

### 檢視證據的鏈條

- [開啟離線瀏覽器 dossier](web/index.html)，查看六個結果、evidence rail 與兩層准入路徑。
- [閱讀公開架構](docs/architecture.zh-TW.md)與[工程演化](docs/evolution.zh-TW.md)。
- [閱讀旗艦案例：報告就是 attack surface](docs/report-is-the-attack-surface.zh-TW.md)。
- [檢視兩層治理機制](docs/two-layer-governance.zh-TW.md)。
- [檢視內容契約](tests/test_content_contract.py)，或[切換為英文](README.md)。

### 執行示範

```bash
python3 -m demo.kairosys_case.cli --scenario ready_report
python3 -m unittest
python3 scripts/check_links.py .
CANDIDATE="$(mktemp -d)/public-candidate"
python3 scripts/assemble_public.py --source . --destination "$CANDIDATE" --manifest PUBLIC-MANIFEST.txt
python3 scripts/check_public_boundary.py "$CANDIDATE"
```

最後兩道指令會依 `PUBLIC-MANIFEST.txt` 把公開候選重組到全新目錄，並對該副本執行 default-deny 邊界掃描。掃描器刻意把 Git metadata 與 runtime cache 也列為 findings，因此它通過的對象是組裝後的候選，而不是工作中的 clone。

## 5 分鐘：設計判斷

問題不在草稿是否看起來漂亮，而在模型完成工作後，來源權威、財務語意、研究完整度與最終 rendered wording 是否仍一致。架構說明先呈現更大的研究系統，兩篇工程案例再讓它的准入控制可被直接檢查。

## 30 分鐘：演化與邊界

Kairosys 的演化經過 persistent assistant 起點、finance-domain pivot、可執行的 layered runtime、greenfield rewrite，以及 trust-first research 準則。工程演化文件保留這條進程，但不把它假裝成一個未曾中斷的 runtime。

這是一個 clean-room、synthetic vertical slice：它示範公開的行為契約，而非完整系統。它不含私有資料，也不是可部署的正式系統。研究員仍須對研究判斷與交付負責。
