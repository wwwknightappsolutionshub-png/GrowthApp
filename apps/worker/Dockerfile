# The worker shares the API codebase — it has no separate Dockerfile.
# In Docker Compose the `worker` service is built from `apps/api/Dockerfile`
# with the entrypoint overridden to run ARQ.
#
# This stub exists only so that `docker build apps/worker` produces a clear
# error rather than a confusing one.
FROM busybox:latest
RUN echo "Build the worker from apps/api/Dockerfile (CMD: arq app.workers.worker_settings.WorkerSettings). See infra/docker-compose.yml." && exit 1
