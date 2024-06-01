from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json
from pyspark.sql.types import StructType, StructField, StringType
import pyspark.sql.functions as F


modelPath="/opt/tap/models/sentitap"
topic="main"
kafkaServer="kafka:9092"

spark = SparkSession.builder \
                    .appName("AudioMoodML") \
                    .getOrCreate()

# To reduce verbose output
spark.sparkContext.setLogLevel("ERROR") 

kafka_schema = StructType([
    StructField('@timestamp', StringType(), True),
    StructField('@version', StringType(), True), 
    StructField('host', StringType(), True),
    StructField('message', StringType(), True)
])

# Define Training Set Structure
""" tweet_schema = StructType([
    StructField(name= 'id', dataType=StringType(), nullable= True),
    StructField(name= 'created_at', dataType=StringType(), nullable= True),
    StructField(name= 'content', dataType=StringType(), nullable= True)
]) """


streaming_df = spark.readStream \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", kafkaServer) \
                    .option("subscribe", topic) \
                    .load()

                    #.option("startingOffsets", "earliest") \

json_df = streaming_df.selectExpr("cast(value as string)")
json_expanded_df = json_df.withColumn("value", from_json(json_df["value"], kafka_schema)).select("value.message")



query = json_expanded_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .option("numRows", "1000") \
    .start()


query.awaitTermination()
