from crewai.tools import BaseTool
from prometheus_api_client import PrometheusConnect
from kubernetes import client, config
import requests
import os
import datetime
import logging
from typing import Optional, Type
from pydantic import BaseModel, Field

# --- Tool Input Schemas ---

class QueryInput(BaseModel):
    query: str = Field(description="The PromQL query to execute")

class AlertInput(BaseModel):
    message: str = Field(description="The alert message to send")

class K8sInput(BaseModel):
    target: str = Field(description="The target deployment in format 'namespace/deployment_name'")

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
    description: str = "Sends an incident alert to the team via Webhook."
    args_schema: Type[BaseModel] = AlertInput

    def _run(self, message: str) -> str:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return "Error: SLACK_WEBHOOK_URL not set."
        
        payload = {"text": f"🚨 *SRE Incident Alert*\n{message}"}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
            return "Alert sent successfully."
        except Exception as e:
            return f"Failed to send alert: {e}"

class K8sOperationsTool(BaseTool):
    name: str = "RestartDeployment"
    description: str = "Restarts a Kubernetes deployment. Input must be 'namespace/deployment_name'."
    args_schema: Type[BaseModel] = K8sInput

    def _run(self, target: str) -> str:
        try:
            # Load K8s Config (Works inside Pod or Local)
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()

            if "/" not in target:
                return "Error: Input must be 'namespace/deployment_name'"
            
            namespace, name = target.split("/")
            
            # Patch the deployment
            v1_apps = client.AppsV1Api()
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            body = {
                'spec': {
                    'template': {
                        'metadata': {
                            'annotations': {
                                'kubectl.kubernetes.io/restartedAt': now
                            }
                        }
                    }
                }
            }
            
            v1_apps.patch_namespaced_deployment(name, namespace, body)
            return f"✅ Successfully triggered rollout restart for {name} in {namespace}."
            
        except Exception as e:
            return f"K8s Error: {e}"
