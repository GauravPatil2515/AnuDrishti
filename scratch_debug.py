import sys
sys.path.insert(0, 'backend/models')
sys.path.insert(0, 'backend/utils')

import torch
import numpy as np
from attention_ginet import AttentionGINet
from reasoner import MockLLMProvider
from substructure_mapper import SubstructureMapper
from faithfulness_validator import FaithfulnessValidator
from constrained_explainer import ConstrainedExplainer
from counterfactual_generator import CounterfactualGenerator
import pandas as pd

# Load model
model = AttentionGINet(num_tasks=12)
checkpoint = torch.load('results/trained_models/attention_gin_model.pth', map_location='cpu')
if 'model_state_dict' in checkpoint:
    model.load_state_dict(checkpoint['model_state_dict'])
else:
    model.load_state_dict(checkpoint)
model.eval()

# Load data
df = pd.read_csv('data_packages/tox21_model_full_package/data/tox21/tox21.csv')
# simple split (last 10%)
n = len(df)
test_start = int(n * 0.9)
df_test = df.iloc[test_start:].reset_index(drop=True)

smiles = df_test.iloc[0]['smiles']
print("SMILES:", smiles)

# Convert SMILES to graph and predict
from experiments.run_faithful_eval import smiles_to_data
data = smiles_to_data(smiles, 'cpu')

with torch.no_grad():
    features, predictions, attention_info = model(data, return_attention=True)

probs = torch.sigmoid(predictions).cpu().numpy()[0]
avg_toxicity = float(np.mean(probs))
attention_weights = attention_info['attention_weights'].cpu().numpy()

# Initialize components
substructure_mapper = SubstructureMapper()
counterfactual_generator = CounterfactualGenerator()
validator = FaithfulnessValidator(model=model, counterfactual_generator=counterfactual_generator)
llm = MockLLMProvider()

# Let's inspect the prompt constructed by ConstrainedExplainer
# We can subclass MockLLMProvider to capture the prompt
captured_prompts = []
class CapturingMockLLM(MockLLMProvider):
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        captured_prompts.append(prompt)
        return super().generate(prompt, max_tokens, temperature)

explainer = ConstrainedExplainer(
    model=model,
    llm_provider=CapturingMockLLM(),
    substructure_mapper=substructure_mapper,
    faithfulness_validator=validator,
    attention_threshold=0.1
)

explanation = explainer.explain(
    smiles=smiles,
    prediction=avg_toxicity,
    attention_weights=attention_weights,
    validate=True
)

print("\n--- CAPTURED PROMPT ---")
if captured_prompts:
    print(captured_prompts[0])
else:
    print("No prompts captured!")

print("\n--- LLM RESPONSE ---")
if captured_prompts:
    resp = MockLLMProvider().generate(captured_prompts[0])
    print(resp)

print("\n--- EXPLANATION RESULT ---")
print("faithfulness_score:", explanation.faithfulness_score)
print("validation_passed:", explanation.validation_passed)
print("rejection_reason:", explanation.rejection_reason)
print("identified_toxicophores:", explanation.identified_toxicophores)
print("details:", explanation.to_dict())
