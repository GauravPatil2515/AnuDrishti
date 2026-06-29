import re

with open("backend/models/reasoner.py", "r") as f:
    content = f.read()

new_generate = """    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        '''Return mock response for testing.'''
        if "JSON" in prompt:
            return '''{
              "executive_summary": "The prediction is driven by the presence of a nitro group, strongly associated with toxicity.",
              "primary_toxicophore": {
                "name": "Nitro",
                "atoms": [6, 7, 8],
                "attention_score": 0.85,
                "mechanism": "Enzymatic reduction forms reactive nitroso intermediates."
              },
              "secondary_features": [],
              "overall_mechanism": "Nitroaromatic compounds undergo enzymatic reduction to form reactive nitroso intermediates, causing oxidative stress.",
              "confidence": 0.95
            }'''
        if "executive summary" in prompt.lower():
            return ("This molecule shows moderate toxicity risk due to the presence of "
                   "reactive functional groups identified by the neural network. ")
        return "[Mock LLM response for testing]"
"""

new_content = re.sub(
    r'    def generate\(self, prompt: str, max_tokens: int = 1000, temperature: float = 0\.3\) -> str:.*?(?=class NeuroSymbolicReasoner:)', 
    new_generate + "\n\n", 
    content, 
    flags=re.DOTALL
)

with open("backend/models/reasoner.py", "w") as f:
    f.write(new_content)
