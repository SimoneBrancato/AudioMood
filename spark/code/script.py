from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json
from pyspark.sql.types import StructType, StructField, StringType


spark = SparkSession.builder.appName("AudioMood").getOrCreate()

spark.sparkContext.setLogLevel("ERROR") 

streaming_df = spark.readStream\
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "main") \
    .option("startingOffsets", "earliest") \
    .load()

json_schema = StructType([
    StructField('@timestamp', StringType(), True),
    StructField('@version', StringType(), True), 
    StructField('host', StringType(), True),
    StructField('message', StringType(), True),
    StructField('headers', StructType([
        StructField('content_type', StringType(), True),
        StructField('http_accept', StringType(), True),
        StructField('accept_encoding', StringType(), True),
        StructField('http_version', StringType(), True),
        StructField('request_method', StringType(), True),
        StructField('connection', StringType(), True),
        StructField('request_path', StringType(), True),
        StructField('http_host', StringType(), True),
        StructField('content_length', StringType(), True),
        StructField('http_user_agent', StringType(), True)
    ]), True)
])

# Apply Schema to JSON value column and expand the value
json_df = streaming_df.selectExpr("cast(value as string) as value")
json_expanded_df = json_df.withColumn("value", from_json(json_df["value"], json_schema)).select("value.*")

# Print the parsed JSON data to the console
query = json_expanded_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# Wait for the termination of the query
query.awaitTermination()
