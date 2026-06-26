#!/usr/bin/env python3
"""路由器管理工具 - 支持 OpenWrt/iStoreOS 的 ubus API"""
import argparse, json, requests, sys

class RouterManager:
    def __init__(self, host, username="root", password="", port=80):
        self.base = f"http://{host}:{port}"
        self.session = requests.Session()
        self.auth(username, password)

    def auth(self, username, password):
        r = self.session.post(f"{self.base}/ubus", json={
            "jsonrpc": "2.0", "id": 1, "method": "call",
            "params": ["00000000000000000000000000000000", "session", "login",
                       {"username": username, "password": password}]
        })
        data = r.json()
        if "result" in data and len(data["result"]) > 1:
            self.ubus_token = data["result"][1]["ubus_rpc_session"]
            print("认证成功")

    def call(self, obj, method, params=None):
        r = self.session.post(f"{self.base}/ubus", json={
            "jsonrpc": "2.0", "id": 1, "method": "call",
            "params": [self.ubus_token, obj, method, params or {}]
        })
        return r.json().get("result", [])

    def get_status(self):
        sysinfo = self.call("system", "sysinfo")
        board = self.call("system", "board")
        print("路由器状态:")
        if len(sysinfo) > 1:
            info = sysinfo[1]
            print(f"  主机名: {info.get('hostname', '?')}")
            print(f"  运行时间: {info.get('uptime', '?')} 秒")
            print(f"  负载: {info.get('load', '?')}")
        if len(board) > 1:
            b = board[1]
            print(f"  型号: {b.get('model', '?')}")

    def reboot(self, confirm=False):
        if not confirm:
            print("确认要重启路由器吗？加 --confirm 参数")
            return
        self.call("system", "reboot")
        print("路由器正在重启...")

    def get_wifi_status(self):
        devices = self.call("wifi", "get_devices", {})
        print("WiFi 状态:")
        if len(devices) > 1:
            for dev in devices[1].get("devices", []):
                print(f"  {dev.get('name', '?')}: {'开启' if dev.get('up') else '关闭'}")

    def get_clients(self):
        hosts = self.call("luci", "get_arp_table")
        print("已连接设备:")
        if len(hosts) > 1:
            for h in hosts[1]:
                print(f"  {h.get('IPADDR','?'):16} {h.get('HWADDR','?'):18} {h.get('HOSTNAME','未知')}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="路由器管理工具")
    p.add_argument("--host", required=True)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    p.add_argument("--action", choices=["status","reboot","wifi","clients"], default="status")
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    rm = RouterManager(args.host, args.user, args.password)
    {"status": rm.get_status, "reboot": lambda: rm.reboot(args.confirm),
     "wifi": rm.get_wifi_status, "clients": rm.get_clients}[args.action]()
