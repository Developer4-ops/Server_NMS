# server_agent.py
import time
import psutil
import requests
import socket
from datetime import datetime

# CONFIG
SERVER_IP = "192.168.0.108"
NMS_API = "http://127.0.0.1:8000/devices/metrics/collect"

def get_local_ip():
    """Automatically detect the primary IP of this server."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def normalize_cpu_metrics(cpu_times):
    """Normalize CPU times to percentages to avoid DB numeric overflow."""
    total = cpu_times.user + cpu_times.system + cpu_times.idle + getattr(cpu_times, "iowait", 0.0)
    if total == 0:
        return 0.0, 0.0, 0.0, 0.0
    cpu_user_percent = min(max((cpu_times.user / total) * 100, 0), 999.99)
    cpu_system_percent = min(max((cpu_times.system / total) * 100, 0), 999.99)
    cpu_idle_percent = min(max((cpu_times.idle / total) * 100, 0), 999.99)
    cpu_iowait_percent = min(max((getattr(cpu_times, "iowait", 0.0) / total) * 100, 0), 999.99)
    return cpu_user_percent, cpu_system_percent, cpu_idle_percent, cpu_iowait_percent

def get_cpu_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_times = psutil.cpu_times()
    load1, load5, load15 = psutil.getloadavg()
    
    cpu_user, cpu_system, cpu_idle, cpu_iowait = normalize_cpu_metrics(cpu_times)

    return {
        "cpu_usage_percent": cpu_percent,
        "cpu_user": cpu_user,
        "cpu_system": cpu_system,
        "cpu_idle": cpu_idle,
        "cpu_iowait": cpu_iowait,
        "load_avg_1": load1,
        "load_avg_5": load5,
        "load_avg_15": load15,
        "core_count": psutil.cpu_count()
    }

def get_memory_metrics():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_mb": mem.total // (1024 * 1024),
        "used_mb": mem.used // (1024 * 1024),
        "free_mb": mem.free // (1024 * 1024),
        "available_mb": mem.available // (1024 * 1024),
        "usage_percent": mem.percent,
        "swap_total_mb": swap.total // (1024 * 1024),
        "swap_used_mb": swap.used // (1024 * 1024),
        "swap_free_mb": swap.free // (1024 * 1024)
    }

def get_disk_metrics():
    disks = []
    io_counters = psutil.disk_io_counters(perdisk=True)
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        io = io_counters.get(part.device.split('/')[-1], psutil._common.sdiskio(0,0,0,0,0,0))
        disks.append({
            "mount_point": part.mountpoint,
            "device_name": part.device,
            "filesystem_type": part.fstype,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "usage_percent": usage.percent,
            "inode_usage_percent": 0,
            "read_bytes": io.read_bytes,
            "write_bytes": io.write_bytes,
            "read_ops": io.read_count if hasattr(io, "read_count") else 0,
            "write_ops": io.write_count if hasattr(io, "write_count") else 0
        })
    return disks

def get_network_metrics():
    nets = []
    io_counters = psutil.net_io_counters(pernic=True)
    stats = psutil.net_if_stats()
    for iface, data in io_counters.items():
        nets.append({
            "interface_name": iface,
            "bytes_sent": data.bytes_sent,
            "bytes_recv": data.bytes_recv,
            "packets_sent": data.packets_sent,
            "packets_recv": data.packets_recv,
            "errors_in": data.errin,
            "errors_out": data.errout,
            "drops_in": data.dropin,
            "drops_out": data.dropout,
            "speed_mbps": stats[iface].speed if iface in stats else 0,
            "status": "UP" if stats.get(iface, None) and stats[iface].isup else "DOWN"
        })
    return nets

def collect_and_send_metrics():
    server_ip = get_local_ip()
    payload = {
        "device_ip": server_ip,
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": get_cpu_metrics(),
        "memory": get_memory_metrics(),
        "disk": get_disk_metrics(),
        "network": get_network_metrics()
    }
    try:
        r = requests.post(NMS_API, json=payload)
        print(f"[{datetime.now()}] IP {server_ip} - Status: {r.status_code}, Response: {r.json()}")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send metrics:", e)

if __name__ == "__main__":
    print("Starting Server Metrics Agent...")
    while True:
        collect_and_send_metrics()
        time.sleep(30)  # every 30 seconds
