from crewai.tools import BaseTool
from prometheus_api_client import PrometheusConnect
from kubernetes import client, config
import requests
import os
import datetime
from typing import Type
from pydantic import BaseModel, Field

# --- Input Schemas ---
class QueryInput(BaseModel):
    query: str = Field(description="The PromQL query to execute")

class AlertInput(BaseModel):
    message: str = Field(description="The alert message to send")

class K8sInput(BaseModel):
    target: str = Field(description="Target in 'namespace/name' format (e.g. 'default/rabbitmq')")
    replicas: int = Field(default=3, description="The desired number of replicas")

# --- Tool Definitions ---

class PrometheusQueryTool(BaseTool):
    name: str = "PrometheusQuery"
    description: str = "Executes a PromQL query and returns the result."
    args_schema: Type[BaseModel] = QueryInput

    def _run(self, query: str) -> str:
        url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        try:
            prom = PrometheusConnect(url=url, disable_ssl=True)
            result = prom.custom_query(query)
            return str(result)
        except Exception as e:
            return f"Prometheus Error: {e}"

class AlertTool(BaseTool):
    name: str = "SendAlert"
    description: str = "Sends an incident alert via Webhook."
    args_schema: Type[BaseModel] = AlertInput

    def _run(self, message: str) -> str:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return "Error: SLACK_WEBHOOK_URL not set."
        try:
            requests.post(webhook_url, json={"text": f"🚨 *SRE Action*\n{message}"}, timeout=5)
            return "Alert sent."
        except Exception as e:
            return f"Failed to send alert: {e}"

class ScaleStatefulSetTool(BaseTool):
    name: str = "ScaleStatefulSet"
    description: str = "Scales a Kubernetes StatefulSet to a specific number of replicas. Input: 'namespace/name' and count."
    args_schema: Type[BaseModel] = K8sInput

    def _run(self, target: str, replicas: int) -> str:
        try:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()

            if "/" not in target:
                return "Error: Target must be 'namespace/name'"
            
            namespace, name = target.split("/")
            
            v1_apps = client.AppsV1Api()
            
            # Execute Scaling
            body = {'spec': {'replicas': replicas}}
            v1_apps.patch_namespaced_stateful_set(name, namespace, body)
            
            return f"✅ Successfully scaled StatefulSet '{name}' in '{namespace}' to {replicas} replicas."
            
        except Exception as e:
            return f"Scaling Error: {e}"
