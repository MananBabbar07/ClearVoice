import requests
import time
import csv

API_URL = "https://manan77709-clearvoice-api.hf.space"

TEST_CLAIMS = [
    "antibiotics can cure the flu",
    "exercise reduces risk of heart disease",
    "smoking causes lung cancer",
    "vitamin C prevents colds",
    "vaccines cause autism",
    "obesity is linked to type 2 diabetes",
    "drinking bleach cures infections",
    "high blood pressure increases stroke risk",
    "sugar causes diabetes",
    "stress causes high blood pressure",
]