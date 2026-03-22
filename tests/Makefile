.PHONY: test-core test-federation test-nats test-all clean logs

COMPOSE := docker compose

test-core:
	$(COMPOSE) -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner

test-federation:
	$(COMPOSE) -f docker-compose.test.yml -f docker-compose.federation.yml up --build --abort-on-container-exit --exit-code-from test-runner

test-nats:
	$(COMPOSE) -f docker-compose.test.yml -f docker-compose.nats.yml up --build --abort-on-container-exit --exit-code-from test-runner

test-all: test-core test-federation test-nats

clean:
	$(COMPOSE) -f docker-compose.test.yml -f docker-compose.federation.yml -f docker-compose.nats.yml down -v --remove-orphans

logs:
	$(COMPOSE) -f docker-compose.test.yml logs
