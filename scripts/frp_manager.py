#!/usr/bin/env python3
"""FRP 配置管理器 - 生成 frpc/frps 配置、检查隧道状态"""
import argparse, json, os, sys

def gen_frps_config(bind_port=7000, token="", dashboard_port=7500, dashboard_user="admin", dashboard_pwd=""):
    """生成 frps 服务端配置"""
    config = f"""# frps 服务端配置 - 由 frp_manager.py 生成
[common]
bind_port = {bind_port}
token = {token}
dashboard_port = {dashboard_port}
dashboard_user = {dashboard_user}
dashboard_pwd = {dashboard_pwd}
log_file = /var/log/frps.log
log_level = info
max_pool_count = 10
"""
    return config

def gen_frpc_config(server_addr, server_port=7000, token="", proxies=None):
    """生成 frpc 客户端配置"""
    config = f"""# frpc 客户端配置 - 由 frp_manager.py 生成
[common]
server_addr = {server_addr}
server_port = {server_port}
token = {token}
log_file = /var/log/frpc.log
log_level = info
"""
    if proxies:
        for p in proxies:
            name = p.get("name", "proxy1")
            ptype = p.get("type", "tcp")
            local_port = p.get("local_port", 80)
            remote_port = p.get("remote_port", 8080)
            config += f"""
[{name}]
type = {ptype}
local_ip = {p.get("local_ip", "127.0.0.1")}
local_port = {local_port}
remote_port = {remote_port}
"""
            if p.get("custom_domain"):
                config += f"custom_domains = {p['custom_domain']}
"
    return config

def check_tunnel_status(dashboard_url="http://127.0.0.1:7500", user="admin", password=""):
    """检查 FRP 隧道状态"""
    try:
        import requests
        r = requests.get(f"{dashboard_url}/api/proxy/tcp", auth=(user, password), timeout=5)
        if r.status_code == 200:
            data = r.json()
            proxies = data.get("proxies", [])
            print(f"🔗 FRP 隧道状态 ({len(proxies)} 个):")
            for p in proxies:
                status = "✅ 运行中" if p.get("status") == "running" else "❌ 已停止"
                print(f"  {p.get('name','?'):20} {status}  {p.get('type','?')} :{p.get('remote_port','?')}")
        else:
            print(f"❌ 无法访问 FRP Dashboard: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ 连接 FRP Dashboard 失败: {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="FRP 配置管理器")
    sub = p.add_subparsers(dest="cmd")

    # 生成 frps 配置
    s1 = sub.add_parser("gen-frps", help="生成服务端配置")
    s1.add_argument("--port", type=int, default=7000)
    s1.add_argument("--token", default="")
    s1.add_argument("--output", default="frps.ini")

    # 生成 frpc 配置
    s2 = sub.add_parser("gen-frpc", help="生成客户端配置")
    s2.add_argument("--server", required=True, help="服务端地址")
    s2.add_argument("--port", type=int, default=7000)
    s2.add_argument("--token", default="")
    s2.add_argument("--output", default="frpc.ini")
    s2.add_argument("--proxies", help="JSON 格式的代理列表")

    # 检查状态
    s3 = sub.add_parser("status", help="检查隧道状态")
    s3.add_argument("--dashboard", default="http://127.0.0.1:7500")
    s3.add_argument("--user", default="admin")
    s3.add_argument("--password", default="")

    args = p.parse_args()
    if args.cmd == "gen-frps":
        cfg = gen_frps_config(args.port, args.token)
        with open(args.output, "w") as f: f.write(cfg)
        print(f"✅ 已生成 {args.output}")
    elif args.cmd == "gen-frpc":
        proxies = json.loads(args.proxies) if args.proxies else None
        cfg = gen_frpc_config(args.server, args.port, args.token, proxies)
        with open(args.output, "w") as f: f.write(cfg)
        print(f"✅ 已生成 {args.output}")
    elif args.cmd == "status":
        check_tunnel_status(args.dashboard, args.user, args.password)
    else:
        p.print_help()
