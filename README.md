# 🤖 Autonomous SRE Crew (Event-Driven)

This project deploys an AI-powered Site Reliability Engineering (SRE) team into your Kubernetes cluster. It continuously monitors services, detects anomalies, and autonomously remediates issues (like restarting "stuck" deployments) or alerts the team.

## 🏗 Architecture

The system uses an **Orchestrator Pattern** to minimize costs and maximize control:

1.  **Monitor Agent (Run Loop):**
    * Queries **Prometheus** every 60s.
    * Checks "Golden Signals" (Latency, Error Rate, Traffic).
    * Acts as a "Watchdog"—if it sees "ANOMALY" or "ERROR", it triggers the Investigator.

2.  **Investigator Agent (On-Demand):**
    * Triggered **only** when the Monitor detects an issue.
    * **Triage:** Analyzes metrics to distinguish between a **Bug** (High Errors) vs. **Zombie Process** (0 CPU/Traffic).
    * **Action:**
        * **Restart:** Uses `K8sOperationsTool` to rollout restart "stuck" deployments.
        * **Alert:** Uses `AlertTool` (Webhook) to notify engineers of code bugs.

3.  **SLO Agent (Scheduled):**
    * Runs every 5 minutes.
    * Audits compliance against targets defined in `slos.yaml`.

---

## 🛠 Prerequisites

* **Kubernetes Cluster** (Local via Docker Desktop/Minikube or Cloud)
* **Prometheus** running in the cluster (or accessible URL).
* **OpenAI API Key** (GPT-4 recommended for Investigator).
* **Slack Webhook URL** (Optional, for alerts).

---

## 🚀 Quick Start

### 1. Configuration
All logic is controlled via YAML files in `charts/sre-crew/files/`. You can edit these on the fly:
* `slos.yaml`: Define your availability targets (e.g., 99.9%).
* `llm_config.json`: Change model (e.g., `gpt-4o-mini`).
* `tasks.yaml`: Update the "Runbooks" the agents follow.

### 2. Build the Image
```bash
cd sre-crew
docker build -t sre-crew:latest . 
```

### 3. Deploy to Kubernetes
```bash
# Export your API Key first
export OPENAI_API_KEY=""

# Install via Helm
helm upgrade --install sre-crew ./sre-crew/charts/sre-crew \
  --create-namespace \
  --namespace sre-crew \
  --set image.pullPolicy=Never \
  --set image.tag=latest \
  --set config.prometheusUrl="http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
```

 ### 4. Testing & Verification

 #### 1. Check Status
```bash
 kubectl get pods -l app=sre-crew

 ```

 #### 2. Watch the Brain at Work

 ```bash

 kubectl logs -f deployment/sre-crew
 ```

 #### Example Log Output:
```bash
 INFO: 🚀 SRE Autonomous Crew Started
INFO: Running Monitor Check...
INFO: Monitor Output: HEALTHY
...
WARN: 🔥 Incident Detected! Triggering Investigator...
INFO: Investigator Output: Analyzed 5xx spike. Determined it is a CODE BUG. Sent Alert to Slack.
```

### 📂 Project Structure

```bash
sre-crew/
├── Dockerfile              # Python environment with 'src' included
├── charts/
│   └── sre-crew/           # Helm Chart
│       ├── templates/      # K8s manifests (Deployment, RBAC, ConfigMap)
│       └── files/          # Configs injected at runtime (agents.yaml, tasks.yaml)
├── src/
│   ├── main.py             # Orchestrator Loop (Monitor -> Decide -> Investigate)
│   ├── crew.py             # CrewAI Agent Definitions
│   └── tools.py            # Capabilities (Prometheus, K8s Restart, Webhook)
└── requirements.txt        # Dependencies (crewai, kubernetes, pydantic)

```