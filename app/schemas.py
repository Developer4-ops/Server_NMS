# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import asyncio

from models import Device, CpuMetric, MemoryMetric, DiskMetric, NetworkMetric  # your SQLAlchemy models

DATABASE_URL = "postgresql+asyncpg://nms_server: server@localhost:5432/yourdb"

# -------------------------------
# Database setup
# -------------------------------
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# -------------------------------
# FastAPI setup
# -------------------------------
app = FastAPI(title="Device Monitoring API", version="1.0")

# -------------------------------
# Pydantic models for response
# -------------------------------
class Metrics(BaseModel):
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    disk_usage_percent: Optional[float]
    network_in_bytes: Optional[int]
    network_out_bytes: Optional[int]

class DeviceResponse(BaseModel):
    id: int
    uuid: str
    hostname: str
    ip_address: str
    status: str
    type_id: int
    location_id: int
    is_active: bool
    last_seen: Optional[datetime]
    created_at: datetime
    metrics: Optional[Metrics]

# -------------------------------
# Utility functions to fetch metrics
# -------------------------------
async def get_device_metrics(ip_address: str) -> Metrics:
    """
    Fetch real-time metrics for a device by its IP address.
    """
    async with async_session() as session:
        # 1. Get latest CPU metric
        cpu_result = await session.execute(
            text("""
                SELECT cpu_usage_percent FROM cpu_metrics cm
                JOIN devices d ON cm.device_id = d.id
                WHERE d.ip_address = :ip
                ORDER BY cm.timestamp DESC LIMIT 1
            """), {"ip": ip_address}
        )
        cpu_row = cpu_result.fetchone()
        cpu_usage = float(cpu_row[0]) if cpu_row else None

        # 2. Get latest Memory metric
        mem_result = await session.execute(
            text("""
                SELECT usage_percent FROM memory_metrics mm
                JOIN devices d ON mm.device_id = d.id
                WHERE d.ip_address = :ip
                ORDER BY mm.timestamp DESC LIMIT 1
            """), {"ip": ip_address}
        )
        mem_row = mem_result.fetchone()
        mem_usage = float(mem_row[0]) if mem_row else None

        # 3. Get latest Disk metric (average usage percent)
        disk_result = await session.execute(
            text("""
                SELECT AVG(usage_percent) FROM disk_metrics dm
                JOIN devices d ON dm.device_id = d.id
                WHERE d.ip_address = :ip
            """), {"ip": ip_address}
        )
        disk_row = disk_result.fetchone()
        disk_usage = float(disk_row[0]) if disk_row and disk_row[0] is not None else None

        # 4. Get latest Network metrics (sum of bytes)
        net_result = await session.execute(
            text("""
                SELECT SUM(bytes_recv), SUM(bytes_sent) FROM network_metrics nm
                JOIN devices d ON nm.device_id = d.id
                WHERE d.ip_address = :ip
            """), {"ip": ip_address}
        )
        net_row = net_result.fetchone()
        network_in = int(net_row[0]) if net_row and net_row[0] is not None else None
        network_out = int(net_row[1]) if net_row and net_row[1] is not None else None

        return Metrics(
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=mem_usage,
            disk_usage_percent=disk_usage,
            network_in_bytes=network_in,
            network_out_bytes=network_out
        )

# -------------------------------
# API Endpoints
# -------------------------------
@app.get("/", summary="Root Endpoint")
async def root():
    return "Device Monitoring API is running"

@app.get("/devices/", response_model=List[DeviceResponse], summary="Get all devices with metrics")
async def get_devices():
    """
    Returns all devices from the database with latest real-time metrics.
    """
    async with async_session() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()

        response = []
        for device in devices:
            metrics = await get_device_metrics(str(device.ip_address))
            device_data = DeviceResponse(
                id=device.id,
                uuid=str(device.uuid),
                hostname=device.hostname,
                ip_address=str(device.ip_address),
                status=device.status,
                type_id=device.type_id,
                location_id=device.location_id,
                is_active=device.is_active,
                last_seen=device.last_seen,
                created_at=device.created_at,
                metrics=metrics
            )
            response.append(device_data)

        return response

@app.get("/devices/{ip_address}", response_model=DeviceResponse, summary="Get device by IP with metrics")
async def get_device_by_ip(ip_address: str):
    """
    Returns a single device and its latest metrics by IP address.
    """
    async with async_session() as session:
        result = await session.execute(select(Device).where(Device.ip_address == ip_address))
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        metrics = await get_device_metrics(ip_address)

        return DeviceResponse(
            id=device.id,
            uuid=str(device.uuid),
            hostname=device.hostname,
            ip_address=str(device.ip_address),
            status=device.status,
            type_id=device.type_id,
            location_id=device.location_id,
            is_active=device.is_active,
            last_seen=device.last_seen,
            created_at=device.created_at,
            metrics=metrics
        )
