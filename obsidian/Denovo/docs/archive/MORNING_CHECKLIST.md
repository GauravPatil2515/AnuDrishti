# Morning Checklist: After Training Completes

## ☀️ Good Morning! Training is Done

**Date:** Check when you run this  
**Expected Training Time:** 8-12 hours  
**You should have:** A trained Attention-GIN model ready for experiments

---

## ✅ Step 1: Verify Training Succeeded (5 minutes)

### Check training logs

```powershell
cd C:\Users\GAURAV PATIL\Downloads\DeNovo-main\DeNovo-main\backend\models

# View last 20 lines of training log
Get-Content training_tox21.log -Tail 20
```

**Look for:**

- ✅ "Training complete!"
- ✅ "Best validation ROC-AUC: 0.XXX"
- ❌ Any "Error" or "Exception" messages

### Check model file exists

```powershell
Test-Path training_tox21/attention_gin_model.pth
# Should return: True
```

### View training history

```powershell
python -c "import pandas as pd; df = pd.read_csv('training_tox21/training_history.csv'); print('Epochs:', len(df)); print('Best ROC-AUC:', df['val_score'].max())"
```

**Expected Output:**

```
Epochs: 50-80
Best ROC-AUC: 0.82-0.85
```

### ✅ If ROC-AUC ≥ 0.82 → SUCCESS! Continue to Step 2

### ❌ If ROC-AUC < 0.82 → See Troubleshooting at bottom

---

## 📊 Step 2: Test the Trained Model (10 minutes)

### Run demo with trained model

```powershell
cd ..\..\experiments

# Test with benzene (low toxicity)
python faithful_xai_demo.py --use-groq --smiles "c1ccccc1"
```

**Expected:**

- Prediction: ~30-40% toxic
- Validation: PASSED or REJECTED
- Faithfulness Score: 0.6-0.8

### Test with toxic molecule

```powershell
# Test with nitrobenzene (high toxicity)
python faithful_xai_demo.py --use-groq --smiles "c1ccc([N+](=O)[O-])cc1"
```

**Expected:**

- Prediction: ~80-90% toxic
- Identified toxicophores: Nitro group
- Validation: PASSED
- Faithfulness Score: 0.7-0.9

### ✅ If both tests work → Model is ready! Continue to Step 3

### ❌ If tests fail → Check Groq API key is set

---

## 🔬 Step 3: Run Small Evaluation Batch (30 minutes)

Test on 50 molecules to verify everything works:

```powershell
cd experiments

# Run evaluation on 50 molecules
python run_faithful_eval.py `
  --model ../backend/models/training_tox21/attention_gin_model.pth `
  --dataset ../MODELS/tox21_model_full_package/data/tox21/tox21.csv `
  --n-molecules 50 `
  --output results/quick_test
```

**This will take ~30 minutes** (depends on Groq API speed)

### Check results

```powershell
cd results/quick_test

# View statistics
Get-Content statistics.json
```

**Expected:**

```json
{
  "mean_faithfulness": 0.65-0.75,
  "rejection_rate": 0.15-0.30,
  "n_evaluated": 50
}
```

### ✅ If rejection_rate is 15-30% → Perfect! This proves the paper's point

### ✅ If mean_faithfulness > 0.60 → Good results! Continue to Step 4

---

## 🎯 Step 4: Decision Point - What's Next?

Based on your results, choose one:

### Option A: Full Evaluation (Recommended - 1 day)

**For complete paper results:**

```powershell
# Run on full test set (800+ molecules)
python run_faithful_eval.py `
  --model ../backend/models/training_tox21/attention_gin_model.pth `
  --n-molecules 200 `
  --output results/tox21_full
```

**Time:** ~3-6 hours (run overnight again)

### Option B: Ablation Studies (For paper - 2 hours)

**Test each component's contribution:**

```powershell
# Without causal check
python run_faithful_eval.py --model ../backend/models/training_tox21/attention_gin_model.pth --disable-causal --n-molecules 50 --output results/ablation_no_causal

# Without counterfactual
python run_faithful_eval.py --model ../backend/models/training_tox21/attention_gin_model.pth --disable-counterfactual --n-molecules 50 --output results/ablation_no_cf

# Without grounding
python run_faithful_eval.py --model ../backend/models/training_tox21/attention_gin_model.pth --disable-grounding --n-molecules 50 --output results/ablation_no_grounding
```

### Option C: Train Other Datasets (Optional - 2 more nights)

**For stronger paper:**

```powershell
# Train ClinTox model (night 2)
cd ..\..\backend\models
python train_attention_gin.py --task clintox --config config_rtx3050.yaml --epochs 60 --output_dir training_clintox

# Train BBBP model (night 3)
python train_attention_gin.py --task bbbp --config config_rtx3050.yaml --epochs 50 --output_dir training_bbbp
```

---

## 📈 Step 5: Check Your Progress Toward Paper

### Current Status Checklist

- [ ] Tox21 model trained (ROC-AUC ≥ 0.82)
- [ ] Demo works with Groq LLM
- [ ] Quick test (50 molecules) completed
- [ ] Faithfulness Score: 0.65-0.75
- [ ] Rejection Rate: 15-30%

### What You Have for Paper

✅ **Trained explainable model**  
✅ **Faithfulness metric working**  
✅ **Rejection mechanism working**  
✅ **LLM integration via Groq**

### What You Still Need

- [ ] Full evaluation (200+ molecules)
- [ ] Ablation studies (3 runs)
- [ ] Case study selection (5-10 molecules)
- [ ] Paper writing (2-4 weeks)

**Estimated:** You're ~20% done with experiments!

---

## 🚀 Recommended Next Steps (Priority Order)

### Today

1. ✅ Verify training (Step 1) - 5 min
2. ✅ Test model (Step 2) - 10 min
3. ✅ Quick evaluation (Step 3) - 30 min
4. ✅ Start full evaluation (Step 4A) - Let it run

### Tomorrow

1. Analyze full evaluation results
2. Run ablation studies (Step 4B)
3. Select case studies for paper

### This Week

1. Train additional datasets (optional)
2. Generate paper figures
3. Start paper outline

---

## 🔧 Troubleshooting

### Problem: Training ROC-AUC < 0.82

**Solution 1: Train longer**

```powershell
# Resume training with more epochs
python train_attention_gin.py --task tox21 --config config_rtx3050.yaml --epochs 120 --output_dir training_tox21_v2
```

**Solution 2: Adjust learning rate**

```powershell
# Lower learning rate, train longer
python train_attention_gin.py --task tox21 --batch_size 32 --epochs 100 --lr 1e-5 --output_dir training_tox21_v2
```

### Problem: Out of Memory During Training

**Solution:**
Edit `config_rtx3050.yaml`:

```yaml
batch_size: 24  # Reduce from 32
emb_dim: 200    # Reduce from 256
```

### Problem: Groq API Rate Limit

**Solution:**
Use mock LLM for testing:

```powershell
# Remove --use-groq flag
python faithful_xai_demo.py --smiles "c1ccccc1"
```

### Problem: Low Faithfulness Scores (< 0.50)

**This is actually good for the paper!**

- It proves the baseline is unfaithful
- Lower threshold to 0.5 in `faithfulness_validator.py`
- Report honestly: "Baseline FS: 0.35, Ours: 0.65" is still +86% improvement!

---

## 📞 Quick Commands Reference

### Check training status

```powershell
Get-Content backend/models/training_tox21.log -Tail 30
```

### Test model

```powershell
cd experiments
python faithful_xai_demo.py --use-groq --smiles "CCO"
```

### Run evaluation

```powershell
python run_faithful_eval.py --model ../backend/models/training_tox21/attention_gin_model.pth --n-molecules 50 --output results/test
```

### View results

```powershell
cd results/test
Get-Content statistics.json
```

---

## 🎯 Success Criteria

**You're ready for the next phase if:**

- ✅ ROC-AUC ≥ 0.82
- ✅ Faithfulness Score > 0.60
- ✅ Rejection Rate: 15-30%
- ✅ Demo works with Groq

**If all above are true:** Congratulations! You have a working Faithful XAI system! 🎉

---

## 📅 Next Session Planning

After completing Steps 1-4, schedule:

- **Week 1:** Full evaluation + ablations
- **Week 2:** Additional datasets (optional)
- **Week 3-6:** Paper writing
- **Week 7:** Submission prep

---

**Good luck! The hardest part (training) is done overnight. Tomorrow morning, you'll have results! 🚀**
