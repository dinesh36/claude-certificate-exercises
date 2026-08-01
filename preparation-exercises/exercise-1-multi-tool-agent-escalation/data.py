"""Mock deployment data store for the task."""

import itertools

SERVICES = {"payments-service", "checkout-api", "user-auth"}

DEPLOYMENTS = {
    "DEPLOY-2001": {"service": "payments-service", "environment": "production", "version": "3.4.0", "status": "live", "risk_score": 3},
    "DEPLOY-2002": {"service": "payments-service", "environment": "staging", "version": "3.5.0", "status": "live", "risk_score": 5},
    "DEPLOY-2003": {"service": "checkout-api", "environment": "staging", "version": "2.1.0", "status": "live", "risk_score": 4},
    "DEPLOY-2004": {"service": "checkout-api", "environment": "production", "version": "2.0.0", "status": "live", "risk_score": 2},
    "DEPLOY-2005": {"service": "user-auth", "environment": "production", "version": "1.9.2", "status": "live", "risk_score": 6},
}

# Tracks which services' deployment lists have already been retried, so
# list_deployments can simulate one transient failure per service and then
# succeed — this lets the agent's retry behavior on isRetryable errors be observed.
_list_attempts: dict[str, int] = {}

_deploy_id_counter = itertools.count(2100)


def _next_deployment_id() -> str:
    return f"DEPLOY-{next(_deploy_id_counter)}"
