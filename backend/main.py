import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.analyzer import TextAnalyzer
from backend.classifier import EssayClassifier

# Initialize FastAPI
app = FastAPI(title="AI Admissions Essay Detector", description="Local explainable AI detector")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
print("Initializing backend services...")
analyzer = TextAnalyzer()
classifier = EssayClassifier()

class AnalyzeRequest(BaseModel):
    text: str

@app.post("/api/analyze")
async def analyze_text(request: AnalyzeRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    # Check minimum word length (e.g. 20 words for reasonable stats)
    word_count = len(request.text.split())
    if word_count < 15:
        raise HTTPException(
            status_code=400, 
            detail=f"Text is too short ({word_count} words). Please enter at least 15 words to perform analysis."
        )
        
    try:
        raw_analysis = analyzer.analyze(request.text)
        if "error" in raw_analysis:
            raise HTTPException(status_code=400, detail=raw_analysis["error"])
            
        result = classifier.classify_essay(raw_analysis)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/dataset-info")
async def get_dataset_info():
    """Returns metadata about the calibrated dataset and raw essays for samples."""
    dataset_path = "data/dataset.json"
    weights_path = "backend/weights.json"
    
    samples = []
    metadata = {
        "calibrated": False,
        "sample_count": 0,
        "types": {},
        "accuracy": 0.0,
        "feature_weights": {}
    }
    
    # Load samples from dataset.json
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r") as f:
                processed_essays = json.load(f)
                
            # Extract raw samples (we fetch the text from the script's raw list or we re-read the script's dataset)
            # For simplicity, we import the raw essays list from prepare_dataset if available
            try:
                from scripts.prepare_dataset import DATASET
                samples = [{"id": e["id"], "title": e["title"], "type": e["type"], "text": e["text"], "label": e["label"]} for e in DATASET]
            except Exception:
                # Fallback to loading titles and labels from json (without full texts)
                samples = [{"id": e["id"], "title": e["title"], "type": e["type"], "label": e["label"]} for e in processed_essays]
                
            metadata["sample_count"] = len(processed_essays)
            
            # Count by types
            types = {}
            for e in processed_essays:
                t = e["type"]
                types[t] = types.get(t, 0) + 1
            metadata["types"] = types
            metadata["calibrated"] = True
        except Exception as e:
            print(f"Error loading samples in api: {e}")
            
    # Load accuracy and weights from weights.json
    if os.path.exists(weights_path):
        try:
            with open(weights_path, "r") as f:
                w = json.load(f)
            metadata["feature_weights"] = dict(zip(w["feature_names"], w["coefficients"]))
            # Read metadata report file to find LOOCV accuracy
            if os.path.exists("data/dataset_metadata.md"):
                with open("data/dataset_metadata.md", "r") as f:
                    content = f.read()
                    import re
                    match = re.search(r"Overall LOOCV Accuracy:\s+\*\*([\d.]+)%\*\*", content)
                    if match:
                        metadata["accuracy"] = float(match.group(1))
        except Exception as e:
            print(f"Error loading weights info in api: {e}")
            
    return {
        "metadata": metadata,
        "samples": samples
    }

@app.post("/api/calibrate")
async def trigger_calibration():
    """Manually triggers the dataset preparation and calibration script."""
    try:
        from scripts.prepare_dataset import main as run_calibration
        run_calibration()
        # Reload classifier weights
        classifier.load_weights()
        return {"status": "success", "message": "Calibration completed and weights reloaded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")

# Mount built React assets (must be declared AFTER API routes to prevent overlapping)
frontend_dist = "frontend/dist"
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    
    # Fallback to index.html for SPA routing
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    print(f"Warning: '{frontend_dist}' directory not found. Frontend static hosting is disabled. Run the frontend build first.")
    
    @app.get("/")
    def index():
        return {
            "message": "AI Admissions Essay Detector Backend is running. Frontend build missing. Please build the React frontend project."
        }
