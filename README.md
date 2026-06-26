# 🏠 NAS-Tools — NAS与路由器管理工具集

OpenWrt / iStoreOS 路由器自动化管理、FRP 内网穿透、WireGuard VPN 配置生成、NAS 健康监控。

## 功能

| 工具 | 说明 |
|------|------|
| `router_manager.py` | 路由器管理（重启、状态、WiFi、防火墙） |
| `frp_manager.py` | FRP 配置生成与隧道状态检查 |
| `wireguard_gen.py` | WireGuard 配置生成（含手机二维码） |
| `nas_monitor.py` | NAS 健康监控（磁盘、CPU、内存、服务） |

## 快速开始

```bash
pip install -r requirements.txt

# 查看路由器状态
python scripts/router_manager.py --host 10.0.0.1 --action status

# 重启路由器
python scripts/router_manager.py --host 10.0.0.1 --action reboot

# 生成 WireGuard 配置
python scripts/wireguard_gen.py --server 10.0.0.1 --peer phone --output phone.conf

# 监控 NAS
python scripts/nas_monitor.py --host 192.168.1.33 --user yingjianchao
```

## 支持的设备

- iStoreOS（主路由）
- OpenWrt（旁路由）
- 飞牛 fnOS（NAS）
- 任意支持 SSH/ubus 的设备

## License

MIT
