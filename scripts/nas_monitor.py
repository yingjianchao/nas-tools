#!/usr/bin/env python3
"""NAS 健康监控 - 检查磁盘、CPU、内存、关键服务"""
import argparse, subprocess, sys, json

def ssh_cmd(host, cmd, user="root", port=22):
    """通过 SSH 执行远程命令"""
    try:
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-p", str(port), f"{user}@{host}", cmd],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def check_disk(host, user, port):
    """检查磁盘使用"""
    print("💾 磁盘使用:")
    out = ssh_cmd(host, "df -h | grep -E '^/dev|Filesystem'", user, port)
    for line in out.split("\n"):
        parts = line.split()
        if len(parts) >= 6:
            if parts[0] == "Filesystem":
                print(f"  {'设备':20} {'总量':8} {'已用':8} {'可用':8} {'使用率':8} {'挂载点'}")
                continue
            usage = int(parts[4].replace("%", ""))
            flag = "⚠️" if usage > 80 else "✅"
            print(f"  {flag} {parts[0]:20} {parts[1]:8} {parts[2]:8} {parts[3]:8} {parts[4]:8} {parts[5]}")

def check_memory(host, user, port):
    """检查内存使用"""
    print("\n🧠 内存使用:")
    out = ssh_cmd(host, "free -h | head -2", user, port)
    for line in out.split("\n"):
        print(f"  {line}")

def check_cpu(host, user, port):
    """检查 CPU 负载"""
    print("\n⚡ CPU 负载:")
    load = ssh_cmd(host, "cat /proc/loadavg", user, port)
    uptime = ssh_cmd(host, "uptime -p", user, port)
    print(f"  负载: {load}")
    print(f"  运行: {uptime}")

def check_services(host, user, port, services=None):
    """检查关键服务状态"""
    if not services:
        services = ["docker", "smbd", "nginx", "ssh"]
    print("\n🔧 服务状态:")
    for svc in services:
        status = ssh_cmd(host, f"systemctl is-active {svc} 2>/dev/null || echo inactive", user, port)
        flag = "✅" if "active" in status and "inactive" not in status else "❌"
        print(f"  {flag} {svc}: {status}")

def check_docker(host, user, port):
    """检查 Docker 容器"""
    print("\n🐳 Docker 容器:")
    out = ssh_cmd(host, "docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null", user, port)
    if out and "ERROR" not in out:
        for line in out.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                print(f"  {parts[0]:25} {parts[1]:30} {parts[2] if len(parts)>2 else ''}")
    else:
        print("  Docker 未运行或未安装")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="NAS 健康监控")
    p.add_argument("--host", required=True, help="NAS IP 地址")
    p.add_argument("--user", default="root", help="SSH 用户名")
    p.add_argument("--port", type=int, default=22, help="SSH 端口")
    p.add_argument("--services", nargs="+", help="要检查的服务列表")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    args = p.parse_args()

    print(f"🔍 检查 {args.host} ...\n")
    check_disk(args.host, args.user, args.port)
    check_memory(args.host, args.user, args.port)
    check_cpu(args.host, args.user, args.port)
    check_services(args.host, args.user, args.port, args.services)
    check_docker(args.host, args.user, args.port)
