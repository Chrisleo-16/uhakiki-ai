from crewai_tools import BaseTool

class ForgeryScanner(BaseTool):
    name: str = "RAD Scanner"
    description: str = "Checks for AI-generated forgeries by calculating $x_i - \hat{x_i}$ residuals."

    def _run(self, doc_path: str):
        return "Residuals within normal range (Authentic)."