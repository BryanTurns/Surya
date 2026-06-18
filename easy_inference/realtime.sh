#!/bin/bash
usage="./realtime.sh [ s3 bucket ] [ dynamo db table ] [ aws region ]"

if [ $# -ne 3 ]; then
    echo "$usage"
    echo "Invalid number of arguments. Exiting..."
    exit 1
fi

end_date=$(date -u -d "+30 minutes -4 years" '+%Y-%m-%d %H:00:00')

# This is +8 hours because the script looks back 2 hours so it needs +2 hours for the input data and +6 hours for the output
# Another way to think about this is there are 8 ground truth images 6 of which we compare against our output
start_date=$(date -d "$end_date +8 hours" '+%Y-%m-%d %H:00:00')

s3_uri="s3://results/$1/$start_date/"
dynamodb_table=$2
aws_region=$3

source .venv/bin/activate
if [ -z "$*" ]; then
    uv run python /Surya/easy_inference/run_easy_inference.py --output-s3-uri "$s3_uri" --start-date "$start_date" --end-date "$end_date" --config-path "/config/easy_inference_docker_config.yaml" --no-prompt
else
    uv run python /Surya/easy_inference/run_easy_inference.py --start-date "$start_date" --end-date "$end_date" --no-prompt --output-s3-uri "$s3_uri" --dynamodb-table "$dynamodb_table" --aws-region "$aws_region"
fi