import os
import sys
import subprocess
import webbrowser
import socket
from contextlib import suppress


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def print_preview_urls(port: str, path: str = "") -> None:
    local_url = f"http://localhost:{port}{path}"
    lan_ip = get_lan_ip()
    lan_url = f"http://{lan_ip}:{port}{path}"
    print("本地服务器已启动，预览地址：")
    print(f"  - 本机: {local_url}")
    if lan_ip.startswith("127."):
        print("  - 局域网: 无法检测到有效的局域网 IP")
    else:
        print(f"  - 局域网: {lan_url}")


def free_port(port: str) -> None:
    """Force close any process that currently occupies the given port."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True, check=False
        )
        lines = [line for line in result.stdout.strip().split("\n") if line]
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    print(f"关闭占用端口 {port} 的进程 PID: {pid}")
                    with suppress(subprocess.SubprocessError):
                        subprocess.run(["kill", "-9", pid], check=False)
    except FileNotFoundError:
        print("未找到 lsof 命令，跳过端口检查。")
    except Exception as exc:
        print(f"释放端口失败: {exc}")


def main() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    port = os.environ.get("RUN_WEBSITE_PORT", "8000")

    print(f"准备在 {project_root} 启动本地服务器，端口：{port}")
    free_port(port)

    server_cmd = [sys.executable, "-m", "http.server", port]
    server_process = subprocess.Popen(server_cmd, cwd=project_root)
    preview_path = "/homepage/homepage_index.html"
    preview_url = f"http://localhost:{port}{preview_path}"

    print_preview_urls(port, preview_path)
    webbrowser.open(preview_url)

    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭服务器...")
    finally:
        server_process.terminate()
        with suppress(subprocess.TimeoutExpired):
            server_process.wait(timeout=5)
        print("服务器已停止。")


if __name__ == "__main__":
    main()
