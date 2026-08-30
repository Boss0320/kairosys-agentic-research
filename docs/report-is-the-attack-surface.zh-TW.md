# 報告就是 attack surface

## 1. Polished report 是危險表面

看似可信的敘事，可能藏著沒有 evidence authority 的主張、沒有 valuation authorization 的目標值，或在最後編修時引入的矛盾。Kairosys 把 rendered report 視為需要 audit 的對象，而不只是展示層。

## 2. 失敗一：模型抬升自己的來源主張

模型可以在草稿中寫入自信的 attribution，但那不會自動變成 evidence。公開 slice 從 tool observations 重建 evidence authority，並明確捨棄模型自行提供的 claim。研究員能分開看到這次嘗試與可信的路徑。

## 3. 失敗二：數字完整，不代表有 valuation authorization

四個季度可能遺漏、格式錯誤或彼此矛盾。因此目標值不是頁面上出現一個數字就能得到的格式權利。Valuation authorization 必須跟隨連貫 financial state；缺少它時，target 會被移除，留下的材料只作為 context。

## 4. 失敗三：最終文字引入新的矛盾

即使前面的檢查通過，rendered report 仍可能寫出彼此不一致的 target、EPS 與 displayed multiple。Rendered-report audit 會檢查最後的關係。這就是為何報告生成後仍需 final audit，而不只是在生成前小心處理 inputs。

## 5. 失敗 audit 仍可能保留標示清楚的草稿

不是每一個 failed audit 都會丟棄所有輸出。若 finding 限制的是某個 claim，而剩下的背景不會誤導，retained draft 可以為 analyst salvage 保留有用 context。它會保持可見標示與 review cap；被阻擋的 target 會被移除，不會偷偷保留。矛盾或不足的材料則會 withheld。

這個細節很重要：系統不是試圖讓每份草稿都看起來可交付，而是讓 delivery meaning 明確，讓 analyst 知道哪些可以 edit、哪些要 review、哪些只是 context、哪些不能繼續。

## 6. clean-room demo 證明什麼，又沒有證明什麼

[離線瀏覽器 dossier](../web/index.html) 證明五個固定 synthetic scenarios 會演示 evidence authority、valuation authorization 與 rendered-report audit 行為。它不證明廣泛的金融覆蓋、不能取代 analyst judgment，也不代表完整系統。[內容契約](../tests/test_content_contract.py)讓公開說明及其 boundaries 可被測試。
