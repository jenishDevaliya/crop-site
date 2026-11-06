import os
import pickle
from functools import lru_cache
from django.conf import settings

@lru_cache(maxsize=1)
def load_bundle():
    pkl_path = os.path.join(settings.BASE_DIR, 'recommender', 'ml', 'Crop_recommendation_RF.pkl')

    with open(pkl_path, 'rb') as f:
        obj = pickle.load(f)

    # obj IS ALREADY a dict → just map keys correctly
    return {
        "model": obj["model"],
        "feature_cols": obj["features_cols"],   # <-- IMPORTANT FIX
        "classes": obj.get("classes", None)
    }


def predict_one(feature_dict):
    bundle = load_bundle()
    model = bundle["model"]
    order = bundle["feature_cols"]

    # build feature row in correct order
    X = [[float(feature_dict[col]) for col in order]]

    pred = model.predict(X)
    return pred[0]
