# check_metrics.py
import psutil

def print_cpu_metrics():
    cpu_times = psutil.cpu_times()
    cpu_percent = psutil.cpu_percent(interval=1)
    load1, load5, load15 = psutil.getloadavg()

    print("=== CPU Metrics ===")
    print(f"CPU Usage Percent: {cpu_percent}%")
    print(f"CPU Times: user={cpu_times.user}, system={cpu_times.system}, idle={cpu_times.idle}, iowait={getattr(cpu_times, 'iowait', 0.0)}")
    print(f"Load Average (1,5,15 min): {load1}, {load5}, {load15}")
    print(f"CPU Cores: {psutil.cpu_count()}\n")


def print_memory_metrics():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    print("=== Memory Metrics ===")
    print(f"Total: {mem.total // (1024*1024)} MB")
    print(f"Used: {mem.used // (1024*1024)} MB")
    print(f"Free: {mem.free // (1024*1024)} MB")
    print(f"Available: {mem.available // (1024*1024)} MB")
    print(f"Usage Percent: {mem.percent}%")
    print(f"Swap Total: {swap.total // (1024*1024)} MB")
    print(f"Swap Used: {swap.used // (1024*1024)} MB")
    print(f"Swap Free: {swap.free // (1024*1024)} MB\n")


def print_disk_metrics():
    print("=== Disk Metrics ===")
    io_counters = psutil.disk_io_counters(perdisk=True)
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        io = io_counters.get(part.device.split('/')[-1], psutil._common.sdiskio(0,0,0,0,0,0))
        print(f"Mount Point: {part.mountpoint}")
        print(f"Device: {part.device}, Filesystem: {part.fstype}")
        print(f"Total: {usage.total / (1024**3):.2f} GB, Used: {usage.used / (1024**3):.2f} GB, Free: {usage.free / (1024**3):.2f} GB, Usage: {usage.percent}%")
        print(f"Read Bytes: {io.read_bytes}, Write Bytes: {io.write_bytes}")
        print(f"Read Ops: {getattr(io, 'read_count', 0)}, Write Ops: {getattr(io, 'write_count', 0)}\n")


def print_network_metrics():
    print("=== Network Metrics ===")
    io_counters = psutil.net_io_counters(pernic=True)
    stats = psutil.net_if_stats()
    for iface, data in io_counters.items():
        speed = stats[iface].speed if iface in stats else 0
        status = "UP" if stats.get(iface) and stats[iface].isup else "DOWN"
        print(f"Interface: {iface}")
        print(f"Bytes Sent: {data.bytes_sent}, Bytes Received: {data.bytes_recv}")
        print(f"Packets Sent: {data.packets_sent}, Packets Received: {data.packets_recv}")
        print(f"Errors In: {data.errin}, Errors Out: {data.errout}")
        print(f"Drops In: {data.dropin}, Drops Out: {data.dropout}")
        print(f"Speed: {speed} Mbps, Status: {status}\n")


if __name__ == "__main__":
    print_cpu_metrics()
    print_memory_metrics()
    print_disk_metrics()
    print_network_metrics()
