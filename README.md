# Flask Task Platform

本專案示範如何使用 Flask 搭配 Flask‑Executor 建立非同步任務平台，具備使用者系統與管理者介面，同時支援 `fractal` 與 `primes` 兩種範例任務。

## 功能概覽
1. **Flask + Flask-Login**：提供登入 / 登出，以及使用者任務列表
2. **Flask‑Executor**：以背景執行緒處理非同步任務，透過 `subprocess` 呼叫指定虛擬環境中的 Python 腳本
3. **任務輸出管理**：所有結果檔案儲存在 `outputs/<task_id>/`，並自動產生 `result.json`
4. **管理者介面**：新增、編輯或刪除使用者，並檢視任務統計、搜尋及封存任務
5. **任務刪除**：一般使用者可刪除自己的任務，移除輸出檔案以節省空間，記錄仍供管理者統計

## 專案結構
```
flask-task-platform/
├── flask_app.py       # 主 Flask 應用
├── tasks.py           # 定義背景任務執行流程
├── models.py          # SQLAlchemy 資料模型（User / Task）
├── task_config.yaml   # 任務腳本與虛擬環境設定
├── requirements.txt   # 相依套件列表
├── .gitignore         # Git 忽略清單
├── outputs/           # 任務輸出目錄（程式執行中自動建立）
├── scripts/           # 任務腳本
│   ├── run_fractal.py
│   ├── run_primes.py
│   └── run_sparams.py
├── templates/         # HTML 範本
│   ├── login.html
│   ├── dashboard.html
│   ├── admin_tasks.html
│   └── admin_users.html
└── static/            # 靜態資源
    └── css/
        └── style.css
```

## 快速啟動
1. （選擇性）建立虛擬環境並啟動：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / macOS
   # source venv/bin/activate
   ```
2. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
3. 編輯 `task_config.yaml`，將 `venv_python` 指向你的 Python 執行路徑（若使用虛擬環境為 `venv/bin/python` 或 `venv\Scripts\python.exe`）
4. 啟動 Flask 應用：
   ```bash
   python flask_app.py
   ```
5. 在瀏覽器開啟 `http://localhost:5000`，以管理者帳號登入
6. 在 Dashboard 提交 `fractal` 或 `primes` 任務，完成後於列表下載結果檔案

## 任務範例
- **Fractal**：輸入深度 `--depth`，於 `outputs/<task_id>/fractal.png` 產生 Sierpinski 三角形圖檔，並將檔案列表與狀態寫入 `result.json`
- **Primes**：輸入上限 `--n`，於 `outputs/<task_id>/result.csv` 輸出所有小於 N 的質數
- **Sparams**：上傳任意埠數的 Touchstone 檔案（副檔名 `.sNp`，`N` 為任意整數），於 `outputs/<task_id>/` 產生各組 S-parameter 圖檔與 `index.html`。`index.html` 中的搜尋框支援輸入正規表示式過濾檢視的圖檔

## 管理者功能
- 設定管理者帳號：手動在資料庫中將 `User.is_admin` 欄位設為 `True`
- 管理者登入後瀏覽 `/admin`，可檢視所有使用者、任務統計、搜尋或封存任務
- 管理者帳號僅提供管理功能，無法提交任務
