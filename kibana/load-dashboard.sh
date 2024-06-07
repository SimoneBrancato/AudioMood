echo "Waiting for Kibana to be ready..."

until $(curl --output /dev/null --silent --head --fail http://kibana:5601); do
  sleep 5
done

sleep 20    # ONLY WORKS WITH SLEEPING TIME - MAKE IT BETTER

echo "Importing dashboard in Kibana..."

# Import the dashboard
curl -X POST "http://kibana:5601/api/saved_objects/_import?overwrite=true" -H "kbn-xsrf: true" --form file=@/export.ndjson


