import sys

# Read the file
with open('tasks.py', 'r') as f:
    lines = f.readlines()

# We are going to modify the optimize_whatif_task function.
# Find the line with: counterfactuals = cf_gen.generate_optimization_candidates(smiles, n_variants=n_variants)
for i, line in enumerate(lines):
    if 'counterfactuals = cf_gen.generate_optimization_candidates(smiles, n_variants=n_variants)' in line:
        # Insert after this line the baseline computation.
        indent = len(line) - len(line.lstrip())
        # We'll insert 6 lines of baseline computation.
        baseline_lines = [
            ' ' * indent + '# Compute baseline toxicity\n',
            ' ' * indent + 'baseline_result = predictor.predict(smiles)\n',
            ' ' * indent + 'baseline_tox = 0.0\n',
            ' ' * indent + 'if \\'summary\\' in baseline_result:\n',
            ' ' * indent + '    baseline_tox = float(baseline_result.get(\\'summary\\', {}).get(\\'average_toxicity_probability\\', 0.0) or 0.0)\n',
            '\n'  # an empty line for readability
        ]
        # Insert the baseline_lines after the current line.
        lines[i+1:i+1] = baseline_lines
        # We have to adjust the index because we inserted lines.
        # We'll break and then continue to the next part (the loop) but note that the line numbers have shifted.
        break

# Now, we need to find the loop where we process each counterfactual.
# We are looking for the line that sets cf_tox.
# In the backup, it was:
#                    cf_tox = float(cf_result.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)
# We want to insert after that line the condition to skip if toxicity increases.
for i, line in enumerate(lines):
    if "cf_tox = float(cf_result.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)" in line:
        # We have found the line. We want to insert after it.
        indent = len(line) - len(line.lstrip())
        # The lines to insert:
        skip_lines = [
            ' ' * indent + '# Skip if candidate increases toxicity significantly\n',
            ' ' * indent + 'toxicity_reduction = baseline_tox - cf_tox\n',
            ' ' * indent + 'if toxicity_reduction < -0.01:\n',
            ' ' * indent + '    continue\n',
        ]
        # Insert after the current line.
        lines[i+1:i+1] = skip_lines
        break

# Write back
with open('tasks.py', 'w') as f:
    f.writelines(lines)
