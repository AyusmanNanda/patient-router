from unittest import result

from ml.train import train
import datetime

def train_model():
    start = datetime.datetime.now()
    result = train()
    end = datetime.datetime.now()
    training_time = end - start
    result["training_time_insec"] = round(training_time.total_seconds(), 2)
    return result