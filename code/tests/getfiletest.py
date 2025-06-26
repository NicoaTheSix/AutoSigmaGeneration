import socket
import os
import re

def get_local_ip():
    # 使用 socket 獲取本機 IP
    hostname = socket.gethostname()  # 獲取主機名稱
    local_ip = socket.gethostbyname(hostname)  # 獲取對應的 IP 地址
    return hostname,local_ip


def get_ip_from_ipconfig():
    # 執行 ipconfig 命令
    result = os.popen("ipconfig").read()
    
    # 使用正則表達式提取 IPv4 地址
    ip_pattern = re.compile(r"IPv4 Address[^\:]*:\s*([0-9\.]+)")
    matches = ip_pattern.findall(result)
    
    if matches:
        return matches  # 返回所有偵測到的 IP 地址
    else:
        return ["無法找到 IPv4 地址"]

PORT = 12345       # 埠號
# 伺服端設定
HOST = '0.0.0.0'
PORT = 12345
RECEIVE_DIR = './recieve'

def start_server(HOST):
    # 創建接收目錄
    os.makedirs(RECEIVE_DIR, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"伺服端正在監聽 {HOST}:{PORT} ...")
        
        conn, addr = server_socket.accept()
        print(f"已連接來自 {addr} 的客戶端。")
        
        while True:
            # 接收檔案/目錄名稱
            meta_data = conn.recv(1024).decode()
            if meta_data == "DONE":  # 接收完成的標記
                break
            
            is_dir, relative_path = meta_data.split('::')
            target_path = os.path.join(RECEIVE_DIR, relative_path)
            
            if is_dir == "DIR":
                # 如果是目錄，創建目錄
                os.makedirs(target_path, exist_ok=True)
            else:
                # 如果是檔案，接收並保存內容
                with open(target_path, 'wb') as f:
                    while True:
                        data = conn.recv(1024)
                        if data == b"END_OF_FILE":  # 檔案結束的標記
                            break
                        f.write(data)
        
        print("所有資料接收完成。")
        conn.close()

if __name__ == "__main__":
    hostname,local_ip = get_local_ip()
    print(f"本機 IP 地址: {local_ip}")
    start_server(local_ip)
