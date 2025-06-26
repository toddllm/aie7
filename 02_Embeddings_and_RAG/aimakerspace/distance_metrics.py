"""
Distance metrics for vector similarity calculations.
Provides multiple distance measures for use in RAG retrieval.
"""

import numpy as np
from typing import Union


def cosine_similarity(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes the cosine similarity between two vectors.
    Range: [-1, 1], where 1 means identical direction.
    """
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def euclidean_distance(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes the Euclidean distance between two vectors.
    Lower values indicate more similarity.
    Note: This returns negative distance for use with max-based sorting.
    """
    distance = np.linalg.norm(vector_a - vector_b)
    return -distance  # Negative so higher values = more similar


def manhattan_distance(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes the Manhattan (L1) distance between two vectors.
    Lower values indicate more similarity.
    Note: This returns negative distance for use with max-based sorting.
    """
    distance = np.sum(np.abs(vector_a - vector_b))
    return -distance  # Negative so higher values = more similar


def dot_product_similarity(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes the dot product between two vectors.
    Higher values indicate more similarity.
    Unlike cosine similarity, this is affected by vector magnitude.
    """
    return np.dot(vector_a, vector_b)


def minkowski_distance(vector_a: np.array, vector_b: np.array, p: float = 3) -> float:
    """
    Computes the Minkowski distance between two vectors.
    When p=1, this is Manhattan distance.
    When p=2, this is Euclidean distance.
    When p→∞, this approaches Chebyshev distance.
    """
    distance = np.sum(np.abs(vector_a - vector_b) ** p) ** (1/p)
    return -distance  # Negative so higher values = more similar


def chebyshev_distance(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes the Chebyshev (L∞) distance between two vectors.
    This is the maximum absolute difference between components.
    """
    distance = np.max(np.abs(vector_a - vector_b))
    return -distance  # Negative so higher values = more similar


def correlation_similarity(vector_a: np.array, vector_b: np.array) -> float:
    """
    Computes Pearson correlation coefficient between two vectors.
    Range: [-1, 1], where 1 means perfect positive correlation.
    This is cosine similarity on mean-centered vectors.
    """
    # Center the vectors
    a_centered = vector_a - np.mean(vector_a)
    b_centered = vector_b - np.mean(vector_b)
    
    # Compute correlation (cosine of centered vectors)
    return cosine_similarity(a_centered, b_centered)


def jaccard_similarity(vector_a: np.array, vector_b: np.array, threshold: float = 0.5) -> float:
    """
    Computes Jaccard similarity for continuous vectors.
    Vectors are binarized using the threshold.
    Range: [0, 1], where 1 means identical sets.
    """
    # Binarize vectors
    a_binary = (vector_a > threshold).astype(int)
    b_binary = (vector_b > threshold).astype(int)
    
    # Compute intersection and union
    intersection = np.sum(a_binary & b_binary)
    union = np.sum(a_binary | b_binary)
    
    if union == 0:
        return 0.0
    
    return intersection / union


# Dictionary mapping metric names to functions
DISTANCE_METRICS = {
    "cosine": cosine_similarity,
    "euclidean": euclidean_distance,
    "manhattan": manhattan_distance,
    "dot_product": dot_product_similarity,
    "minkowski": minkowski_distance,
    "chebyshev": chebyshev_distance,
    "correlation": correlation_similarity,
    "jaccard": jaccard_similarity,
}


def get_distance_metric(name: str):
    """
    Retrieve a distance metric function by name.
    
    Args:
        name: Name of the distance metric
        
    Returns:
        The corresponding distance metric function
        
    Raises:
        ValueError: If the metric name is not recognized
    """
    if name not in DISTANCE_METRICS:
        available = ", ".join(DISTANCE_METRICS.keys())
        raise ValueError(f"Unknown distance metric: {name}. Available metrics: {available}")
    
    return DISTANCE_METRICS[name]