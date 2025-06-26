import socket
import os
import struct

SAVE_DIR = 'C://test'
os.makedirs(SAVE_DIR, exist_ok=True)

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('connection interrupted')
        data += more
    return data

def handle_connection(conn, addr):
    print(f"connected successfully: {addr}")
    try:
        while True:
            name_len_data = conn.recv(4)
            if not name_len_data:
                break
            name_len = struct.unpack('I', name_len_data)[0]
            filename = recv_all(conn, name_len).decode()

            filesize = struct.unpack('I', recv_all(conn, 4))[0]
            print(f"file recieved: {filename} ({filesize} bytes)")

            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, 'wb') as f:
                remaining = filesize
                while remaining > 0:
                    chunk = conn.recv(min(1024, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            print(f"✅ saved in : {filepath}\n")

    except Exception as e:
        print("❌ error :", e)
    finally:
        conn.close()
        print(f"🔌 connection to {addr} closed")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("172.25.160.1", 12345))
    server.listen(5)
    print("📡 waiting for connection")

    while True:
        conn, addr = server.accept()
        handle_connection(conn, addr)

if __name__ == '__main__':
    main()
