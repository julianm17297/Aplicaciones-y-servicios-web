from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.database.connection import Base

class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensores.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    magnitud = Column(String(50), nullable=False)
    unidad = Column(String(20), nullable=False)
    valor_minimo = Column(Numeric(12, 4), nullable=False)
    valor_maximo = Column(Numeric(12, 4), nullable=False)