# Faithful XAI - Quick Start Guide (Windows)

## ✅ System Confirmed

- GPU: RTX 3050 6GB ✅
- Groq API: Active ✅
- Python: Installed ✅

---

## 🚀 Step-by-Step Commands

### 1. Test Demo (After Setup)

```powershell
# Navigate to project
cd "C:\Users\GAURAV PATIL\Downloads\DeNovo-main\DeNovo-main"

# Run demo with benzene
cd experiments
python faithful_xai_demo.py --use-groq --smiles "c1ccccc1"

# Run demo with nitrobenzene (toxic)
python faithful_xai_demo.py --use-groq --smiles "c1ccc([N+](=O)[O-])cc1"
```

**Expected Output:**

- Prediction: ~85% toxic
- Identified toxicophores: Nitro group
- Faithfulness Score: ~0.7
- Validation: PASSED or REJECTED

---

### 2. Start Training (Overnight)

```powershell
# Navigate to models directory
cd "C:\Users\GAURAV PATIL\Downloads\DeNovo-main\DeNovo-main\backend\models"

# Start training (will take 8-12 hours)
python train_attention_gin.py --task tox21 --config config_rtx3050.yaml --output_dir training_tox21
```

**What to expect:**

- Training will output logs every 50 batches
- TensorBoard available at `http://localhost:6006`
- Checkpoints saved in `training_tox21/`
- Best model: `training_tox21/attention_gin_model.pth`

**Monitor progress:**

```powershell
# In another terminal
tensorboard --logdir training_tox21/tensorboard
```

---

### 3. After Training Completes

```powershell
# Check final performance
python -c "import pandas as pd; df = pd.read_csv('training_tox21/training_history.csv'); print(f'Best ROC-AUC: {df.val_score.max():.4f}'); print(f'Epochs: {len(df)}')"

#Expected: ROC-AUC ≥ 0.82
```

---

## 📊 Next Phase: Experiments

### Run Faithful Evaluation

```powershell
cd ../../experiments

# Create evaluation script (I'll provide this)
python run_faithful_eval.py --model ../backend/models/training_tox21/attention_gin_model.pth --output results/faithful_eval
```

**This will generate:**

- Faithfulness scores for test set
- Rejection statistics
- Case studies for paper

---

## 🔧 Troubleshooting

### If GPU not detected

```powershell
nvidia-smi  # Check if GPU is visible
python -c "import torch; print(torch.cuda.is_available())"
```

### If Groq API fails

```powershell
# Check API key
echo $env:GROQ_API_KEY

# Test manually
python -c "from groq import Groq; client = Groq(); print('OK')"
```

### If training OOM (out of memory)

```yaml
# Edit config_rtx3050.yaml
batch_size: 24  # Reduce from 32
emb_dim: 200    # Reduce from 256
```

---

## 📈 Expected Timeline

| Day | Task | Duration |
|-----|------|----------|
| **Today** | Setup + Test demo | 30 min |
| **Tonight** | Training (Tox21) | 8-12 hours |
| **Tomorrow** | Verify results | 1 hour |
| **Day 3-4** | Train other models (ClinTox, BBBP) | 2 nights |
| **Week 2** | Run experiments | 2-3 days |
| **Week 3-6** | Paper writing | 4 weeks |

---

## 🎯 Success Criteria

✅ **Demo runs** → See explanation output  
✅ **Training completes** → ROC-AUC ≥ 0.82  
✅ **Faithfulness Score** → ~0.70-0.75  
✅ **Rejection Rate** → 20-25%  

---

## 📞 Common Questions

**Q: Can I pause training?**  
A: Yes, use Ctrl+C. Resume with `--resume` flag (if implemented) or restart.

**Q: How much power will training use?**  
A: RTX 3050 TDP: ~60-80W. Leave laptop plugged in.

**Q: Can I use the laptop during training?**  
A: Yes, but performance may be slower. Training runs in background.

**Q: What if training fails?**  
A: Reduce batch_size to 24 or 16 in config_rtx3050.yaml

---

## 📁 Important Files

- `config_rtx3050.yaml` - Training configuration
- `faithful_xai_demo.py` - Integration demo
- `train_attention_gin.py` - Training script
- `FAITHFUL_XAI_SUMMARY.md` - Full documentation

---

## 🚀 Ready to Start?

After setup completes, run:

```powershell
python experiments/faithful_xai_demo.py --use-groq --smiles "CCO"
```

If you see output → Setup successful! ✅
