from pyspark.sql import SparkSession
from pyspark.sql.utils import AnalysisException
import subprocess
import pymongo
from pymongo.errors import ConnectionFailure

def check_hdfs():
    import pyarrow as pa
    try:
        # Trying to list the directory
        result = subprocess.run(["hdfs", "dfs", "-test", "-d", "/spark-logs"], capture_output=True)
        if result.returncode == 0:
            print("HDFS directory /spark-logs exists.")
        else:
            print("HDFS directory /spark-logs does not exist.")
    except Exception as e:
        print(f"Error checking HDFS: {e}")

def check_yarn_nodes():
    try:
        import requests
        response = requests.get('http://hadoop-master:8088/ws/v1/cluster/nodes')
        if response.status_code == 200:
            data = response.json()
            nodes = data['nodes']['node']
            print(f"YARN Nodes ({len(nodes)}):")
            for node in nodes:
                print(f" - {node['id']} ({node['state']})")
        else:
            print("Failed to fetch Yarn nodes.")
    except Exception as e:
        print(f"Error checking YARN: {e}")

def check_mongodb():
    try:
        client = pymongo.MongoClient("mongodb://hadoop-master:27017/", serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        db = client.test
        # Insert and retrieve a test document
        test_doc = {"test": "value"}
        result = db.test_collection.insert_one(test_doc)
        if result.acknowledged:
            print("MongoDB connection and write successful.")
            # Clean up
            db.test_collection.delete_one({"_id": result.inserted_id})
        else:
            print("MongoDB insert not acknowledged.")
    except ConnectionFailure:
        print("Failed to connect to MongoDB.")
    except Exception as e:
        print(f"Error checking MongoDB: {e}")

if __name__ == "__main__":
    print("Checking HDFS...")
    check_hdfs()
    print("Checking YARN Node registration...")
    check_yarn_nodes()
    print("Checking MongoDB connection...")
    check_mongodb()
