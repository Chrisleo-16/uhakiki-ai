import opendatasets as od

# This library handles the 'Accept Terms' logic better
dataset_url = "https://www.kaggle.com/datasets/sujithmandala/identity-card-tampering-detection"
od.download(dataset_url)