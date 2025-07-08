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

## Windows 端安裝指引

以下安裝指引適用於已安裝 ANSYS Electronics Desktop (AEDT) 且可連線至 License Server 的 Windows 工作站。
請依照以下步驟操作：

### 1. 環境準備

1. 確認 **Windows 工作站**：

   * 已安裝 AEDT 並能正常開啟。
   * 能夠連線至公司內部的 License Server。
   * 具有穩定的網際網路連線。

2. 檢查系統需求：

   * 建議作業系統：Windows 10 64-bit 或以上。
   * Python 3.8 至 3.11。

### 2. 下載與解壓

1. 從 GitHub 或內部資源下載 `sim_service-master.zip`。
2. 將壓縮檔解壓至欲安裝的資料夾（例如：`C:\sim_service-master`）。


### 3. 建立虛擬環境與安裝模組

1. 開啟 **命令提示字元 (CMD)**，切換至解壓後的資料夾：

   ```bat
   cd C:\sim_service-master
   ```

2. 執行安裝批次腳本：

   ```bat
   install_venv.bat
   ```

   * 此腳本將建立 Python 虛擬環境並安裝所需套件。
   * 期間若提示權限問題，請以系統管理員權限重新執行。


### 4. 啟動應用程式

1. 若步驟 3 成功完成，執行：

   ```bat
   start.bat
   ```

2. 程式啟動後，Console 會顯示伺服器對外的 IP 位址與連接埠，例如：

   > Server will be available at [http://192.168.0.10:5000](http://192.168.0.10:5000)

### 5. 測試登入

| 身份          | 帳號 (Username) | 密碼 (Password) | 說明       |
| ----------- | ------------- | ------------- | -------- |
| 一般使用者       | `abc`         | `1234`        | 可使用基礎功能  |
| 管理者 (Admin) | `admin`       | `admin`       | 具備管理介面權限 |

1. 在瀏覽器中輸入步驟 4 顯示的網址。
2. 輸入上述帳號與密碼進行登入測試。

### 6. 外部登入測試（跨電腦測試）

若欲從其他電腦瀏覽此網站，需確認下列事項：

1. **伺服器端已開放 5000 埠（TCP）**：

   * 可透過防火牆例外或手動設定防火牆開啟。
   * 指令參考（需管理員權限）：

     ```powershell
     netsh advfirewall firewall add rule name="SimService Port 5000" dir=in action=allow protocol=TCP localport=5000
     ```

2. **用戶端電腦與伺服器在同一區網或網段可互通**。

3. 用戶端瀏覽器輸入伺服器顯示的 IP 與連接埠，例如：

   ```
   http://192.168.0.10:5000
   ```

4. 驗證是否能夠正常顯示登入頁面並進行登入操作。

## 任務範例
- **Fractal**：輸入深度 `--depth`，於 `outputs/<task_id>/fractal.png` 產生 Sierpinski 三角形圖檔，並將檔案列表與狀態寫入 `result.json`
- **Primes**：輸入上限 `--n`，於 `outputs/<task_id>/result.csv` 輸出所有小於 N 的質數
- **Sparams**：上傳任意埠數的 Touchstone 檔案（副檔名 `.sNp`，`N` 為任意整數），於 `outputs/<task_id>/` 產生各組 S-parameter 圖檔與 `index.html`。`index.html` 中的搜尋框支援輸入正規表示式過濾檢視的圖檔
- **Microstrip**：模擬微帶傳輸線並輸出 `microstrip.png`，需要安裝 `pyaedt` 並連線 ANSYS Electronics Desktop
- **Layer Viewer**：上傳 `.brd` 檔後產生所有訊號層的影像，另輸出 `stackup.xlsx` 與壓縮後的 AEDB，於 `index.html` 透過清單選擇並檢視各層

## 管理者功能
- 設定管理者帳號：手動在資料庫中將 `User.is_admin` 欄位設為 `True`
- 管理者登入後瀏覽 `/admin`，可檢視所有使用者、任務統計、搜尋或封存任務
- 管理者帳號僅提供管理功能，無法提交任務

## Stress Test
執行 `python -m service.stress_jobs --iterations 100 --rate 0.5 --seed 42` 即可隨機向所有任務類型提交作業，測試系統在大量請求下的穩定性。`--rate` 表示平均每秒提交的作業數，可搭配 `--seed` 控制分布。
