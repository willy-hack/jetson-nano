# <div align="center">未來工程師Jetson nano一條指令配置檔案[溪南國中]</div>

### 下載一條指令配置檔案命令
```bash
wget "https://raw.githubusercontent.com/willy-hack/jetson-nano/refs/tags/1.0.5/install.sh"
sudo chmod +x ./install.sh && sudo ./install.sh
```

 - 文件說明:
    - 1.[camera](./code/camra.py).py
        - IMX477相機內參自動校準,將因為廣角模組而造成的畫面扭曲矯正回來
    - 2.[function](./code/function.py).py
        - 裡面包含了主程序中所需要的自訂義函數
    - 3.[HSV_write](./code/HSV_write.py).py
        - 此文件用來讀取場地上=>必障方塊,停車場,場地圖上的藍、橘色線的HSV數值用於主程序識別用
    - 4.[jetson_nano_binarization](./code/jetson_nano_binarization.py).py
        - 將畫面二值化的函數
    - 5.[jetson_nano_main_final](./code/jetson_nano_main_final.py).py
        - 決賽主程序
    - 6.[jetson_nano_main](./code/jetson_nano_main.py).py
        - 資格賽主程序
    - 7.[start-code](./code/start-code.py).py
        - 啟動主程序的程式,會偵測Raspberry Pi pico是否啟動,如果是就會執行主程式
    - 8.[start](./code/start.sh).sh
        - 用來銜接systemctl服務和start-code.py兩個檔案
    - 9.[start-code](./code/start-code.service).service
        - 用來自啟動start.sh的重要文件
    - 10.[hsv_values](./code/hsv_values.pkl).pkl
        - 儲存著場地上面所有需要進行識別物體的HSV數值
    - 11.[calibration_data](./code/calibration_data.npz).npz
        - 儲存著IMX477廣角鏡頭模組的校正內參數,若是此文件被刪除主程序將無法啟動