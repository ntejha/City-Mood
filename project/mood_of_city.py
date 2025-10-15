import os
import requests
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StructType, StructField, StringType
from textblob import TextBlob
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv(".env")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Variable for city to analyze
city = "New York"

# Build NewsAPI request URL
url = f"https://newsapi.org/v2/everything?q={city}&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"

# Fetch news
response = requests.get(url)
news_json = response.json()

# Extract headlines
headlines = [article['title'] for article in news_json.get('articles', [])]

# Initialize Spark session with MongoDB support
spark = SparkSession.builder \
    .appName("MoodOfTheCity") \
    .config("spark.mongodb.write.connection.uri", "mongodb://hadoop-master:27017/sentiment.city_emotions") \
    .getOrCreate()

# Schema for DataFrame
schema = StructType([
    StructField("headline", StringType(), True),
    StructField("emotion", StringType(), True)
])

# Prepare data rows with sentiment analysis
data = []
for headline in headlines:
    polarity = TextBlob(headline).sentiment.polarity
    if polarity > 0.1:
        emotion = "Optimism"
    elif polarity < -0.1:
        emotion = "Fear/Anger"
    else:
        emotion = "Neutral"
    data.append((headline, emotion))

# Create DataFrame
df = spark.createDataFrame(data, schema)

# Show the result on console
df.show(truncate=False)

# Write results to MongoDB - CORRECTED
df.write \
    .format("mongodb") \
    .mode("append") \
    .option("database", "sentiment") \
    .option("collection", "city_emotions") \
    .save()

spark.stop()