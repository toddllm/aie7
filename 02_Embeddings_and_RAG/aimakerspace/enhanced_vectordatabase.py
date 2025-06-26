"""
Enhanced Vector Database with metadata support and multiple distance metrics.
"""

import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional, Callable
from datetime import datetime
import json

from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.distance_metrics import (
    cosine_similarity, 
    get_distance_metric,
    DISTANCE_METRICS
)


class EnhancedVectorDatabase:
    """
    Vector database with metadata support and multiple distance metrics.
    
    Features:
    - Multiple distance metrics (cosine, euclidean, manhattan, etc.)
    - Metadata storage and filtering
    - Timestamp tracking
    - Source attribution
    """
    
    def __init__(self, embedding_model: EmbeddingModel = None, distance_metric: str = "cosine"):
        self.vectors = defaultdict(np.array)
        self.metadata = defaultdict(dict)
        self.embedding_model = embedding_model or EmbeddingModel()
        self.distance_metric_name = distance_metric
        self.distance_measure = get_distance_metric(distance_metric)
        
    def insert(self, key: str, vector: np.array, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Insert a vector with optional metadata.
        
        Args:
            key: The text content
            vector: The embedding vector
            metadata: Optional metadata dictionary
        """
        self.vectors[key] = vector
        
        # Add default metadata
        default_metadata = {
            "timestamp": datetime.now().isoformat(),
            "vector_dim": len(vector),
            "distance_metric": self.distance_metric_name
        }
        
        if metadata:
            default_metadata.update(metadata)
            
        self.metadata[key] = default_metadata
    
    def search(
        self,
        query_vector: np.array,
        k: int,
        distance_measure: Optional[Callable] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors with optional metadata filtering.
        
        Args:
            query_vector: The query embedding
            k: Number of results to return
            distance_measure: Optional custom distance measure
            metadata_filter: Optional metadata constraints
            
        Returns:
            List of tuples (text, score, metadata)
        """
        if distance_measure is None:
            distance_measure = self.distance_measure
            
        # Apply metadata filter if provided
        candidates = self.vectors.items()
        if metadata_filter:
            candidates = [
                (key, vector) for key, vector in candidates
                if self._matches_filter(self.metadata[key], metadata_filter)
            ]
        
        # Calculate scores
        scores = [
            (key, distance_measure(query_vector, vector), self.metadata[key])
            for key, vector in candidates
        ]
        
        # Sort and return top k
        return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    
    def search_by_text(
        self,
        query_text: str,
        k: int,
        distance_measure: Optional[Callable] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        return_as_text: bool = False,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search by text query with optional metadata filtering.
        """
        query_vector = self.embedding_model.get_embedding(query_text)
        results = self.search(query_vector, k, distance_measure, metadata_filter)
        
        if return_as_text:
            return [(result[0], result[2]) for result in results]
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """
        Check if metadata matches the filter criteria.
        
        Supports:
        - Exact match: {"source": "paper.pdf"}
        - List membership: {"source": ["paper1.pdf", "paper2.pdf"]}
        - Range queries: {"page": {"$gte": 10, "$lte": 20}}
        """
        for key, filter_value in filter_dict.items():
            if key not in metadata:
                return False
                
            meta_value = metadata[key]
            
            # Exact match
            if isinstance(filter_value, (str, int, float, bool)):
                if meta_value != filter_value:
                    return False
                    
            # List membership
            elif isinstance(filter_value, list):
                if meta_value not in filter_value:
                    return False
                    
            # Range queries
            elif isinstance(filter_value, dict):
                for op, val in filter_value.items():
                    if op == "$gte" and meta_value < val:
                        return False
                    elif op == "$lte" and meta_value > val:
                        return False
                    elif op == "$gt" and meta_value <= val:
                        return False
                    elif op == "$lt" and meta_value >= val:
                        return False
                    elif op == "$ne" and meta_value == val:
                        return False
                        
        return True
    
    def update_metadata(self, key: str, metadata_update: Dict[str, Any]) -> None:
        """Update metadata for an existing entry."""
        if key in self.metadata:
            self.metadata[key].update(metadata_update)
            self.metadata[key]["last_updated"] = datetime.now().isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        total_vectors = len(self.vectors)
        
        # Metadata statistics
        metadata_keys = set()
        sources = set()
        
        for meta in self.metadata.values():
            metadata_keys.update(meta.keys())
            if "source" in meta:
                sources.add(meta["source"])
        
        return {
            "total_vectors": total_vectors,
            "distance_metric": self.distance_metric_name,
            "available_metrics": list(DISTANCE_METRICS.keys()),
            "metadata_fields": list(metadata_keys),
            "unique_sources": list(sources),
            "vector_dimensions": self.vectors[next(iter(self.vectors))].shape[0] if total_vectors > 0 else 0
        }
    
    async def abuild_from_list(
        self, 
        list_of_text: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> "EnhancedVectorDatabase":
        """
        Build database from text list with optional metadata.
        
        Args:
            list_of_text: List of text documents
            metadata_list: Optional list of metadata dictionaries
        """
        embeddings = await self.embedding_model.async_get_embeddings(list_of_text)
        
        if metadata_list is None:
            metadata_list = [{}] * len(list_of_text)
            
        for i, (text, embedding) in enumerate(zip(list_of_text, embeddings)):
            metadata = metadata_list[i].copy() if i < len(metadata_list) else {}
            metadata["index"] = i
            self.insert(text, np.array(embedding), metadata)
            
        return self
    
    def save_to_json(self, filepath: str) -> None:
        """Save the database to a JSON file."""
        data = {
            "vectors": {k: v.tolist() for k, v in self.vectors.items()},
            "metadata": dict(self.metadata),
            "distance_metric": self.distance_metric_name
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    @classmethod
    def load_from_json(cls, filepath: str, embedding_model: EmbeddingModel = None) -> "EnhancedVectorDatabase":
        """Load database from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        db = cls(embedding_model, data.get("distance_metric", "cosine"))
        
        for key, vector_list in data["vectors"].items():
            db.vectors[key] = np.array(vector_list)
            
        db.metadata = defaultdict(dict, data["metadata"])
        
        return db