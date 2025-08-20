  import socket


def chat_interact():
    print("输入，开心/伤心")
    asd = input("请输入内容： ")
    print(asd)
    print(f"你输入的内容：{asd}")

    if asd == "开心":
        print("开心就说说吧")
    elif asd == "伤心":
        print("我做的那不对？可改")
        print("-----------------------------")
    else:
        print("写入的内容ok? ")
        print("-----------------------------")

    FASK = ["不开心", "开心？", "好了行了聊会呗"]
    for x in FASK:
        print("-----------------------------")
        print(x)

    print("")
    if asd == "伤心":
        asdf = ["好了我错了。", "不开玩笑了"]
        for j in asdf:
            print("-----------------------------")
            print(j)
    else:
        print("谢你来聊会")
    return asd  


def run_tcp_server():
    host = 'localhost'
    while True:
        try:
            port = int(input("端口号开放/无占用："))
            break
        except ValueError:
            print("数字格式的端口号")

    TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        TCP.bind((host, port))
        TCP.listen(10)
        print("-----------------------------")
        print(f"监听端口号 {port}，目前用 TCP 连接（无加密）")

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
    chat_interact()
    run_tcp_server()
    run_tcp_server()
