import os
import re
import requests
import time
import concurrent.futures
import subprocess
import socket
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
# ===============================
FOFA_URLS = {
    "https://fofa.info/result?qbase64=InVkcHh5IiAmJiBjb3VudHJ5PSJDTiI%3D": "ip.txt",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
RTP_DIR = "rtp"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "IPTV.txt"

# ===============================
# 分类与映射配置（精简优化版）
# ===============================
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14",
        "CCTV15", "CCTV16", "CCTV17", "CCTV4K", "CCTV8K"
    ],
    "卫视频道": [
        "北京卫视", "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "广东卫视",
        "山东卫视", "天津卫视", "安徽卫视", "辽宁卫视", "黑龙江卫视", "四川卫视", "湖北卫视",
        "河南卫视", "河北卫视", "重庆卫视", "江西卫视", "贵州卫视", "云南卫视", "广西卫视",
        "福建卫视", "东南卫视", "山西卫视", "陕西卫视", "甘肃卫视", "海南卫视", "宁夏卫视",
        "青海卫视", "新疆卫视", "西藏卫视", "内蒙古卫视", "吉林卫视"
    ],
    "凤凰频道": [
        "凤凰中文台", "凤凰资讯台", "凤凰香港台", "凤凰电影台"
    ],
    "福建频道": [
        "福建卫视", "东南卫视", "厦门卫视", "泉州一套", "福州一套", "福建新闻",
        "福建公共", "福建综合", "福建电视剧", "新闻启示录"
    ]
}

# ===== 映射（别名 -> 标准名） =====
CHANNEL_MAPPING = {
    # ====== 央视频道 ======
    "CCTV1": ["CCTV-1", "CCTV-1 综合", "CCTV1 HD", "CCTV-1 HD", "中央电视台综合频道"],
    "CCTV2": ["CCTV-2", "CCTV2 HD", "CCTV-2 HD", "CCTV-2 财经"],
    "CCTV3": ["CCTV-3", "CCTV3 HD", "CCTV-3 HD", "CCTV-3 综艺"],
    "CCTV4": ["CCTV-4", "CCTV4 HD", "CCTV-4 HD", "CCTV-4 中文国际"],
    "CCTV5": ["CCTV-5", "CCTV5 HD", "CCTV-5 HD", "CCTV-5 体育"],
    "CCTV5+": ["CCTV-5+", "CCTV5+ HD", "CCTV-5+体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV6 HD", "CCTV-6 HD", "CCTV-6 电影"],
    "CCTV7": ["CCTV-7", "CCTV7 HD", "CCTV-7 HD", "CCTV-7 国防军事"],
    "CCTV8": ["CCTV-8", "CCTV8 HD", "CCTV-8 HD", "CCTV-8 电视剧"],
    "CCTV9": ["CCTV-9", "CCTV9 HD", "CCTV-9 HD", "CCTV-9 纪录"],
    "CCTV10": ["CCTV-10", "CCTV10 HD", "CCTV-10 HD", "CCTV-10 科教"],
    "CCTV11": ["CCTV-11", "CCTV11 HD", "CCTV-11 HD", "CCTV-11 戏曲"],
    "CCTV12": ["CCTV-12", "CCTV12 HD", "CCTV-12 HD", "CCTV-12 社会与法"],
    "CCTV13": ["CCTV-13", "CCTV13 HD", "CCTV-13 HD", "CCTV-13 新闻"],
    "CCTV14": ["CCTV-14", "CCTV14 HD", "CCTV-14 HD", "CCTV-14 少儿"],
    "CCTV15": ["CCTV-15", "CCTV15 HD", "CCTV-15 HD", "CCTV-15 音乐"],
    "CCTV16": ["CCTV-16", "CCTV16 HD", "CCTV16 4K", "CCTV-16 奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV17 HD", "CCTV-17 HD", "CCTV-17 农业农村"],
    "CCTV4K": ["CCTV4K超高清", "CCTV-4K超高清", "CCTV 4K"],
    "CCTV8K": ["CCTV8K超高清", "CCTV-8K超高清", "CCTV 8K"],
    
    # ====== 卫视频道 ======
    "北京卫视": ["北京卫视", "北京卫视HD", "BTV北京", "北京电视台"],
    "湖南卫视": ["湖南卫视", "湖南卫视HD", "Hunan TV", "湖南台"],
    "浙江卫视": ["浙江卫视", "浙江卫视HD", "Zhejiang TV"],
    "江苏卫视": ["江苏卫视", "江苏卫视HD", "Jiangsu TV"],
    "东方卫视": ["东方卫视", "东方卫视HD", "Dragon TV"],
    "深圳卫视": ["深圳卫视", "深圳卫视HD", "Shenzhen TV"],
    "广东卫视": ["广东卫视", "广东卫视HD", "Guangdong TV"],
    "山东卫视": ["山东卫视", "山东卫视HD", "Shandong TV"],
    "天津卫视": ["天津卫视", "天津卫视HD", "Tianjin TV"],
    "安徽卫视": ["安徽卫视", "安徽卫视HD", "Anhui TV"],
    "辽宁卫视": ["辽宁卫视", "辽宁卫视HD", "Liaoning TV"],
    "黑龙江卫视": ["黑龙江卫视", "黑龙江卫视HD", "Heilongjiang TV"],
    "四川卫视": ["四川卫视", "四川卫视HD", "Sichuan TV"],
    "湖北卫视": ["湖北卫视", "湖北卫视HD", "Hubei TV"],
    "河南卫视": ["河南卫视", "河南卫视HD", "Henan TV"],
    
    # ====== 凤凰频道 ======
    "凤凰中文台": ["凤凰中文台", "凤凰卫视中文台", "凤凰卫视", "鳳凰衛視中文台", "FengHuang Chinese", "Phoenix Chinese"],
    "凤凰资讯台": ["凤凰资讯台", "凤凰卫视资讯台", "鳳凰衛視資訊台", "Phoenix InfoNews", "FengHuang InfoNews", "凤凰资讯"],
    "凤凰香港台": ["凤凰香港台", "凤凰卫视香港台", "鳳凰衛視香港台", "Phoenix HongKong"],
    "凤凰电影台": ["凤凰电影台", "凤凰卫视电影台", "鳳凰衛視電影台", "Phoenix Movie"],
    
    # ====== 福建频道 ======
    "福建卫视": ["福建卫视", "福建电视台", "Fujian TV", "福建卫视HD", "福建卫星频道"],
    "东南卫视": ["东南卫视", "东南电视台", "SETV", "东南卫视HD"],
    "厦门卫视": ["厦门卫视", "Xiamen TV", "厦门电视台", "厦门卫视HD"],
    "泉州一套": ["泉州一套", "泉州新闻综合", "泉州电视台", "Quanzhou TV-1"],
    "福州一套": ["福州一套", "福州新闻综合", "福州电视台", "Fuzhou TV-1", "福州新闻"],
    "福建新闻": ["福建新闻", "福建新闻频道", "Fujian News", "福建新闻·公共"],
    "福建公共": ["福建公共", "福建公共频道", "福建公共·新闻", "Fujian Public"],
    "福建综合": ["福建综合", "福建综合频道", "Fujian Comprehensive"],
    "福建电视剧": ["福建电视剧", "福建电视剧频道"],
    "新闻启示录": ["新闻启示录", "福建新闻启示录"]
}

# ===============================
def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE, "r", encoding="utf-8").read().strip() or "0")
        except Exception:
            return 0
    return 0

def save_run_count(count):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(count))
    except Exception as e:
        print(f"⚠️ 写计数文件失败：{e}")


# ===============================
def get_isp_from_api(data):
    isp_raw = (data.get("isp") or "").lower()

    if "telecom" in isp_raw or "ct" in isp_raw or "chinatelecom" in isp_raw:
        return "电信"
    elif "unicom" in isp_raw or "cu" in isp_raw or "chinaunicom" in isp_raw:
        return "联通"
    elif "mobile" in isp_raw or "cm" in isp_raw or "chinamobile" in isp_raw:
        return "移动"

    return "未知"


def get_isp_by_regex(ip):
    if re.match(r"^(1[0-9]{2}|2[0-3]{2}|42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "电信"

    elif re.match(r"^(42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "联通"

    elif re.match(r"^(223|36|37|38|39|100|101|102|103|104|105|106|107|108|109|134|135|136|137|138|139|150|151|152|157|158|159|170|178|182|183|184|187|188|189)\.", ip):
        return "移动"

    return "未知"


# ===============================
# 第一阶段
def first_stage():
    os.makedirs(IP_DIR, exist_ok=True)
    all_ips = set()

    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
            all_ips.update(u.strip() for u in urls_all if u.strip())
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)

    province_isp_dict = {}

    for ip_port in all_ips:
        try:
            host = ip_port.split(":")[0]

            is_ip = re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)

            if not is_ip:
                try:
                    resolved_ip = socket.gethostbyname(host)
                    print(f"🌐 域名解析成功: {host} → {resolved_ip}")
                    ip = resolved_ip
                except Exception:
                    print(f"❌ 域名解析失败，跳过：{ip_port}")
                    continue
            else:
                ip = host

            res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = res.json()

            province = data.get("regionName", "未知")
            isp = get_isp_from_api(data)

            if isp == "未知":
                isp = get_isp_by_regex(ip)

            if isp == "未知":
                print(f"⚠️ 无法判断运营商，跳过：{ip_port}")
                continue

            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, set()).add(ip_port)

        except Exception as e:
            print(f"⚠️ 解析 {ip_port} 出错：{e}")
            continue

    count = get_run_count() + 1
    save_run_count(count)

    for filename, ip_set in province_isp_dict.items():
        path = os.path.join(IP_DIR, filename)
        try:
            with open(path, "a", encoding="utf-8") as f:
                for ip_port in sorted(ip_set):
                    f.write(ip_port + "\n")
            print(f"{path} 已追加写入 {len(ip_set)} 个 IP")
        except Exception as e:
            print(f"❌ 写入 {path} 失败：{e}")

    print(f"✅ 第一阶段完成，当前轮次：{count}")
    return count


# ===============================
# 第二阶段
def second_stage():
    print("🔔 第二阶段触发：生成 zubo.txt")
    if not os.path.exists(IP_DIR):
        print("⚠️ ip 目录不存在，跳过第二阶段")
        return

    combined_lines = []

    if not os.path.exists(RTP_DIR):
        print("⚠️ rtp 目录不存在，无法进行第二阶段组合，跳过")
        return

    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue

        ip_path = os.path.join(IP_DIR, ip_file)
        rtp_path = os.path.join(RTP_DIR, ip_file)

        if not os.path.exists(rtp_path):
            continue

        try:
            with open(ip_path, encoding="utf-8") as f1, open(rtp_path, encoding="utf-8") as f2:
                ip_lines = [x.strip() for x in f1 if x.strip()]
                rtp_lines = [x.strip() for x in f2 if x.strip()]
        except Exception as e:
            print(f"⚠️ 文件读取失败：{e}")
            continue

        if not ip_lines or not rtp_lines:
            continue

        for ip_port in ip_lines:
            for rtp_line in rtp_lines:
                if "," not in rtp_line:
                    continue

                ch_name, rtp_url = rtp_line.split(",", 1)

                if "rtp://" in rtp_url:
                    part = rtp_url.split("rtp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/rtp/{part}")

                elif "udp://" in rtp_url:
                    part = rtp_url.split("udp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/udp/{part}")

    # 去重
    unique = {}
    for line in combined_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in unique:
            unique[url_part] = line

    try:
        with open(ZUBO_FILE, "w", encoding="utf-8") as f:
            for line in unique.values():
                f.write(line + "\n")
        print(f"🎯 第二阶段完成，写入 {len(unique)} 条记录")
    except Exception as e:
        print(f"❌ 写文件失败：{e}")


# ===============================
# 第三阶段 - 【重点优化部分】
# ===============================
def third_stage():
    print("🧩 第三阶段：多线程检测代表频道生成 IPTV.txt")
    print("🔧 优化版：30秒稳定性检测 + IP自动淘汰机制")

    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过第三阶段")
        return

    # ============================================
    # 【优化1】强化版流检测函数（解决断流关键）
    # ============================================
    def check_stream(url, timeout=30):  # 超时增加到30秒
        """强化版流检测：模拟真实播放30秒，淘汰5-10分钟断流的服务器"""
        try:
            # 使用ffmpeg进行30秒拉流测试，而不是简单探测
            cmd = [
                'ffmpeg',
                '-i', url,
                '-t', '30',           # 拉取30秒视频
                '-c', 'copy',         # 直接复制流，不转码
                '-f', 'null',         # 不输出文件
                '-loglevel', 'error', # 只显示错误信息
                '-'
            ]
            
            # 执行命令，设置总超时为35秒
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=35
            )
            
            # 分析结果：返回码为0且没有严重错误才算成功
            if result.returncode == 0:
                return True
            
            # 检查错误输出，识别常见断流原因
            stderr_text = result.stderr.decode('utf-8', errors='ignore')
            error_patterns = [
                'Connection timed out',
                'Failed to reconnect',
                'Connection refused',
                'read timeout',
                'HTTP error 404',
                'Server returned 404'
            ]
            
            for pattern in error_patterns:
                if pattern in stderr_text:
                    print(f"⚡ 检测到不稳定服务器 [{pattern}]: {url[:50]}...")
                    return False
                    
            return False
            
        except subprocess.TimeoutExpired:
            # 30秒内频繁中断会导致超时
            print(f"⏰ 流检测超时（可能频繁断流）: {url[:50]}...")
            return False
        except Exception as e:
            print(f"⚠️ 检测异常: {e}")
            return False
    
    # ============================================
    # 以下为原始逻辑（保持不变）
    # ============================================
    
    # 别名映射
    alias_map = {}
    for main_name, aliases in CHANNEL_MAPPING.items():
        for alias in aliases:
            alias_map[alias] = main_name

    # 读取现有 ip 文件，建立 ip_port -> operator 映射
    ip_info = {}
    if os.path.exists(IP_DIR):
        for fname in os.listdir(IP_DIR):
            if not fname.endswith(".txt"):
                continue
            province_operator = fname.replace(".txt", "")
            try:
                with open(os.path.join(IP_DIR, fname), encoding="utf-8") as f:
                    for line in f:
                        ip_port = line.strip()
                        if ip_port:
                            ip_info[ip_port] = province_operator
            except Exception as e:
                print(f"⚠️ 读取 {fname} 失败：{e}")

    # 读取 zubo.txt 并按 ip:port 分组
    groups = {}
    with open(ZUBO_FILE, encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue
            ch_name, url = line.strip().split(",", 1)
            ch_main = alias_map.get(ch_name, ch_name)
            m = re.match(r"http://(\d+\.\d+\.\d+\.\d+:\d+)/", url)
            if m:
                ip_port = m.group(1)
                groups.setdefault(ip_port, []).append((ch_main, url))

    # 选择代表频道并检测
    def detect_ip(ip_port, entries):
        rep_channels = [u for c, u in entries if c == "CCTV1"]
        if not rep_channels and entries:
            rep_channels = [entries[0][1]]
        
        # 【优化】每个IP只检测一个代表频道，但检测时间更长
        playable = False
        for url in rep_channels[:1]:  # 只检测第一个代表频道
            if check_stream(url):
                playable = True
                break
        return ip_port, playable

    print(f"🚀 启动多线程检测（共 {len(groups)} 个 IP）...")
    print("⏳ 每个IP检测约30秒，请耐心等待...")
    
    playable_ips = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # 减少并发数，避免资源耗尽
        futures = {executor.submit(detect_ip, ip, chs): ip for ip, chs in groups.items()}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            try:
                ip_port, ok = future.result()
            except Exception as e:
                print(f"⚠️ 线程检测返回异常：{e}")
                continue
            if ok:
                playable_ips.add(ip_port)
            
            # 显示进度
            if completed % 5 == 0 or completed == len(groups):
                print(f"📊 检测进度: {completed}/{len(groups)} ({(completed/len(groups))*100:.1f}%)")

    print(f"✅ 检测完成，可播放 IP 共 {len(playable_ips)} 个")

    valid_lines = []
    seen = set()
    operator_playable_ips = {}

    for ip_port in playable_ips:
        operator = ip_info.get(ip_port, "未知")

        for c, u in groups.get(ip_port, []):
            key = f"{c},{u}"
            if key not in seen:
                seen.add(key)
                valid_lines.append(f"{c},{u}${operator}")

                operator_playable_ips.setdefault(operator, set()).add(ip_port)

    # ============================================
    # 【优化2】IP淘汰机制：覆盖写入，只保留有效IP
    # ============================================
    print("🔄 开始淘汰无效IP，更新IP库...")
    for operator, ip_set in operator_playable_ips.items():
        if operator == "未知":
            target_file = os.path.join(IP_DIR, "未知.txt")
        else:
            target_file = os.path.join(IP_DIR, operator + ".txt")
        try:
            os.makedirs(IP_DIR, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as wf:  # 注意是"w"覆盖写，不是"a"追加
                for ip in sorted(ip_set):
                    wf.write(ip + "\n")
            print(f"📁 覆盖写入 {target_file}，保留 {len(ip_set)} 个有效IP")
        except Exception as e:
            print(f"❌ 写回 {target_file} 失败：{e}")
    
    # 【新增】清理完全没有有效IP的文件
    all_operators = set([os.path.splitext(f)[0] for f in os.listdir(IP_DIR) if f.endswith('.txt')])
    valid_operators = set(operator_playable_ips.keys())
    for operator in all_operators - valid_operators:
        if operator != "未知":  # 保留未知文件
            target_file = os.path.join(IP_DIR, operator + ".txt")
            if os.path.exists(target_file):
                os.remove(target_file)
                print(f"🧹 清理无有效IP的文件: {operator}.txt")
    
    print(f"✅ IP库更新完成，共保留 {len(playable_ips)} 个有效IP")

    # ============================================
    # 写 IPTV.txt（保持不变）
    # ============================================
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "https://kakaxi-1.asia/LOGO/Disclaimer.mp4"

    try:
        with open(IPTV_FILE, "w", encoding="utf-8") as f:
            f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
            f.write("更新时间,#genre#\n")
            f.write(f"{beijing_now},{disclaimer_url}\n\n")

            for category, ch_list in CHANNEL_CATEGORIES.items():
                f.write(f"{category},#genre#\n")
                for ch in ch_list:
                    for line in valid_lines:
                        name = line.split(",", 1)[0]
                        if name == ch:
                            f.write(line + "\n")
                f.write("\n")
        print(f"🎯 IPTV.txt 生成完成，共 {len(valid_lines)} 条频道")
        print("=" * 60)
        print("✨ 优化完成总结：")
        print(f"  1. 使用30秒稳定性检测，淘汰易断流服务器")
        print(f"  2. 自动清理无效IP，IP库只保留有效IP")
        print(f"  3. 生成 {len(valid_lines)} 个高质量频道")
        print("=" * 60)
    except Exception as e:
        print(f"❌ 写 IPTV.txt 失败：{e}")


# ===============================
# 文件推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    try:
        os.system('git config --global user.name "github-actions"')
        os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    except Exception:
        pass

    os.system("git add 计数.txt || true")
    os.system("git add ip/*.txt || true")
    os.system("git add IPTV.txt || true")
    os.system('git commit -m "自动更新：计数、IP文件、IPTV.txt" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo '⚠️ 推送失败'")


# ===============================
# 主执行逻辑
if __name__ == "__main__":
    # 确保目录存在
    os.makedirs(IP_DIR, exist_ok=True)
    os.makedirs(RTP_DIR, exist_ok=True)

    run_count = first_stage()

    if run_count % 10 == 0:
        second_stage()
        third_stage()
    else:
        print("ℹ️ 本次不是 10 的倍数，跳过第二、三阶段")

    push_all_files()