from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ------------------------------------------------------------
# Device Registration & Basic Info
# ------------------------------------------------------------
class DeviceBase(BaseModel):
    hostname: Optional[str] = Field(None, description="Device hostname or system name")
    ip_address: str = Field(..., description="Device IP address")
    os: Optional[str] = Field(None, description="Operating System of the device")
    status: Optional[str] = Field("active", description="Device status (active/inactive)")


class DeviceCreate(DeviceBase):
    pass


class Device(DeviceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# Metrics Schema for Device Performance
# ------------------------------------------------------------
class DeviceMetricsBase(BaseModel):
    device_ip: str = Field(..., description="IP of the device that sent the metrics")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    network_sent: Optional[float] = Field(None, description="Network data sent in MB")
    network_received: Optional[float] = Field(None, description="Network data received in MB")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Time when metrics were collected")


class DeviceMetricsCreate(DeviceMetricsBase):
    pass


class DeviceMetrics(DeviceMetricsBase):
    id: int

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# Alert System (for future expansion)
# ------------------------------------------------------------
class AlertBase(BaseModel):
    device_ip: str
    severity: str
    message: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    id: int

    class Config:
        orm_mode = True

