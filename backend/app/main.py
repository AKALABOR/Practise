import logging
import hashlib
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional
from . import models, schemas, database
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from .blockchain import send_data_to_blockchain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Measurement API",
    description="Практика по Апі з сенсорами",
    version="1.0.0"
)

def calculate_hash(sensor_id, value, unit, prev_hash):
    data_string = f"{sensor_id}{value}{unit}{prev_hash}"
    return hashlib.sha256(data_string.encode()).hexdigest()


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "measurement-service"}

@app.post("/measurements/", response_model=schemas.MeasurementResponse, tags=["Blockchain"], status_code=201)
async def create_measurement(
    item: schemas.MeasurementCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db)
):
    last_record_query = select(models.Measurement).order_by(desc(models.Measurement.id)).limit(1)
    result = await db.execute(last_record_query)
    last_record = result.scalar_one_or_none()

    if last_record:
        previous_hash = last_record.data_hash
    else:
        previous_hash = "GENESIS_BLOCK"

    current_hash = calculate_hash(item.sensor_id, item.value, item.unit, previous_hash)

    db_item = models.Measurement(
        sensor_id=item.sensor_id,
        value=item.value,
        unit=item.unit,
        metadata_info=item.metadata_info,
        prev_hash=previous_hash,
        data_hash=current_hash
    )
    
    db.add(db_item)
    
    try:
        await db.commit()
        await db.refresh(db_item)
        location = "Unknown"
        if item.metadata_info and "location" in item.metadata_info:
            location = item.metadata_info["location"]
        background_tasks.add_task(send_data_to_blockchain, item.sensor_id, item.value, location)
        return db_item
    except Exception as e:
        logger.error(f"Помилка при збереженні: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Помилка бази даних")

@app.get("/measurements/", response_model=List[schemas.MeasurementResponse], tags=["Measurements"])
async def read_measurements(
    skip: int = Query(0, description="Скільки записів пропустити"),
    limit: int = Query(100, description="Максимальна кількість записів"),
    sensor_id: Optional[int] = Query(None, description="Фільтр за ID сенсора"),
    start_date: Optional[datetime] = Query(None, description="Початкова дата"),
    end_date: Optional[datetime] = Query(None, description="Кінцева дата"),
    location: Optional[str] = Query(None, description="Фільтр за містом на англійській"),
    db: AsyncSession = Depends(database.get_db)
):
    query = select(models.Measurement)
    if sensor_id is not None:
        query = query.filter(models.Measurement.sensor_id == sensor_id)
    if start_date:
        query = query.filter(models.Measurement.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.Measurement.recorded_at <= end_date)
    if location:
        query = query.filter(models.Measurement.metadata_info.op("->>")("location") == location)
    query = query.order_by(desc(models.Measurement.recorded_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.put("/measurements/{m_id}", response_model=schemas.MeasurementResponse, tags=["Measurements"])
async def update_measurement(m_id: int, item: schemas.MeasurementUpdate, db: AsyncSession = Depends(database.get_db)):

    result = await db.execute(select(models.Measurement).filter(models.Measurement.id == m_id))
    db_item = result.scalar_one_or_none()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    if item.value is not None:
        db_item.value = item.value
    if item.metadata_info is not None:
        db_item.metadata_info = item.metadata_info
        
    try:
        await db.commit()
        await db.refresh(db_item)
        return db_item
    except Exception as e:
        logger.error(f"Помилка при оновленні: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Помилка бази даних")

@app.delete("/measurements/{m_id}", tags=["Measurements"], status_code=204)
async def delete_measurement(m_id: int, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Measurement).filter(models.Measurement.id == m_id))
    db_item = result.scalar_one_or_none()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
        
    try:
        await db.delete(db_item)
        await db.commit()
        return None
    except Exception as e:
        logger.error(f"Помилка при видаленні: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Помилка бази даних")

@app.get("/blockchain/verify", tags=["Blockchain"])
async def verify_chain(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Measurement).order_by(models.Measurement.id))
    chain = result.scalars().all()

    errors = []
    
    for i in range(len(chain)):
        current_block = chain[i]
        
        if i == 0:
            if current_block.prev_hash != "GENESIS_BLOCK":
                errors.append(f"Block {current_block.id}: Invalid Genesis Hash")
        else:
            previous_block = chain[i-1]
            if current_block.prev_hash != previous_block.data_hash:
                errors.append(f"Block {current_block.id}: Broken Link! PrevHash doesn't match Block {previous_block.id}")

        recalculated_hash = calculate_hash(
            current_block.sensor_id, 
            float(current_block.value),
            current_block.unit, 
            current_block.prev_hash
        )
        
        if current_block.data_hash != recalculated_hash:
             errors.append(f"Block {current_block.id}: Data Tampered! Hash mismatch.")

    if errors:
        return {"status": "CORRUPTED", "errors": errors}
    
    return {"status": "SECURE", "length": len(chain)}