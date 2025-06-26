# udp_receiver.py
import socket
import struct
import os

SAVE_DIR = 'C://test'
os.makedirs(SAVE_DIR, exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('172.25.160.1', 12346))
print("等待 UDP 檔案...")

# 建議設定接收上限（UDP 有大小限制）
MAX_SIZE = 65535
data, addr = server.recvfrom(MAX_SIZE)
print(f"接收到來自 {addr} 的資料，總長度: {len(data)}")

# 解析格式：[name_len][name][filesize][data]
ptr = 0
name_len = struct.unpack('I', data[ptr:ptr+4])[0]
ptr += 4
filename = data[ptr:ptr+name_len].decode()
ptr += name_len
filesize = struct.unpack('I', data[ptr:ptr+4])[0]
ptr += 4
filedata = data[ptr:ptr+filesize]

filepath = os.path.join(SAVE_DIR, filename)
with open(filepath, 'wb') as f:
    f.write(filedata)

print(f"已儲存檔案：{filepath}（{filesize} bytes）")
server.close()
