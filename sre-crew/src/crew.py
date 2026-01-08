from crewai import Agent, Task, Crew
from src.tools import PrometheusQueryTool, AlertTool, K8sOperationsTool
from langchain_openai import ChatOpenAI
import yaml
import json
import os

class SREOrchestrator:
    def __init__(self):
        self.agents_config = self._load_yaml('config/agents.yaml')
        self.tasks_config = self._load_yaml('config/tasks.yaml')
        self.slos_config = self._load_yaml('config/slos.yaml')
        self.llm_settings = self._load_json('config/llm_config.json')
        
        # STRICT CONFIGURATION:
        # We access keys directly. If a key is missing in the JSON, 
        # the pod will crash with a KeyError, alerting you to fix the config.
        self.llm = ChatOpenAI(
            model=self.llm_settings['model'],
            temperature=self.llm_settings['temperature'],
            max_tokens=self.llm_settings['max_tokens'],
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def _load_yaml(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def run_monitor(self):
        agent = Agent(
            config=self.agents_config['monitor_agent'],
            tools=[PrometheusQueryTool()],
            llm=self.llm,
            verbose=False
        )
        task = Task(config=self.tasks_config['monitor_task'], agent=agent)
        return Crew(agents=[agent], tasks=[task]).kickoff()

    def run_investigation(self, context):
        agent = Agent(
            config=self.agents_config['investigator_agent'],
            tools=[PrometheusQueryTool(), AlertTool(), K8sOperationsTool()],
            llm=self.llm,
            verbose=True
        )
        
        task_def = self.tasks_config['investigation_task']
        task_def['description'] = task_def['description'].format(anomaly_context=context)
        
        task = Task(
            description=task_def['description'],
            expected_output=task_def['expected_output'],
            agent=agent
        )
        
        return Crew(agents=[agent], tasks=[task]).kickoff()

    def run_slo_check(self):
        agent = Agent(
            config=self.agents_config['slo_agent'],
            tools=[PrometheusQueryTool()],
            llm=self.llm,
            verbose=True
        )
        slo_context = str(self.slos_config)
        task_desc = self.tasks_config['slo_task']['description'] + f"\n\nSLO CONFIG:\n{slo_context}"
        
        task = Task(
            description=task_desc,
            expected_output=self.tasks_config['slo_task']['expected_output'],
            agent=agent
        )
        return Crew(agents=[agent], tasks=[task]).kickoff()
