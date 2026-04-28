import pytest
from ml_model_trainer import QuantumKeyQualityClassifier


def test_no_entropy_features_in_training_list():
    clf = QuantumKeyQualityClassifier()
    # features that must NOT appear in input features
    forbidden = {"entropy_score", "shannon_entropy", "min_entropy"}
    # training_feature_names is the final set used for training
    assert not (forbidden & set(clf.training_feature_names)), (
        "Leakage detected: entropy-derived columns present in training features"
    )
