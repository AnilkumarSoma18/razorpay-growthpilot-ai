
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import pandas as pd
import numpy as np
import json
from app.ml.recommendation_model import RecommendationModel
import uuid

def generate_synthetic_interactions():
    # Simulate data extracting from backend/database
    products = [str(uuid.uuid4()) for _ in range(10)]
    customers = [str(uuid.uuid4()) for _ in range(50)]
    
    data = []
    for c in customers:
        # Simulate some customers buying related products (e.g. 0 and 1 together)
        if np.random.rand() > 0.5:
            data.append({"customer_id": c, "product_id": products[0], "interaction_type": "purchase", "timestamp": "2026-01-01"})
            data.append({"customer_id": c, "product_id": products[1], "interaction_type": "purchase", "timestamp": "2026-01-01"})
            
        # Random noise
        data.append({"customer_id": c, "product_id": np.random.choice(products), "interaction_type": "view", "timestamp": "2026-01-02"})
        
    return pd.DataFrame(data), products, customers

if __name__ == "__main__":
    df, products, customers = generate_synthetic_interactions()
    
    # Train-test split (Temporal)
    # Since this is synthetic static, we just split by arbitrary rows for demonstration
    train_df = df.iloc[:int(len(df)*0.8)]
    test_df = df.iloc[int(len(df)*0.8):]
    
    model = RecommendationModel(version="1.0-alpha")
    model.train(train_df)
    
    # Evaluation (Precision@K)
    k = 2
    hits = 0
    total = 0
    for c in test_df['customer_id'].unique():
        hist = train_df[train_df['customer_id'] == c]['product_id'].tolist()
        actual_future = test_df[(test_df['customer_id'] == c) & (test_df['interaction_type'] == 'purchase')]['product_id'].tolist()
        
        if not actual_future:
            continue
            
        candidates = [{"id": p} for p in products]
        ranked = model.predict_rank(candidates, customer_history=hist)
        top_k = [r['product']['id'] for r in ranked[:k]]
        
        if any(p in top_k for p in actual_future):
            hits += 1
        total += 1
        
    precision_at_k = hits / total if total > 0 else 0
    
    metrics = {
        "model_version": "1.0-alpha",
        "precision_at_2": precision_at_k,
        "train_samples": len(train_df),
        "test_samples": len(test_df)
    }
    
    os.makedirs("evaluation/results", exist_ok=True)
    with open("evaluation/results/recommendation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Model trained and evaluated. Metrics saved. Precision@2: {precision_at_k}")
