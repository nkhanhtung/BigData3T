from pymongo import MongoClient

try:
    client = MongoClient("mongodb+srv://maiminhtung2005_db_user:ggzaIHwy1EOsEFnC@cluster0.lu0egys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['BigData']
    stock_logs = db['stocks_logs']
except Exception as e:
    print("Error connection", e)
