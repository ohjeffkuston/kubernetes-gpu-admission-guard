FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir .
USER 65532:65532
ENTRYPOINT ["python", "-m", "kubernetes_gpu_admission_guard"]
CMD ["--input", "examples/cluster-snapshot.json"]
