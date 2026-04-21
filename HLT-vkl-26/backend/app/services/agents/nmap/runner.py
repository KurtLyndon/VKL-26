from app.models import TaskExecution
from app.services.agents.runner_base import AgentRunner


class NmapRunner(AgentRunner):
    agent_type = "nmap"

    def run(self, task_execution: TaskExecution, target_value: str) -> str:
        return f"""<nmaprun>
  <host>
    <status state="up" />
    <address addr="{target_value}" addrtype="ipv4" />
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" />
        <service name="ssh" product="OpenSSH" version="9.0" />
      </port>
      <port protocol="tcp" portid="80">
        <state state="open" />
        <service name="http" product="nginx" version="1.24" />
      </port>
    </ports>
  </host>
</nmaprun>"""
