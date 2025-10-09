# app/main.py
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import (
    Column, Integer, String, Boolean, BigInteger, DECIMAL, TIMESTAMP, text
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.sql import func
from sqlalchemy.future import select

# -----------------------
# Configuration
# -----------------------
DATABASE_URL = "postgresql+asyncpg://nms_server:server@localhost:5432/nms_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

app = FastAPI(title="Server NMS API")

# -----------------------
# Database Models
# -----------------------
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(INET, nullable=False, unique=True)
    manufacturer = Column(String(100))
    model = Column(String(100))
    os_version = Column(String(100))
    is_active = Column(Boolean, server_default=text("true"))
    status = Column(String(20), server_default=text("'unknown'"))
    last_seen = Column(TIMESTAMP(timezone=True))
    uptime_seconds = Column(BigInteger)
    tags = Column(JSONB, server_default=text("'[]'::jsonb"))
    custom_fields = Column(JSONB, server_default=text("'{}'::jsonb"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class CpuMetric(Base):
    __tablename__ = "cpu_metrics"

    device_id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True)
    cpu_usage_percent = Column(DECIMAL(5, 2))
    cpu_user = Column(DECIMAL(5, 2))
    cpu_system = Column(DECIMAL(5, 2))
    cpu_idle = Column(DECIMAL(5, 2))
    cpu_iowait = Column(DECIMAL(5, 2))
    load_avg_1 = Column(DECIMAL(10, 2))
    load_avg_5 = Column(DECIMAL(10, 2))
    load_avg_15 = Column(DECIMAL(10, 2))
    core_count = Column(Integer)


class MemoryMetric(Base):
    __tablename__ = "memory_metrics"

    device_id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True)
    total_mb = Column(BigInteger)
    used_mb = Column(BigInteger)
    free_mb = Column(BigInteger)
    available_mb = Column(BigInteger)
    usage_percent = Column(DECIMAL(5, 2))
    swap_total_mb = Column(BigInteger)
    swap_used_mb = Column(BigInteger)
    swap_free_mb = Column(BigInteger)


class DiskMetric(Base):
    __tablename__ = "disk_metrics"

    device_id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True)
    mount_point = Column(String(255), primary_key=True)
    device_name = Column(String(100))
    filesystem_type = Column(String(50))
    total_gb = Column(DECIMAL(15, 2))
    used_gb = Column(DECIMAL(15, 2))
    free_gb = Column(DECIMAL(15, 2))
    usage_percent = Column(DECIMAL(5, 2))
    inode_usage_percent = Column(DECIMAL(5, 2))
    read_bytes = Column(BigInteger)
    write_bytes = Column(BigInteger)
    read_ops = Column(BigInteger)
    write_ops = Column(BigInteger)


class NetworkMetric(Base):
    __tablename__ = "network_metrics"

    device_id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True)
    interface_name = Column(String(100), primary_key=True)
    bytes_sent = Column(BigInteger)
    bytes_recv = Column(BigInteger)
    packets_sent = Column(BigInteger)
    packets_recv = Column(BigInteger)
    errors_in = Column(BigInteger)
    errors_out = Column(BigInteger)
    drops_in = Column(BigInteger)
    drops_out = Column(BigInteger)
    speed_mbps = Column(Integer)
    status = Column(String(20))

# -----------------------
# Pydantic Schemas
# -----------------------
class DeviceCreate(BaseModel):
    hostname: str
    ip_address: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    tags: Optional[list] = []


class DeviceResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    status: Optional[str] = None

    class Config:
        from_attributes = True


class CpuMetricsSchema(BaseModel):
    cpu_usage_percent: float
    cpu_user: float
    cpu_system: float
    cpu_idle: float
    cpu_iowait: float
    load_avg_1: float
    load_avg_5: float
    load_avg_15: float
    core_count: int


class MemoryMetricsSchema(BaseModel):
    total_mb: int
    used_mb: int
    free_mb: int
    available_mb: int
    usage_percent: float
    swap_total_mb: int
    swap_used_mb: int
    swap_free_mb: int


class DiskMetricsSchema(BaseModel):
    mount_point: str
    device_name: str
    filesystem_type: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    inode_usage_percent: float
    read_bytes: int
    write_bytes: int
    read_ops: int
    write_ops: int


class NetworkMetricsSchema(BaseModel):
    interface_name: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int
    speed_mbps: int
    status: str


class CollectMetricsPayload(BaseModel):
    device_ip: str
    timestamp: Optional[str] = None
    cpu: CpuMetricsSchema
    memory: MemoryMetricsSchema
    disk: List[DiskMetricsSchema]
    network: List[NetworkMetricsSchema]

# -----------------------
# Helpers
# -----------------------
def parse_timestamp(ts: Optional[str]) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        iso = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(iso).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def row_to_dict(instance: Any) -> Dict[str, Any]:
    if instance is None:
        return None
    out = {}
    for col in instance.__table__.columns:
        val = getattr(instance, col.name)
        if isinstance(val, datetime):
            out[col.name] = val.isoformat()
        else:
            out[col.name] = val
    return out

# -----------------------
# API Endpoints
# -----------------------
@app.post("/devices/", response_model=DeviceResponse)
async def create_device(device: DeviceCreate):
    async with async_session() as db:
        existing = (await db.execute(select(Device).where(Device.ip_address == device.ip_address))).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Device with this IP already exists")

        db_device = Device(**device.dict())
        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)
        return DeviceResponse.from_attributes(db_device)


@app.get("/devices/", response_model=List[DeviceResponse])
async def get_devices():
    async with async_session() as db:
        result = await db.execute(select(Device))
        devices = result.scalars().all()
        return [DeviceResponse.from_attributes(d) for d in devices]


@app.post("/devices/metrics/collect", summary="Collect Metrics", description="Agent posts collected CPU, memory, disk, and network metrics.")
async def collect_metrics(payload: CollectMetricsPayload):
    async with async_session() as db:
        # Find device by IP
        result = await db.execute(select(Device).where(Device.ip_address == payload.device_ip))
        device = result.scalars().first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        device_id = device.id
        ts = parse_timestamp(payload.timestamp)

        # Insert metrics
        db.add(CpuMetric(device_id=device_id, timestamp=ts, **payload.cpu.dict()))
        db.add(MemoryMetric(device_id=device_id, timestamp=ts, **payload.memory.dict()))

        for disk_item in payload.disk:
            db.add(DiskMetric(device_id=device_id, timestamp=ts, **disk_item.dict()))

        for net_item in payload.network:
            db.add(NetworkMetric(device_id=device_id, timestamp=ts, **net_item.dict()))

        # Update device status
        device.last_seen = ts
        device.status = "online"
        db.add(device)
        await db.commit()

    return {"detail": "Metrics collected successfully"}


@app.get("/devices/{ip_address}/metrics")
async def get_device_metrics(ip_address: str):
    """Return latest metrics for a device identified by IP."""
    async with async_session() as db:
        result = await db.execute(select(Device).where(Device.ip_address == ip_address))
        device = result.scalars().first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        device_id = device.id

        # Latest CPU metrics
        cpu = (
            await db.execute(
                select(CpuMetric)
                .where(CpuMetric.device_id == device_id)
                .order_by(CpuMetric.timestamp.desc())
            )
        ).scalars().first()

        # Latest Memory metrics
        memory = (
            await db.execute(
                select(MemoryMetric)
                .where(MemoryMetric.device_id == device_id)
                .order_by(MemoryMetric.timestamp.desc())
            )
        ).scalars().first()

        # Latest Disk metrics
        disk_list = []
        mounts = (
            await db.execute(
                select(DiskMetric.mount_point)
                .where(DiskMetric.device_id == device_id)
                .distinct()
            )
        ).scalars().all()

        for mount in mounts:
            disk_item = (
                await db.execute(
                    select(DiskMetric)
                    .where(DiskMetric.device_id == device_id, DiskMetric.mount_point == mount)
                    .order_by(DiskMetric.timestamp.desc())
                )
            ).scalars().first()
            if disk_item:
                disk_list.append(row_to_dict(disk_item))

        # Latest Network metrics
        network_list = []
        interfaces = (
            await db.execute(
                select(NetworkMetric.interface_name)
                .where(NetworkMetric.device_id == device_id)
                .distinct()
            )
        ).scalars().all()

        for iface in interfaces:
            net_item = (
                await db.execute(
                    select(NetworkMetric)
                    .where(NetworkMetric.device_id == device_id, NetworkMetric.interface_name == iface)
                    .order_by(NetworkMetric.timestamp.desc())
                )
            ).scalars().first()
            if net_item:
                network_list.append(row_to_dict(net_item))

        return {
            "device": {
                "id": device.id,
                "hostname": device.hostname,
                "ip_address": str(device.ip_address),
                "status": device.status,
            },
            "metrics": {
                "cpu": row_to_dict(cpu) if cpu else None,
                "memory": row_to_dict(memory) if memory else None,
                "disk": disk_list,
                "network": network_list,
            },
        }
