class BaseAgent:
    """
    Base class for all agents in the system.
    Provides basic identity and logging structure.
    """
    def __init__(self, name, role):
        self.name = name
        self.role = role
        print(f"[{self.name}] Initialized as {self.role}")

    def log(self, message):
        """Standardized logging for the agent."""
        print(f"[{self.name}] {message}")

    def run(self, *args, **kwargs):
        """
        Main execution method for the agent.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Agents must implement the run method.")
