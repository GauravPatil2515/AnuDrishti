#!/usr/bin/env bash
# ======================================================================
# DeNovo Research Submission: Reproducibility Pipeline
# ======================================================================
# This script reproduces all paper results, tables, and figures from
# the final empirical models and evaluations.
#
# Author: DeNovo-XAI Research Team
# ======================================================================
set -e

echo "======================================================================"
echo "DeNovo Research Submission: Reproducibility Pipeline"
echo "======================================================================"
echo "This script reproduces all paper results, tables, and figures from"
echo "the final empirical models and evaluations."
echo ""

# Detect python command (use .venv if available)
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "Using virtual environment python: $PYTHON_CMD"
else
    PYTHON_CMD="python3"
    echo "Using system python: $PYTHON_CMD"
fi

echo "🧪 [1/6] Running Model Validation..."
$PYTHON_CMD validate_models.py

echo "📊 [2/6] Running Faithfulness Evaluation Baseline Comparisons..."
$PYTHON_CMD experiments/compare_baselines.py \
    --constrained results/eval_tox21_fixed/statistics.json \
    --unconstrained results/baseline_unconstrained_tox21/statistics.json \
    --out results/faithfulness_comparison

echo "📈 [3/6] Plotting Sensitivity/Pareto trade-off curves..."
$PYTHON_CMD experiments/plot_sensitivity.py

echo "🎨 [4/6] Generating main paper figures (distributions, rates)..."
$PYTHON_CMD experiments/generate_paper_figures.py \
    --results results/eval_tox21_fixed/results.csv \
    --output results/paper_figures

echo "📝 [5/6] Selecting qualitative case studies..."
$PYTHON_CMD experiments/select_case_studies.py

echo "📄 [6/6] Compiling LaTeX manuscript draft..."
if command -v pdflatex &> /dev/null; then
    echo "pdflatex found. Compiling Overleaf paper template..."
    cd overleaf
    # Compile twice to resolve references and labels
    pdflatex -interaction=nonstopmode main.tex &> /dev/null || true
    pdflatex -interaction=nonstopmode main.tex &> /dev/null || echo "⚠️ Warning: pdflatex compilation finished with some warnings (normal)."
    cd ..
    if [ -f overleaf/main.pdf ]; then
        echo "✅ Compiled PDF saved to overleaf/main.pdf"
    else
        echo "❌ Compilation failed to produce PDF."
    fi
else
    echo "ℹ️ pdflatex not found. Skipping PDF compilation."
    echo "   You can import the 'overleaf' folder or 'paper_drafts/overleaf_FINAL_SUBMISSION.zip' directly to Overleaf to compile."
fi

echo ""
echo "======================================================================"
echo "🎉 REPRODUCTION COMPLETE!"
echo "- All figures are in results/paper_figures/ and overleaf/figures/."
echo "- All comparisons are in results/faithfulness_comparison/."
echo "- Case studies are detailed in results/paper_figures/selected_cases.md."
echo "======================================================================"
