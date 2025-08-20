  GNU nano 8.4                                                               zxc.py                                                                             TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        TCP.bind((host, port))
        TCP.listen(10)
        print("------------------------------------")
        print(f"监听端口号 {port}，目前用 TCP 连接（无加密）")

        # 循环接受客户端连接
        while True:
            print("等待客户端连接...")
            conn, addr = TCP.accept()
            print(f"连接地址（IPV4）：{addr}")

            while True:
                try:
                    response = conn.recv(6000).decode('utf-8')
                    if not response:
                        print("客户端断开连接")
                        break
                    print(f"接收数据（防 SQL 注入视角）：{response}")

                    response_message = input("回复：")
                    conn.send(response_message.encode('utf-8'))

                except socket.error as e:
                    print(f"收发数据出错中止：{e}")
                    break
            conn.close()

    except socket.error as e:
        print(f"绑定/监听端口出错：{e}")
    finally:
        TCP.close()


if __name__ == "__main__":
    # 先执行本地
    chat_interact()
    # TCP服务
    run_tcp_server()
