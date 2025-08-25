import socket

def chat_interact():  #封装

    print("输入，开心/伤心")
    asd = input("请输入内容: ")
    print(asd)
    print(f"你输入的内容: {asd}")
      #逻辑判断
    if asd == "开心":
        print("开心就说说吧")
    elif asd == "伤心":
        print("我做的那不对？可改")
        print("-------------------------------------")
    else:
        print("写入的内容ok？")
        print("-------------------------------------")

    FASK = ["不开心", "开心？", "好了行了聊会呗"]
    for x in FASK:
        print("--------------------------------------")
        print(x)

    print("")
    if asd == "伤心":
        asdf = ["好了我错了。", "不开玩笑了"]
        for j in asdf:
            print("------------------------------------------------")
            print(j)
    else:
        print("谢你来聊会")
    return asd  # 返回输入/交互拓展


def run_tcp_server():
    """启动 TCP 服务"""
    host = 'localhost'
    # 优化端口/异常处理
    while True:
        try:
            port = int(input("端口号开放/无占用："))
            break
        except ValueError: