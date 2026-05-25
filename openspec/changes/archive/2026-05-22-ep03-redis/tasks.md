## 1. Infrastructure

- [x] 1.1 Enable Redis 7 in `infra/docker/docker-compose.yml` (service, volume, healthcheck)
- [x] 1.2 Update `scripts/docker.sh` to wait for Redis PING after Postgres
- [x] 1.3 Add `REDIS_URL` to `config.py`, `.env.example`, `requirements.txt` (`redis[hiredis]`)

## 2. Redis client & health

- [x] 2.1 Add `app/core/redis.py` (async client, optional when URL unset)
- [x] 2.2 Extend `HealthData` and health handlers with `postgres` / `redis` status probes

## 3. Cache layer

- [x] 3.1 Add `app/cache/` with key helpers, `ConversationCache`, `StreamCache`
- [x] 3.2 Integrate Cache-Aside + invalidation in `ConversationService`

## 4. Tests & docs

- [x] 4.1 Harness: health dependency fields; conversations still pass with Redis
- [x] 4.2 Unit test for `StreamCache` append/get/delete
- [x] 4.3 Update `infra/docker/README.md`, `docs/database.md`, EP03 epic checkboxes
