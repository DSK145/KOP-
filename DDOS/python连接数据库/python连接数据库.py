# 导入所需库：
# os用于文件操作和执行系统命令，platform用于判断操作系统，socket用于网络通信
import os
import platform
import socket

# 全局配置参数：定义程序中用到的固定参数，便于统一修改和维护
# 目标数据库文件名，程序会搜索该文件
DB_FILENAME = "攻击数据库.sql"
# 自动搜索文件的路径列表，按顺序查找，优先匹配靠前的路径
SEARCH_PATHS = [
    os.path.expanduser("~/DDOS/"),  # 用户目录下的DDOS文件夹（~代表当前用户主目录）
    "/root/DDOS/",                  # root用户的DDOS文件夹
    "/opt/DDOS/",                   # 系统opt目录下的DDOS文件夹
    os.path.expanduser("~"),        # 当前用户的主目录
    "/root/"                        # root用户的主目录
]
TIMEOUT = 10  # 网络连接超时时间，单位为秒
BUF_SIZE = 4096  # 接收网络数据的缓冲区大小，单位为字节


# 查找数据库文件的函数
# 功能：先按预设路径自动搜索文件，未找到则提示用户手动输入并验证有效性
def find_db_file():
    print(f"查找文件: {DB_FILENAME}")  # 打印当前要查找的文件名
    for base_path in SEARCH_PATHS:  # 遍历预设的搜索路径
        file_path = os.path.join(base_path, DB_FILENAME)  # 拼接完整的文件路径
        if os.path.isfile(file_path):  # 判断该路径是否为有效文件
            print(f"找到文件: {file_path}")  # 找到后打印路径
            return file_path  # 返回找到的文件路径
    # 若自动搜索未找到，进入手动输入流程
    while True:  # 循环直到用户输入有效路径
        file_path = input("未找到，请输入文件路径: ").strip()  # 获取用户输入并去除首尾空格
        if os.path.isfile(file_path):  # 验证用户输入的路径是否为有效文件
            return file_path  # 输入有效，返回该路径
        print("路径无效，请重试")  # 输入无效，提示用户重新输入


# 通过ping命令检测IP地址的网络连通性
# 功能：调用系统ping命令，根据执行结果判断IP是否可达
def ping_ip(ip):
    # 根据操作系统设置ping命令的参数：
    # Windows系统使用"-n 1"（发送1个数据包），类Unix系统（Linux/macOS）使用"-c 1"
    param = "-n 1" if platform.system().lower() == "windows" else "-c 1"
    # 执行ping命令，将输出重定向到空设备（避免干扰终端显示）
    # os.system返回0表示命令执行成功（IP可达），非0表示失败（IP不可达）
    response = os.system(f"ping {param} {ip} > /dev/null 2>&1")
    return response == 0  # 返回布尔值，True表示IP可达


# 验证端口号的有效性
# 功能：检查输入的端口号是否为1-65535之间的整数
def validate_port(port):
    try:
        port = int(port)  # 尝试将输入转换为整数
        # 端口号的有效范围是1-65535（0为保留端口，不建议使用）
        return 1 <= port <= 65535
    except:  # 转换失败（输入不是数字），返回False
        return False


# 向目标IP和端口发送内容，并接收响应
# 功能：建立TCP连接，发送POST请求，接收并返回完整响应
def send_line(ip, port, content):
    try:
        # 创建socket对象（默认使用TCP协议）
        with socket.socket() as s:
            s.settimeout(TIMEOUT)  # 设置连接超时时间
            s.connect((ip, port))  # 连接目标IP和端口

            # 构造POST请求的数据部分（将内容作为表单数据发送）
            data = f"content={content}"
            # 构造完整的HTTP POST请求头
            request = (
                f"POST / HTTP/1.1\r\n"  # 请求方法、路径和HTTP版本
                f"Host: {ip}\r\n"  # 目标主机（IP地址）
                f"Content-Length: {len(data)}\r\n"  # 数据部分的长度
                "Content-Type: application/x-www-form-urlencoded\r\n"  # 数据类型为表单
                "Connection: close\r\n\r\n"  # 告诉服务器响应后关闭连接，空行分隔头和数据
                f"{data}"  # 实际发送的数据
            )
            s.sendall(request.encode())  # 发送请求（编码为字节流）

            # 接收完整的响应数据
            response = b""  # 用于存储响应的字节串
            # 循环接收数据，直到没有更多数据（recv返回空字节串）
            while (part := s.recv(BUF_SIZE)):
                response += part
            # 返回成功标志和响应内容（解码为字符串，忽略无法解码的字符）
            return True, response.decode(errors='replace')
    except Exception as e:  # 发生异常（如连接失败、超时等）
        return False, str(e)  # 返回失败标志和错误信息


# 主函数：程序的核心执行流程
def main():
    db_path = find_db_file()  # 查找并获取数据库文件的路径

    # 通过ping验证IP的有效性（网络可达性）
    while True:
        ip = input("目标IP: ").strip()  # 获取用户输入的目标IP
        print(f"正在ping {ip}...")  # 提示正在执行ping操作
        if ping_ip(ip):  # 调用ping_ip函数检测
            print(f"{ip} 可达")  # IP可达，退出循环
            break
        print(f"{ip} 不可达，请重新输入")  # IP不可达，提示重新输入

    # 验证端口的有效性
    while True:
        port_input = input("目标端口: ").strip()  # 获取用户输入的端口号
        if validate_port(port_input):  # 调用validate_port函数验证
            port = int(port_input)  # 转换为整数，退出循环
            break
        print("端口需为1-65535之间的数字")  # 端口无效，提示重新输入

    # 读取文件内容并逐行发送
    # 打开文件，按行读取内容（忽略空行，去除首尾空格）
    with open(db_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"\n共{len(lines)}行数据，开始发送...\n")  # 提示总数据量
    # 遍历每一行数据，调用send_line发送
    for i, line in enumerate(lines, 1):
        print(f"发送第{i}行: {line[:50]}...")  # 打印当前发送的行号和部分内容（避免过长）
        success, resp = send_line(ip, port, line)  # 发送当前行内容

        # 打印响应结果
        print("响应结果:")
        print("-"*50)  # 分隔线，增强可读性
        print(resp if success else f"失败: {resp}")  # 打印响应内容或错误信息
        print("-"*50 + "\n")  # 分隔线，换行


# 程序入口：当脚本直接运行时，执行main函数
if __name__ == "__main__":
    main()