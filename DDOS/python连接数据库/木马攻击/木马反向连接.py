import socket

# 配置监听的 IP 和端口
HOST = '0.0.0.0'
PORT = 4444

def start_listening():
    # 创建一个 TCP 套接字
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 绑定 IP 和端口
        s.bind((HOST, PORT))
        # 开始监听，最大连接数为 1
        s.listen(1)
        print(f"[*] Listening on {HOST}:{PORT}...")
        # 等待客户端连接
        conn, addr = s.accept()
        print(f"[*] Accepted connection from {addr}")
        try:
            # 接收客户端连接成功的消息
            print(conn.recv(1024).decode())
            while True:
                # 提示用户输入命令
                command = input("Enter command (or 'exit' to quit): ")
                if command.lower() == 'exit':
                    # 发送退出命令给客户端
                    conn.send(command.encode())
                    break
                # 发送命令给客户端
                conn.send(command.encode())
                output = ""
                while True:
                    # 接收客户端的响应
                    data = conn.recv(1024).decode()
                    output += data
                    if "[END_OF_OUTPUT]" in output:
                        break
                # 去除分隔符并打印输出
                output = output.replace("[END_OF_OUTPUT]\n", "")
                print(output)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # 关闭连接
            conn.close()

if __name__ == "__main__":
    print("""
    [警告] 本程序仅用于合法授权的教育与测试场景！
    未经授权使用将违反法律法规和道德准则。
    """)
    start_listening()