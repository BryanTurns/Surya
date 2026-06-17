###### START: dependencies ######
# Debian Python image
FROM python:3.11-bookworm AS dependencies

WORKDIR /Surya

# Install uv (python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency tracking files over for use by uv
COPY pyproject.toml uv.lock ./

# Install dependencies from uv.lock file seperately from the project itself
# This allows the project source to change
RUN --mount=type=cache,target=/Surya/.uvcache uv sync --frozen --cache-dir /Surya/.uvcache --link-mode=copy --no-install-project

# Create root directories that will be bind mounted to so the child images are flexible
RUN mkdir /output && mkdir /config

# These are all necessary for the uv sync later on 
COPY LICENSE ./
COPY README.md ./
COPY surya/ ./surya/
###### END: dependencies ######

###### START: easy_inference ######
FROM dependencies AS easy_inference

# Install the project
RUN uv sync --frozen

# Copy the source relevant to the easy_inference use case
COPY easy_inference/ ./easy_inference
# Copy the custom config for easy_inference to the config folder
COPY easy_inference/easy_inference_docker_config.yaml /config/easy_inference_docker.yaml

# Entrypoint is the base command that is always ran
ENTRYPOINT [ "uv", "run", "python", "/Surya/easy_inference/run_easy_inference.py", "--skip-gt", "--no-prompt" ]
# CMD is the default flags that can be overwritten by specificying your own 
# Ex: `docker run easy_inference:latest --config-path /config/my-config.yaml --start-datetime '2026-06-17 14:00:00' --end-datetime '2026-06-17 14:00:00'`
CMD [  "--config-path", "/config/easy_inference_docker_config.yaml" ]
###### END: easy_inference ######

###### START: solar_flare_forcasting ######
FROM dependencies AS solar_flare_forcasting

WORKDIR /Surya

# Install the project
RUN uv sync --frozen

# Copy the source relevant to the solar flare forecasting use case
COPY downstream_examples/solar_flare_forcasting/ downstream_examples/solar_flare_forcasting/

# Entrypoint is the base command
ENTRYPOINT [ "uv", "run", "python", "/Surya/downstream_examples/solar_flare_forcasting/infer.py",\
             "--num_samples", "3",\
             "--checkpoint_path", "/Surya/downstream_examples/solar_flare_forcasting/assets/solar_flare_weights.pth"\
             "--output_dir /output" ]
# CMD is the default flags that can be overwritten
# Ex: `docker run solar_flare_forecasting:latest --config_path /config/my_config.yaml --device cuda`
CMD [  "--config_path", "/Surya/downstream_examples/solar_flare_forcasting/config.yaml", "--device", "cpu" ]
###### END: solar_flare_forecasting ######
