FROM pytorch/pytorch:2.6.0-cuda12.6-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV LD_LIBRARY_PATH="\
/opt/conda/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:\
/opt/conda/lib/python3.11/site-packages/nvidia/cuda_runtime/lib64:\
/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib:\
/opt/conda/lib/python3.11/site-packages/cusparselt/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/cuda_cupti/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/cublas/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/cusparse/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/cufft/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/curand/lib/:\
/opt/conda/lib/python3.11/site-packages/nvidia/nccl/lib/:\
${LD_LIBRARY_PATH}"

RUN apt-get update -y && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*

WORKDIR /scribe-service

COPY ./requirements.txt /scribe-service/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /scribe-service/requirements.txt

COPY . /scribe-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]