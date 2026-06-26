#!/usr/bin/env python3
"""WireGuard 配置生成器 - 生成服务端/客户端配置和手机二维码"""
import argparse, subprocess, sys, os, base64

def gen_keypair():
    """生成 WireGuard 密钥对"""
    try:
        priv = subprocess.check_output(["wg", "genkey"], text=True).strip()
        pub = subprocess.check_output(["wg", "pubkey"], input=priv, text=True).strip()
        return priv, pub
    except FileNotFoundError:
        # 没有 wg 命令时用 Python 生成
        import nacl.public
        sk = nacl.public.PrivateKey.generate()
        pk = sk.public_key
        return (base64.b64encode(sk.encode()).decode(),
                base64.b64encode(pk.encode()).decode())

def gen_server_config(private_key, listen_port=51820, network="10.10.0.0/24"):
    """生成服务端配置"""
    return f"""[Interface]
PrivateKey = {private_key}
Address = {network.split("/")[0].rsplit(".", 1)[0]}.1/24
ListenPort = {listen_port}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
"""

def gen_client_config(name, private_key, server_pubkey, server_endpoint,
                      client_ip="10.10.0.2", dns="10.0.0.1", allowed="0.0.0.0/0"):
    """生成客户端配置"""
    return f"""# WireGuard 客户端配置 - {name}
[Interface]
PrivateKey = {private_key}
Address = {client_ip}/24
DNS = {dns}

[Peer]
PublicKey = {server_pubkey}
Endpoint = {server_endpoint}
AllowedIPs = {allowed}
PersistentKeepalive = 25
"""

def gen_qr_code(config, output_path="wg-peer.png"):
    """生成配置的二维码（方便手机导入）"""
    try:
        subprocess.run(["qrencode", "-o", output_path, "-t", "PNG", config], check=True)
        print(f"📱 二维码已保存: {output_path}")
    except FileNotFoundError:
        print("⚠️  需要安装 qrencode: apt install qrencode")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="WireGuard 配置生成器")
    sub = p.add_subparsers(dest="cmd")

    s1 = sub.add_parser("gen-keys", help="生成密钥对")
    s1.add_argument("--count", type=int, default=1, help="生成几对")

    s2 = sub.add_parser("gen-server", help="生成服务端配置")
    s2.add_argument("--port", type=int, default=51820)
    s2.add_argument("--network", default="10.10.0.0/24")
    s2.add_argument("--output", default="wg0-server.conf")

    s3 = sub.add_parser("gen-client", help="生成客户端配置")
    s3.add_argument("--name", required=True, help="客户端名称")
    s3.add_argument("--server-pubkey", required=True, help="服务端公钥")
    s3.add_argument("--server-endpoint", required=True, help="服务端地址:端口")
    s3.add_argument("--ip", default="10.10.0.2", help="客户端 IP")
    s3.add_argument("--dns", default="10.0.0.1")
    s3.add_argument("--qr", action="store_true", help="生成二维码")
    s3.add_argument("--output", default="")

    args = p.parse_args()
    if args.cmd == "gen-keys":
        for i in range(args.count):
            priv, pub = gen_keypair()
            print(f"密钥对 {i+1}:")
            print(f"  私钥: {priv}")
            print(f"  公钥: {pub}")
    elif args.cmd == "gen-server":
        priv, _ = gen_keypair()
        cfg = gen_server_config(priv, args.port, args.network)
        with open(args.output, "w") as f: f.write(cfg)
        print(f"✅ 服务端配置已保存: {args.output}")
        print(f"  服务端公钥（给客户端用）: {_}")
    elif args.cmd == "gen-client":
        priv, pub = gen_keypair()
        cfg = gen_client_config(args.name, priv, args.server_pubkey, args.server_endpoint, args.ip, args.dns)
        out = args.output or f"wg-{args.name}.conf"
        with open(out, "w") as f: f.write(cfg)
        print(f"✅ 客户端配置已保存: {out}")
        if args.qr:
            gen_qr_code(cfg, out.replace(".conf", ".png"))
    else:
        p.print_help()
