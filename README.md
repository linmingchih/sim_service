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
├── service/           # 應用程式模組
│   ├── flask_app.py   # 主 Flask 應用
│   ├── tasks.py       # 定義背景任務執行流程
│   ├── models.py      # SQLAlchemy 資料模型
│   ├── admin_routes.py
│   ├── user_routes.py
│   ├── config_utils.py
│   ├── scripts/       # 任務腳本
│   │   ├── run_fractal.py
│   │   ├── run_primes.py
│   │   └── run_sparams.py
│   ├── templates/     # HTML 範本
│   └── static/        # 靜態資源
├── task_config.yaml   # 任務腳本與虛擬環境設定
├── requirements.txt   # 相依套件列表
├── .gitignore         # Git 忽略清單
└── outputs/           # 任務輸出目錄（程式執行中自動建立）
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
   Windows 使用者也可直接執行 `install_venv.bat`，依提示指定 Python 3.10+
   的執行路徑後，程式會自動建立 `venv` 並安裝 `requirements.txt` 中的模組。
2. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
3. 編輯 `task_config.yaml`，將 `venv_python` 指向你的 Python 執行路徑（若使用虛擬環境為 `venv/bin/python` 或 `venv\Scripts\python.exe`）
4. 啟動 Flask 應用（預設使用 Waitress 作為生產環境伺服器）：
   ```bash
   python service/flask_app.py
   ```
   若要使用內建開發伺服器，可設定 `FLASK_DEBUG=1`：
   ```bash
   FLASK_DEBUG=1 python service/flask_app.py
   ```
5. 在瀏覽器開啟 `http://localhost:5000`，以管理者帳號登入
6. 在 Dashboard 提交 `fractal` 或 `primes` 任務，完成後於列表下載結果檔案
7. 若要使用 `microstrip` 模擬功能，確保在相同的虛擬環境中安裝 `pyaedt`
   ，並在 `task_config.yaml` 將 `venv_python` 指向該環境的 Python 執行檔
   （例如 `venv\Scripts\python.exe` 或 `venv/bin/python`）。

## Windows 端安裝指引
1. 準備一台已安裝 **ANSYS Electronics Desktop (AEDT)** 且可連線至 License Server 的 Windows 工作站，並確保該機器能上網。
2. 下載 `sim_service-master.zip` 後解壓縮。
3. 在資料夾中執行 `install_venv.bat` 建立虛擬環境並下載所需模組。
4. 完成後執行 `start.bat`，應用的 IP 位址會顯示於 console。
5. 測試登入請使用帳號 `abc`、密碼 `1234`；使用 `admin` / `admin` 可進入管理者模式。

## 任務範例
- **Fractal**：輸入深度 `--depth`，於 `outputs/<task_id>/fractal.png` 產生 Sierpinski 三角形圖檔，並將檔案列表與狀態寫入 `result.json`
- **Primes**：輸入上限 `--n`，於 `outputs/<task_id>/result.csv` 輸出所有小於 N 的質數
- **Sparams**：上傳任意埠數的 Touchstone 檔案（副檔名 `.sNp`，`N` 為任意整數），於 `outputs/<task_id>/` 產生各組 S-parameter 圖檔與 `index.html`。`index.html` 中的搜尋框支援輸入正規表示式過濾檢視的圖檔
- **Microstrip**：模擬微帶傳輸線並輸出 `microstrip.png`，需要安裝 `pyaedt` 並連線 ANSYS Electronics Desktop

## 管理者功能
- 設定管理者帳號：手動在資料庫中將 `User.is_admin` 欄位設為 `True`
- 管理者登入後瀏覽 `/admin`，可檢視所有使用者、任務統計、搜尋或封存任務
- 管理者帳號僅提供管理功能，無法提交任務
