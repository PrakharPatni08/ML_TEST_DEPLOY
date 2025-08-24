# test_mongo_connection.py
from pymongo import MongoClient

uri = "mongodb+srv://prakharpatni321:StrongPassword123@municipalcluster.tt4pe9t.mongodb.net/?retryWrites=true&w=majority&appName=MunicipalCluster"
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()  # Forces a call to the server
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {e}")