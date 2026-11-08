# Factory to Field: one-command demo. Build context is the repo root.
#   docker compose -f factory_to_field/docker-compose.yml up --build
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY factory_to_field/requirements.txt factory_to_field/requirements.txt
RUN pip install --no-cache-dir -r factory_to_field/requirements.txt
COPY factory_to_field factory_to_field
# Build the simulated world and knowledge graph at image build time so start-up is instant.
RUN python -m factory_to_field.world.build && python -m factory_to_field.kg.build --skip-shacl
EXPOSE 8800
CMD ["python", "-m", "factory_to_field.ui.live_app", "--host", "0.0.0.0", "--port", "8800"]
