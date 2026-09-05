
import pandas as pd
import numpy as np
import uuid
import json
from datetime import datetime

class RecommendationModel:
    def __init__(self, version="1.0"):
        self.version = version
        self.popular_products = []
        self.co_purchase_matrix = {}
        
    def train(self, df_interactions):
        '''
        df_interactions should contain:
        customer_id, product_id, category, price, interaction_type, timestamp
        '''
        if df_interactions.empty:
            return
            
        # 1. Popularity baseline
        popularity = df_interactions.groupby('product_id').size().reset_index(name='count')
        self.popular_products = popularity.sort_values('count', ascending=False)['product_id'].tolist()
        
        # 2. Co-purchase affinity (Item-Item CF simplified)
        purchases = df_interactions[df_interactions['interaction_type'] == 'purchase']
        if not purchases.empty:
            # cross merge to find co-purchases
            co_purch = pd.merge(purchases[['customer_id', 'product_id']], purchases[['customer_id', 'product_id']], on='customer_id')
            co_purch = co_purch[co_purch['product_id_x'] != co_purch['product_id_y']]
            affinity = co_purch.groupby(['product_id_x', 'product_id_y']).size().reset_index(name='weight')
            
            for _, row in affinity.iterrows():
                p1, p2, w = row['product_id_x'], row['product_id_y'], row['weight']
                if p1 not in self.co_purchase_matrix:
                    self.co_purchase_matrix[p1] = {}
                self.co_purchase_matrix[p1][p2] = w

    def predict_rank(self, candidate_products, customer_history=None):
        '''
        Ranks a list of candidate product dicts.
        Uses personalized co-purchase signals if customer_history (list of product_ids) exists.
        Falls back to popularity.
        '''
        ranked = []
        for p in candidate_products:
            score = 0
            pid = p['id']
            reason = "GENERAL CATALOG RELEVANCE"
            
            # Personalization signal
            if customer_history:
                affinity_score = 0
                for hist_p in customer_history:
                    if hist_p in self.co_purchase_matrix and pid in self.co_purchase_matrix[hist_p]:
                        affinity_score += self.co_purchase_matrix[hist_p][pid]
                if affinity_score > 0:
                    score += affinity_score * 10
                    reason = "PERSONALIZED RECOMMENDATION (Based on your history)"
                    
            # Popularity signal
            if score == 0 and pid in self.popular_products:
                score += (len(self.popular_products) - self.popular_products.index(pid))
                reason = "RULE-BASED (Popular product)"
                
            ranked.append({
                "product": p,
                "score": score,
                "reason": reason,
                "ml_version": self.version
            })
            
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
