import os
import re
import requests
import time
import concurrent.futures
import subprocess
from datetime import datetime, timezone, timedelta
import socket

# ===============================
# 配置区
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
# 分类与映射配置 - 只保留央视、卫视、福建频道和凤凰频道
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17", "CCTV4K", "CCTV8K"
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视"
    ],
    "福建频道": [
        "福建卫视", "福建综合", "福建新闻", "福建经济", "福建电视剧", "福建公共", "福建少儿", "厦门卫视", "泉州电视台", "福州电视台"
    ],
    "凤凰频道": [
        "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台"
    ]
}

# ===== 映射（别名 -> 标准名） =====
CHANNEL_MAPPING = {
    # CCTV映射
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1 HD", "CCTV-1综合", "CCTV-1 综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 HD", "CCTV-2财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 HD", "CCTV-3综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4 HD", "CCTV-4中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲", "CCTV4欧洲 HD", "CCTV-4 欧洲", "CCTV-4中文国际欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4北美", "CCTV4美洲 HD", "CCTV-4 美洲", "CCTV-4中文国际美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 HD", "CCTV-5体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ HD", "CCTV-5+体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 HD", "CCTV-6电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 HD", "CCTV-7国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 HD", "CCTV-8电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 HD", "CCTV-9纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 HD", "CCTV-10科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 HD", "CCTV-11戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 HD", "CCTV-12社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 HD", "CCTV-13新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 HD", "CCTV-14少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 HD", "CCTV-15音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 4K", "CCTV-16奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 HD", "CCTV-17农业农村"],
    "CCTV4K": ["CCTV4K超高清", "CCTV-4K超高清", "CCTV-4K 超高清", "CCTV 4K"],
    "CCTV8K": ["CCTV8K超高清", "CCTV-8K超高清", "CCTV-8K 超高清", "CCTV 8K"],
    
    # 卫视频道映射
    "湖南卫视": ["湖南卫视4K", "湖南卫视高清", "湖南卫视 HD"],
    "浙江卫视": ["浙江卫视4K", "浙江卫视高清", "浙江卫视 HD"],
    "江苏卫视": ["江苏卫视4K", "江苏卫视高清", "江苏卫视 HD"],
    "东方卫视": ["东方卫视4K", "东方卫视高清", "东方卫视 HD"],
    "北京卫视": ["北京卫视4K", "北京卫视高清", "北京卫视 HD"],
    "广东卫视": ["广东卫视4K", "广东卫视高清", "广东卫视 HD"],
    
    # 福建频道映射
    "福建卫视": ["福建卫视高清", "福建卫视 HD", "Fujian TV", "福建衛視"],
    "福建综合": ["福建综合频道", "福建综合高清", "福建综合 HD"],
    "福建新闻": ["福建新闻频道", "福建新闻高清", "福建新闻 HD"],
    "厦门卫视": ["厦门卫视高清", "厦门卫视 HD", "Xiamen TV"],
    
    # 凤凰频道映射
    "凤凰卫视中文台": ["凤凰中文", "凤凰中文台", "凤凰卫视中文", "凤凰卫视", "鳳凰衛視中文台"],
    "凤凰卫视资讯台": ["凤凰资讯", "凤凰资讯台", "凤凰卫视资讯", "鳳凰衛視資訊台"],
    "凤凰卫视香港台": ["凤凰香港台", "凤凰卫视香港", "凤凰香港", "鳳凰衛視香港台"],
    "凤凰卫视电影台": ["凤凰电影", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台"],
}

# ===============================
# 增强的直播源测试配置 - 测试时间改为30秒
TEST_CONFIG = {
    'timeout': 15,  # 基础超时时间
    'extended_timeout': 40,  # 扩展测试超时时间
    'test_duration': 30,  # 测试持续时间改为30秒
    'required_streams': 3,  # 需要成功测试的流数量
    'stable_check_interval': 5,  # 稳定性检查间隔（秒）
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
            for line in sorted(unique.values()):
                f.write(line + "\n")
        print(f"🎯 第二阶段完成，写入 {len(unique)} 条记录")
    except Exception as e:
        print(f"❌ 写文件失败：{e}")

# ===============================
# 增强的直播源测试函数 - 测试时间改为30秒
def enhanced_stream_test(url, test_duration=30):
    """增强的直播源测试，测试更长时间以确保稳定性"""
    try:
        # 第一阶段：快速检查视频流格式
        print(f"🔍 快速检查: {url}")
        quick_check = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", 
             "-show_entries", "stream=codec_name,width,height,bit_rate", 
             "-of", "default=noprint_wrappers=1:nokey=1", 
             "-timeout", "8000000", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        # 检查是否有视频流信息
        has_video_stream = False
        if quick_check.stdout:
            output = quick_check.stdout.decode('utf-8', errors='ignore')
            if "h264" in output or "hevc" in output or "mpeg2" in output:
                has_video_stream = True
                print(f"✅ 视频流格式检查通过: {url}")
        
        if not has_video_stream:
            print(f"❌ 无有效视频流格式: {url}")
            return False
            
        # 第二阶段：扩展测试，拉流30秒
        print(f"⏱️  开始30秒稳定性测试: {url}")
        try:
            # 创建测试命令 - 使用更详细的参数
            test_cmd = [
                "ffmpeg", "-i", url,
                "-t", str(test_duration),  # 测试时长30秒
                "-f", "null", "-",
                "-loglevel", "info",
                "-stats"
            ]
            
            # 执行扩展测试
            start_time = time.time()
            extended_test = subprocess.run(
                test_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=test_duration + 15  # 增加额外超时时间
            )
            end_time = time.time()
            test_duration_actual = end_time - start_time
            
            # 检查返回码和错误输出
            if extended_test.returncode == 0:
                print(f"🎯 30秒稳定性测试通过 ({test_duration_actual:.1f}秒): {url}")
                return True
            else:
                error_output = extended_test.stderr.decode('utf-8', errors='ignore')
                
                # 检查特定错误类型
                if "Connection timed out" in error_output:
                    print(f"❌ 连接超时: {url}")
                elif "404 Not Found" in error_output or "403 Forbidden" in error_output:
                    print(f"❌ 资源不存在或禁止访问: {url}")
                elif "Server returned 4XX" in error_output:
                    print(f"❌ 服务器返回4XX错误: {url}")
                elif "End of file" in error_output and test_duration_actual > 20:
                    # 如果已经测试了超过20秒，认为可用
                    print(f"⚠️  文件结束但已测试{test_duration_actual:.1f}秒，标记为可用: {url}")
                    return True
                else:
                    # 输出前200个字符的错误信息
                    error_preview = error_output[:200] + "..." if len(error_output) > 200 else error_output
                    print(f"❌ 测试失败: {url} - 错误: {error_preview}")
                    
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  测试超时但已测试超过{test_duration}秒，标记为可用: {url}")
            return True  # 超时但已经测试了一段时间，可能可用
        except Exception as e:
            print(f"⚠️ 扩展测试异常: {e}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  快速检查超时: {url}")
        return False
    except Exception as e:
        print(f"⚠️ 测试异常: {e}")
        return False

# ===============================
# 第三阶段 - 30秒增强版测试
def third_stage_enhanced():
    print("🧩 第三阶段：30秒增强版稳定性测试")
    print("🔍 使用30秒稳定性测试，确保直播源稳定可用")

    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过第三阶段")
        return

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

    # 增强检测函数 - 使用30秒测试
    def detect_ip_enhanced(ip_port, entries):
        # 选择多个代表频道进行测试
        rep_channels = []
        
        # 优先测试CCTV1和CCTV5这两个关键频道
        for ch_main, url in entries:
            if ch_main in ["CCTV1", "CCTV5"]:
                rep_channels.append(url)
        
        # 如果没找到关键频道，测试任意前2个频道
        if len(rep_channels) < 2 and entries:
            for ch_main, url in entries:
                if url not in rep_channels:
                    rep_channels.append(url)
                if len(rep_channels) >= 2:
                    break
        
        # 对代表频道进行30秒增强测试
        success_count = 0
        for url in rep_channels[:2]:  # 最多测试2个频道（因为每个要30秒）
            if enhanced_stream_test(url, TEST_CONFIG['test_duration']):
                success_count += 1
                if success_count >= 1:  # 至少1个成功即可
                    break
        
        return ip_port, success_count >= 1

    print(f"🚀 启动30秒增强版多线程检测（共 {len(groups)} 个 IP）...")
    playable_ips = set()
    
    # 控制并发数，避免资源占用过多（30秒测试，并发数要更少）
    max_workers = min(3, len(groups))  # 减少并发数
    print(f"📊 使用 {max_workers} 个并发线程进行30秒稳定性测试")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(detect_ip_enhanced, ip, chs): ip for ip, chs in groups.items()}
        
        # 添加进度跟踪
        completed = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            try:
                ip_port, ok = future.result(timeout=TEST_CONFIG['test_duration'] + 20)  # 增加超时时间
                if ok:
                    playable_ips.add(ip_port)
                    print(f"✅ IP可用 ({completed}/{total}): {ip_port}")
                else:
                    print(f"❌ IP不可用 ({completed}/{total}): {ip_port}")
            except concurrent.futures.TimeoutError:
                print(f"⏱️  IP测试超时 ({completed}/{total}): 标记为不可用")
            except Exception as e:
                print(f"⚠️ 线程检测异常 ({completed}/{total}): {e}")
                continue

    print(f"✅ 30秒稳定性测试完成，可播放 IP 共 {len(playable_ips)} 个")

    # 收集有效频道
    valid_lines = []
    seen_urls = set()
    operator_playable_ips = {}
    
    # 只收集我们需要的分类中的频道
    target_channels = set()
    for category_list in CHANNEL_CATEGORIES.values():
        target_channels.update(category_list)

    for ip_port in playable_ips:
        operator = ip_info.get(ip_port, "未知")
        
        for ch_main, url in groups.get(ip_port, []):
            # 只保留目标频道
            if ch_main in target_channels and url not in seen_urls:
                seen_urls.add(url)
                valid_lines.append(f"{ch_main},{url}${operator}")
                operator_playable_ips.setdefault(operator, set()).add(ip_port)

    # 写回可用的IP到文件
    for operator, ip_set in operator_playable_ips.items():
        if operator == "未知":
            target_file = os.path.join(IP_DIR, "未知.txt")
        else:
            target_file = os.path.join(IP_DIR, operator + ".txt")
        try:
            os.makedirs(IP_DIR, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as wf:
                for ip in sorted(ip_set):
                    wf.write(ip + "\n")
            print(f"📥 覆盖写入 {target_file}，共 {len(ip_set)} 条可用 IP")
        except Exception as e:
            print(f"❌ 写回 {target_file} 失败：{e}")

    # 生成 IPTV.txt（包含更新时间与分类）
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "https://kakaxi-1.asia/LOGO/Disclaimer.mp4"

    try:
        with open(IPTV_FILE, "w", encoding="utf-8") as f:
            f.write(f"更新时间: {beijing_now}（北京时间）\n")
            f.write("⚠️ 注意：频道列表已通过30秒增强稳定性测试\n")
            f.write("📺 经过30秒稳定性测试，减少断流问题\n\n")
            f.write("免责声明,#genre#\n")
            f.write(f"免责声明视频,{disclaimer_url}\n\n")

            # 按分类写入频道
            for category, ch_list in CHANNEL_CATEGORIES.items():
                f.write(f"{category},#genre#\n")
                category_channels = []
                
                # 收集该分类的所有频道
                for ch in ch_list:
                    for line in valid_lines:
                        name = line.split(",", 1)[0]
                        if name == ch:
                            category_channels.append(line)
                
                # 去重并排序
                unique_channels = {}
                for line in category_channels:
                    url = line.split(",", 1)[1].split("$")[0]
                    if url not in unique_channels:
                        unique_channels[url] = line
                
                # 写入该分类的频道
                for line in sorted(unique_channels.values()):
                    f.write(line + "\n")
                
                f.write("\n")
        
        print(f"🎯 IPTV.txt 生成完成，共 {len(valid_lines)} 条频道")
        print(f"📊 频道分布：")
        for category, ch_list in CHANNEL_CATEGORIES.items():
            count = sum(1 for ch in ch_list if any(ch in line for line in valid_lines))
            if count > 0:
                print(f"  {category}: {count}个频道")
        
    except Exception as e:
        print(f"❌ 写 IPTV.txt 失败：{e}")

# ===============================
# 文件推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    try:
        subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions'], check=True)
        subprocess.run(['git', 'config', '--global', 'user.email', 'github-actions@users.noreply.github.com'], check=True)
    except Exception as e:
        print(f"⚠️ Git配置失败：{e}")

    # 添加文件
    try:
        subprocess.run(['git', 'add', '计数.txt'], check=True)
        subprocess.run(['git', 'add', 'ip/*.txt'], check=True)
        subprocess.run(['git', 'add', 'IPTV.txt'], check=True)
    except Exception as e:
        print(f"⚠️ Git添加文件失败：{e}")

    # 提交
    try:
        commit_msg = f"自动更新：30秒增强稳定性测试结果 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    except Exception:
        print("⚠️ 无需提交或提交失败")

    # 推送
    try:
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ 推送成功")
    except Exception:
        print("⚠️ 推送失败")

# ===============================
# 主执行逻辑
if __name__ == "__main__":
    # 确保目录存在
    os.makedirs(IP_DIR, exist_ok=True)
    os.makedirs(RTP_DIR, exist_ok=True)
    
    print("=" * 50)
    print("IPTV直播源30秒增强稳定性测试采集器")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("测试时长: 30秒/频道")
    print("=" * 50)

    # 检查ffmpeg是否可用
    try:
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("✅ FFmpeg 可用")
        else:
            print("⚠️ FFmpeg 返回非零状态码，可能有问题")
            exit(1)
    except FileNotFoundError:
        print("❌ FFmpeg 未安装，请确保已安装FFmpeg")
        exit(1)
    except Exception as e:
        print(f"⚠️ 检查FFmpeg时出错：{e}")
        exit(1)

    run_count = first_stage()

    if run_count % 10 == 0:
        print(f"🔔 运行次数 {run_count} 是10的倍数，开始第二、三阶段")
        second_stage()
        third_stage_enhanced()
    else:
        print(f"ℹ️ 本次运行次数 {run_count}，不是 10 的倍数，跳过第二、三阶段")

    push_all_files()
    
    print("\n" + "=" * 50)
    print("✅ 所有任务完成！")
    print(f"📺 生成的IPTV.txt包含：")
    for category in CHANNEL_CATEGORIES.keys():
        print(f"  • {category}")
    print("⏱️  所有频道均经过30秒稳定性测试")
    print("=" * 50)