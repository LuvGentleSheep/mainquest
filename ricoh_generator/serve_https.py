#!/usr/bin/env python3
"""
局域网 HTTPS 测试服务器
─────────────────────────
用途：让 iOS 设备在局域网内通过 HTTPS 访问 PWA，
      使 Web Share API（带文件分享）正常工作。

使用方法：
  cd ricoh_generator
  python3 serve_https.py

首次运行会自动生成自签名证书 (cert.pem / key.pem)。
iOS 设备访问时会提示"不安全"，点击"继续访问"即可。
"""

import http.server
import ssl
import os
import subprocess
import socket
import sys

PORT = 4443
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"


def get_lan_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def generate_cert():
    """用 openssl 生成自签名证书（含局域网 IP 作为 SAN）"""
    ip = get_lan_ip()
    print(f"📋 为 {ip} 生成自签名 SSL 证书...")

    # 生成包含 SAN 的自签名证书，有效期 365 天
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", KEY_FILE, "-out", CERT_FILE,
        "-days", "365", "-nodes",
        "-subj", f"/CN={ip}/O=GR-Canvas-Dev",
        "-addext", f"subjectAltName=IP:{ip},DNS:localhost,IP:127.0.0.1"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 证书生成失败: {result.stderr}")
        sys.exit(1)
    print(f"✅ 证书已生成: {CERT_FILE}, {KEY_FILE}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 如果证书不存在则自动生成
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        generate_cert()

    ip = get_lan_ip()

    # 创建 HTTPS 服务器
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("0.0.0.0", PORT), handler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print()
    print("=" * 52)
    print("  GR IV Canvas - HTTPS 测试服务器")
    print("=" * 52)
    print(f"  本机访问: https://localhost:{PORT}")
    print(f"  局域网:   https://{ip}:{PORT}")
    print("-" * 52)
    print('  iOS 首次访问会提示「不安全连接」')
    print('  -> Safari: 点击「显示详细信息」->「访问此网站」')
    print('  -> 主屏PWA: 需先在 Safari 中信任一次')
    print("-" * 52)
    print("  Ctrl+C 停止服务器")
    print("=" * 52)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
