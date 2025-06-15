# Flask Task Platform

本專案示範如何使用 Flask、Celery 及 Redis 建立非同步任務平台，具備使用者系統與管理者介面，同時支援 `fractal` 與 `primes` 兩種範例任務。

## 功能概覽
1. **Flask + Flask-Login**：提供登入 / 登出，以及使用者任務列表
2. **Celery + Redis**：處理非同步任務，透過 `subprocess` 呼叫指定虛擬環境中的 Python 腳本
3. **任務輸出管理**：所有結果檔案儲存在 `outputs/<task_id>/`，並自動產生 `result.json`
4. **管理者介面**：新增、編輯或刪除使用者，並檢視任務統計、搜尋及封存任務

## 專案結構
```
flask-task-platform/
├── flask_app.py       # 主 Flask 應用
├── celery_app.py      # Celery 設定檔
├── tasks.py           # 定義 Celery 任務執行流程
├── models.py          # SQLAlchemy 資料模型（User / Task）
├── task_config.yaml   # 任務腳本與虛擬環境設定
├── requirements.txt   # 相依套件列表
├── .gitignore         # Git 忽略清單
├── outputs/           # 任務輸出目錄（程式執行中自動建立）
├── scripts/           # 任務腳本
│   ├── run_fractal.py
│   └── run_primes.py
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
1. 安裝並啟動 Redis：
   ```bash
   # Ubuntu / Debian
   sudo apt-get update && sudo apt-get install -y redis-server
   redis-server
   ```
2. （選擇性）建立虛擬環境並啟動：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 編輯 `task_config.yaml`，將 `venv_python` 指向你的 Python 執行路徑（若使用虛擬環境為 `venv/bin/python`）
5. 啟動 Celery worker：
   ```bash
# 若以 root 權限（如於 WSL/容器）或 Windows 上執行，可能因無法建立 semaphore 而失敗，
# 可加上 --pool=solo 避免此問題。
celery -A celery_app.celery worker --loglevel=info --pool=solo
   ```
6. 啟動 Flask 應用：
   ```bash
   python flask_app.py
   ```
7. 在瀏覽器開啟 `http://localhost:5000`，以管理者帳號登入
8. 在 Dashboard 提交 `fractal` 或 `primes` 任務，完成後於列表下載結果檔案

## 任務範例
- **Fractal**：輸入深度 `--depth`，於 `outputs/<task_id>/fractal.png` 產生 Sierpinski 三角形圖檔，並將檔案列表與狀態寫入 `result.json`
- **Primes**：輸入上限 `--n`，於 `outputs/<task_id>/result.csv` 輸出所有小於 N 的質數

## 管理者功能
- 設定管理者帳號：手動在資料庫中將 `User.is_admin` 欄位設為 `True`
- 管理者登入後瀏覽 `/admin`，可檢視所有使用者、任務統計、搜尋或封存任務