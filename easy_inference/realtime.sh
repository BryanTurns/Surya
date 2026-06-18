#!/bin/bash



S3_BUCKET_NAME="surya-ird-output"

end_date=$(date -u -d "+30 minutes -4 years" '+%Y-%m-%d %H:00:00')

# This is +8 hours because the script looks back 2 hours so it needs +2 hours for the input data and +6 hours for the output
# Another way to think about this is there are 8 ground truth images 6 of which we compare against our output
start_date=$(date -d "$end_date +8 hours" '+%Y-%m-%d %H:00:00')

s3_uri="s3://$S3_BUCKET_NAME/$start_date/"


source .venv/bin/activate
# If there are arguments passed to the script, use them 
if [ -z "$*" ]; then
    uv run python /Surya/easy_inference/run_easy_inference.py --output-s3-uri "$s3_uri" --start-date "$start_date" --end-date "$end_date" --config-path "/config/easy_inference_docker_config.yaml" --no-prompt
else
    uv run python /Surya/easy_inference/run_easy_inference.py --output-s3-uri "$s3_uri" --start-date "$start_date" --end-date "$end_date" --no-prompt $*
fi