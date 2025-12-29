# CONTRIBUTING.md - DeNovo Drug Discovery Platform

## Welcome Contributors

Thank you for your interest in contributing to DeNovo. This document provides guidelines for contributing to the project.

---

## 🚀 Getting Started

### Setting Up Development Environment

1. **Fork and Clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/DeNovo.git
   cd DeNovo-main
   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: .\venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**

   ```bash
   # Install PyTorch first
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   pip install torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
   
   # Install remaining dependencies
   pip install -r requirements.txt
   ```

4. **Run Tests**

   ```bash
   python scripts/validate_all_models.py
   python scripts/test_api.py
   ```

---

## 📁 Project Structure

```
DeNovo-main/
├── backend/            # Flask API (main focus)
│   ├── app.py          # Main application
│   └── models/         # ML models
├── frontend/           # React.js UI
├── data_packages/      # Training data
├── results/            # Trained models
├── training/           # Training scripts
└── experiments/        # Research experiments
```

---

## 🔧 Types of Contributions

### 1. Adding a New ADMET Model

1. **Prepare Data Package**
   - Create folder: `data_packages/new_model_package/`
   - Include: training data (CSV), test data, and config

2. **Update Training Config**
   - Edit `training/training_config.yaml`
   - Add new model entry with hyperparameters

3. **Train the Model**

   ```bash
   python training/train_all_models.py --model new_model
   ```

4. **Integrate into Unified Predictor**
   - Update `backend/models/unified_predictor.py`
   - Add `_load_new_model()` and `_predict_new_model()` methods

5. **Update API**
   - Add endpoint documentation to README.md

### 2. Improving Explainability

- Work on: `backend/models/faithfulness_validator.py`
- Add new validation tests to the faithfulness checker
- Improve SMARTS patterns in `backend/utils/substructure_mapper.py`

### 3. Frontend Improvements

- Work in: `frontend/src/`
- Use React.js best practices
- Follow existing component patterns

---

## 📝 Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints where possible
- Document functions with docstrings
- Maximum line length: 100 characters

### JavaScript/React

- Use functional components with hooks
- Follow ESLint configuration
- Use meaningful component names

### Commits

- Use descriptive commit messages
- Format: `type(scope): description`
- Examples:
  - `feat(model): add hepatotoxicity predictor`
  - `fix(api): handle invalid SMILES input`
  - `docs(readme): update installation instructions`

---

## 🧪 Testing

Before submitting a PR, ensure:

1. **Models Load Successfully**

   ```bash
   python scripts/validate_all_models.py
   ```

2. **API Endpoints Work**

   ```bash
   python scripts/test_api.py
   ```

3. **Backend Starts Without Errors**

   ```bash
   cd backend && python app.py
   ```

---

## 📤 Submitting Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests
4. Commit with descriptive message
5. Push to your fork
6. Open a Pull Request

### PR Checklist

- [ ] Code follows project style
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] README updated (if applicable)
- [ ] No breaking changes (or documented)

---

## 🐛 Reporting Issues

When reporting bugs, include:

- Operating system and Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages (full traceback)
- SMILES string (if molecule-related)

---

## 📧 Contact

- **Maintainer**: Gaurav Patil
- **Email**: <gauravppaiml123@gst.sies.edu.in>
- **GitHub Issues**: Preferred for bug reports and feature requests

---

Thank you for contributing to safer drug discovery! 🧬
