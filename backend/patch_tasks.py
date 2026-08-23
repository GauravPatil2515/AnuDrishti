import sys

with open('tasks.py', 'r') as f:
    lines = f.readlines()

# Find the line index of the start of the optimize_whatif_task function
start_idx = None
for i, line in enumerate(lines):
    if line.strip() == '@celery_app.task(bind=True, max_retries=3)':
        # Check if the next line is the function definition
        if i+1 < len(lines) and 'def optimize_whatif_task' in lines[i+1]:
            start_idx = i
            break

if start_idx is None:
    print("Could not find optimize_whatif_task function")
    sys.exit(1)

# Find the end of the function (next function or end of file)
end_idx = None
for i in range(start_idx+1, len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith('@celery_app.task') or stripped.startswith('def '):
        end_idx = i
        break
if end_idx is None:
    end_idx = len(lines)

# Extract the function lines
func_lines = lines[start_idx:end_idx]

# We are going to look for two patterns and insert lines.
# Pattern 1: the line that assigns counterfactuals
# Pattern 2: the line inside the loop that sets cf_tox (we'll insert after the if block)

new_func_lines = []
i = 0
while i < len(func_lines):
    line = func_lines[i]
    new_func_lines.append(line)

    # Check for pattern 1: counterfactuals assignment
    if 'counterfactuals = cf_gen.generate_optimization_candidates(smiles, n_variants=n_variants)' in line:
        # Insert the baseline computation after this line
        new_func_lines.append('        # Compute baseline toxicity\n')
        new_func_lines.append('        baseline_result = predictor.predict(smiles)\n')
        new_func_lines.append('        baseline_tox = 0.0\n')
        new_func_lines.append('        if \\'summary\\' in baseline_result:\n')
        new_func_lines.append('            baseline_tox = float(baseline_result.get(\\'summary\\', {}).get(\\'average_toxicity_probability\\', 0.0) or 0.0)\n')
        i += 1
        continue

    # Check for pattern 2: we are inside the loop and we want to insert after the if block that sets cf_tox
    # We look for the line: '                    cf_tox = float(cf_result.get(\\'summary\\', {}).get(\\'average_toxicity_probability\\', 0.0) or 0.0)'
    if 'cf_tox = float(cf_result.get(\\'summary\\', {}).get(\\'average_toxicity_probability\\', 0.0) or 0.0)' in line:
        # We have to insert after this line, but note that we are in the inner block.
        # We'll add the skip condition lines with the same indentation as this line.
        indent = len(line) - len(line.lstrip())
        new_func_lines.append(' ' * indent + '# Skip if candidate increases toxicity significantly\n')
        new_func_lines.append(' ' * indent + 'toxicity_reduction = baseline_tox - cf_tox\n')
        new_func_lines.append(' ' * indent + 'if toxicity_reduction < -0.05:\n')
        new_func_lines.append(' ' * indent + '    continue\n')
        i += 1
        continue

    i += 1

# Now, replace the function in the original lines
lines[start_idx:end_idx] = new_func_lines

# Write back
with open('tasks.py', 'w') as f:
    f.writelines(lines)
