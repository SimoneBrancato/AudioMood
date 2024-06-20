from pyspark.sql import SparkSession
from sparknlp.base import DocumentAssembler, PipelineModel
from sparknlp.annotator import T5Transformer
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json
from pyspark.sql.functions import col, explode

kafkaServer = "kafka:9092"
topic = "summary"
elastic_index = "am_summary"

# Define kafka messages structure
kafka_schema = tp.StructType([
    tp.StructField('@timestamp', tp.StringType(), True),
    tp.StructField('message', tp.StringType(), True)
])


# Define Spark connection to ElasticSearch
print("Defining SparkConf")
sparkConf = SparkConf().set("es.nodes", "elasticsearch") \
                        .set("es.port", "9200") \
                        .set("spark.driver.memory","64G") \
                        .set("spark.driver.maxResultSize", "0") \
                        .set("spark.kryoserializer.buffer.max", "2000M") \
                        .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                        .set("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.3.3")
                        
# Build Spark Session in SparkNLP mode
print("Starting Spark Session")
spark = SparkSession.builder \
    .appName("Spark NLP") \
    .master("local[16]") \
    .config(conf=sparkConf) \
    .getOrCreate()

# To reduce verbose output
spark.sparkContext.setLogLevel("ERROR") 

# Read the stream from Kafka
print("Reading stream from kafka...")
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()

# Parse and simplify dataframe structure
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", kafka_schema).alias("data")) \
    .select(
        col("data.@timestamp").alias("timestamp"),
        col("data.message").alias("text")
    )  

# Transforms raw texts into `document` annotation
document_assembler = (
    DocumentAssembler().setInputCol("text").setOutputCol("documents")
)

# Set up T5 Text-to-Text pretrained model for summarization
t5 = (
    T5Transformer.load("/code/models/t5_base_en_4.0.0_3.0_1654004828680")
    .setTask("summarize:")
    .setInputCols(["documents"])
    .setMaxOutputLength(600)
    .setOutputCol("t5")
)

# Define the Spark pipeline
pipeline = PipelineModel(stages = [document_assembler, t5])

# Process each batch of data into summarization pipeline 
df_summary = pipeline.transform(df)

# Select relevant data
df_summary.printSchema()

df_summary = df_summary.select("t5.result")

df_summary.writeStream \
    .format("console") \
    .option("truncate", "false") \
    .start() \
    .awaitTermination()





# Send data to ElasticSearch
""" df_summary.writeStream \
            .format("es") \
            .option("checkpointLocation", "/tmp/") \
            .option("failOnDataLoss", "false") \
            .start(elastic_index) \
            .awaitTermination()   """                       


