from fastapi import APIRouter, Depends, HTTPException
from api.app.schemas.models import ETAPredictionRequest, ETAPredictionResponse
from api.app.core.security import get_current_user
from src.storage.s3_lake import get_s3_client
import joblib
import pandas as pd
import os

router = APIRouter(prefix="/predict", tags=["Predictions"], dependencies=[Depends(get_current_user)])

# Variable global para cachear el modelo en memoria
_model_cache = {}

def load_latest_model():
    """Descarga el último modelo de MinIO usando boto3 y lo carga en memoria."""
    client = get_s3_client()
    bucket = "ml-models"
    prefix = "models/eta_model/"
    
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' not in response:
            raise HTTPException(status_code=503, detail="Modelo no encontrado en MinIO")
        
        # Obtener el archivo más reciente (ordenado por fecha de modificación)
        latest = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        s3_key = latest['Key']
        
        local_path = "/tmp/latest_model.joblib"
        client.download_file(bucket, s3_key, local_path)
        
        return joblib.load(local_path), s3_key
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando modelo: {str(e)}")

@router.post("/eta", response_model=ETAPredictionResponse)
async def predict_eta(payload: ETAPredictionRequest):
    global _model_cache
    if "model" not in _model_cache:
        _model_cache["model"], _model_cache["version"] = load_latest_model()
    
    model = _model_cache["model"]
    
    # Preparar features
    features = pd.DataFrame([{
        "total_distance_km": payload.total_distance_km,
        "avg_speed_knots": payload.avg_speed_knots,
        "vessel_type_Fishing": 1 if payload.vessel_type == "Fishing" else 0,
        "vessel_type_Passenger": 1 if payload.vessel_type == "Passenger" else 0,
        "vessel_type_Tanker": 1 if payload.vessel_type == "Tanker" else 0,
    }])
    
    try:
        prediction = model.predict(features)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de inferencia: {str(e)}")
        
    return ETAPredictionResponse(
        predicted_eta_hours=float(prediction),
        model_version=_model_cache["version"].split('/')[-1].replace('.joblib', '')
    )
