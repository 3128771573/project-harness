"""系统监控服务：读取宿主 CPU/内存/磁盘/网络/系统 详细指标

容器内运行时，通过挂载的 /host/proc、/host/sys、/host/os-release 读取宿主机数据。
"""
import os
import time
from datetime import datetime, timezone

# 宿主机路径（docker-compose 已挂载 /proc:/host/proc:ro 等）
_HOST_PROC = "/host/proc" if os.path.isdir("/host/proc") else "/proc"
_HOST_SYS = "/host/sys" if os.path.isdir("/host/sys") else "/sys"
_HOST_OS_RELEASE = "/host/os-release" if os.path.isfile("/host/os-release") else "/etc/os-release"

# 网络速率计算缓存
_net_cache: dict = {"rx_bytes": None, "tx_bytes": None, "ts": None}


def _read_proc(path: str) -> list[str]:
    # 挂载路径是宿主机 /proc 的根；调用方传相对路径
    try:
        with open(f"{_HOST_PROC}/{path}") as f:
            return f.read().splitlines()
    except Exception:
        return []


# ---------- CPU ----------

def _cpu_percent() -> int:
    try:
        with open(f"{_HOST_PROC}/stat") as f:
            line = f.readline().split()
        idle = int(line[4]) + int(line[5])
        total = sum(int(v) for v in line[1:])
        time.sleep(0.4)
        with open(f"{_HOST_PROC}/stat") as f:
            line = f.readline().split()
        idle2 = int(line[4]) + int(line[5])
        total2 = sum(int(v) for v in line[1:])
        d_idle = idle2 - idle
        d_total = total2 - total
        if d_total <= 0:
            return 0
        return max(0, min(100, round(100 * (1 - d_idle / d_total))))
    except Exception:
        return 0


def _cpu_cores() -> int:
    return os.cpu_count() or 1


def _cpu_model() -> str:
    for line in _read_proc("cpuinfo"):
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def _cpu_freq() -> str:
    for line in _read_proc("cpuinfo"):
        if line.lower().startswith("cpu mhz"):
            try:
                return f"{float(line.split(':')[1].strip()) / 1000:.2f} GHz"
            except Exception:
                break
    return "—"


def _load_avg() -> list[float]:
    try:
        with open(f"{_HOST_PROC}/loadavg") as f:
            parts = f.read().split()
        return [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        return [0, 0, 0]


def _process_count() -> int:
    try:
        with open(f"{_HOST_PROC}/loadavg") as f:
            parts = f.read().split()
        # 格式: "running/total" 第4段
        return int(parts[3].split("/")[1])
    except Exception:
        return 0


# ---------- 内存 ----------

def _mem_info() -> dict:
    info = {}
    for line in _read_proc("meminfo"):
        parts = line.split()
        if len(parts) >= 2:
            info[parts[0].rstrip(":")] = int(parts[1])  # KB
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = total - available
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    return {
        "total_gb": round(total / 1024 / 1024, 1),
        "used_gb": round(used / 1024 / 1024, 1),
        "free_gb": round(info.get("MemFree", 0) / 1024 / 1024, 1),
        "buff_cache_gb": round(info.get("Buffers", 0) / 1024 / 1024 + info.get("Cached", 0) / 1024 / 1024, 1),
        "available_gb": round(available / 1024 / 1024, 1),
        "percent": max(0, min(100, round(100 * used / total))) if total else 0,
        "swap_total_gb": round(swap_total / 1024 / 1024, 1),
        "swap_used_gb": round((swap_total - swap_free) / 1024 / 1024, 1),
    }


# ---------- 磁盘 ----------

def _disk_main() -> dict:
    try:
        s = os.statvfs("/")
        total = s.f_blocks * s.f_frsize
        free = s.f_bavail * s.f_frsize
        used = total - free
        return {
            "mount": "/",
            "total_gb": round(total / 1024**3, 1),
            "used_gb": round(used / 1024**3, 1),
            "free_gb": round(free / 1024**3, 1),
            "percent": max(0, min(100, round(100 * used / total))),
        }
    except Exception:
        return {"mount": "/", "total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


def _disk_mounts() -> list[dict]:
    mounts = []
    try:
        # 读取宿主 PID 1 的 mount 表（容器 /proc/mounts 是容器视角）
        with open(f"{_HOST_PROC}/1/mounts") as f:
            lines = f.read().splitlines()
        seen = set()
        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue
            dev, mount, fstype = parts[0], parts[1], parts[2]
            # 只统计真实块设备，跳过虚拟文件系统
            if not dev.startswith("/dev/"):
                continue
            if fstype in ("proc", "sysfs", "devpts", "tmpfs", "overlay", "cgroup", "cgroup2"):
                continue
            if mount in seen:
                continue
            seen.add(mount)
            try:
                s = os.statvfs(mount)
                total = s.f_blocks * s.f_frsize
                free = s.f_bavail * s.f_frsize
                used = total - free
                mounts.append({
                    "device": dev,
                    "mount": mount,
                    "total_gb": round(total / 1024**3, 1),
                    "used_gb": round(used / 1024**3, 1),
                    "free_gb": round(free / 1024**3, 1),
                    "percent": max(0, min(100, round(100 * used / total))) if total else 0,
                })
            except Exception:
                continue
    except Exception:
        pass
    return mounts


# ---------- 网络 ----------

def _net_speed() -> dict:
    """返回 rx/tx KB/s（基于两次采样差值，读取宿主 PID 1 的网络栈）"""
    try:
        rx = tx = 0
        for line in _read_proc("1/net/dev"):
            if ":" not in line:
                continue
            iface, rest = line.split(":", 1)
            iface = iface.strip()
            if iface == "lo":
                continue
            vals = rest.split()
            if len(vals) >= 9:
                rx += int(vals[0])      # receive bytes
                tx += int(vals[8])      # transmit bytes

        now = time.time()
        prev_rx = _net_cache.get("rx_bytes")
        prev_tx = _net_cache.get("tx_bytes")
        prev_ts = _net_cache.get("ts")
        speed = {"rx_kbs": 0, "tx_kbs": 0, "rx_total_gb": round(rx / 1024**3, 2), "tx_total_gb": round(tx / 1024**3, 2)}

        if prev_rx is not None and prev_ts and (now - prev_ts) > 0:
            dt = now - prev_ts
            speed["rx_kbs"] = round(max(0, rx - prev_rx) / dt / 1024, 1)
            speed["tx_kbs"] = round(max(0, tx - prev_tx) / dt / 1024, 1)

        _net_cache.update(rx_bytes=rx, tx_bytes=tx, ts=now)
        return speed
    except Exception:
        return {"rx_kbs": 0, "tx_kbs": 0, "rx_total_gb": 0, "tx_total_gb": 0}


def _net_ips() -> list[str]:
    ips = []
    try:
        # 读取宿主 PID 1 的所有接口 IP（/proc/1/net/fib_trie 或 /proc/1/net/route 结合）
        import re

        try:
            with open(f"{_HOST_PROC}/1/net/fib_trie") as f:
                content = f.read()
            for ip in re.findall(r"\d+\.\d+\.\d+\.\d+", content):
                if not ip.startswith(("127.", "0.", "172.17", "172.18", "172.19", "172.20", "169.254")):
                    if ip not in ips:
                        ips.append(ip)
        except Exception:
            pass

        # 若上面拿不到，退化为 UDP 探测主 IP
        if not ips:
            import socket

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ips.append(s.getsockname()[0])
            finally:
                s.close()
    except Exception:
        pass
    return ips[:3]


# ---------- 系统 ----------

def _hostname() -> str:
    # 宿主机名（挂载的 /etc/hostname）
    for p in ("/host/etc-hostname", "/host/proc/sys/kernel/hostname"):
        try:
            with open(p) as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            continue
    try:
        import socket

        return socket.gethostname()
    except Exception:
        return "unknown"


def _os_release() -> str:
    try:
        with open(_HOST_OS_RELEASE) as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "Linux"


def _kernel() -> str:
    for line in _read_proc("version"):
        parts = line.split()
        if len(parts) > 2:
            return parts[2]
    return "unknown"


def _arch() -> str:
    try:
        import platform

        return platform.machine()
    except Exception:
        return "unknown"


def _uptime() -> str:
    try:
        with open(f"{_HOST_PROC}/uptime") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        if days > 0:
            return f"{days} 天 {hours} 小时 {minutes} 分"
        if hours > 0:
            return f"{hours} 小时 {minutes} 分"
        return f"{minutes} 分"
    except Exception:
        return "unknown"


def _temps() -> list[dict]:
    """读取 CPU 温度（thermal zones，宿主机 /sys）"""
    temps = []
    try:
        import glob

        for path in sorted(glob.glob(f"{_HOST_SYS}/class/thermal/thermal_zone*/temp")):
            try:
                with open(path) as f:
                    raw = int(f.read().strip()) / 1000
                with open(path.replace("/temp", "/type")) as f:
                    name = f.read().strip()
                temps.append({"name": name, "temp": round(raw, 1)})
            except Exception:
                continue
    except Exception:
        pass
    return temps


def get_system_status() -> dict:
    """汇总系统详细指标"""
    disk_main = _disk_main()
    return {
        "cpu": {
            "percent": _cpu_percent(),
            "cores": _cpu_cores(),
            "model": _cpu_model(),
            "freq": _cpu_freq(),
            "load": _load_avg(),
        },
        "memory": _mem_info(),
        "disk": {
            "main": disk_main,
            "mounts": _disk_mounts(),
        },
        "network": _net_speed(),
        "system": {
            "hostname": _hostname(),
            "os": _os_release(),
            "kernel": _kernel(),
            "arch": _arch(),
            "uptime": _uptime(),
            "processes": _process_count(),
            "ip": _net_ips(),
        },
        "temps": _temps(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
