# Contributing to AnuDrishti (PharmaGuard AI)

Thank you for your interest in contributing to **AnuDrishti**, an open-source, regulatory-grade platform for AI-driven molecular safety assessment and computational toxicology!

---

## Code of Conduct & Scientific Principles

All contributors must adhere to the following **Core Scientific Principles**:
1. **Scientific Honesty**: Never hardcode fabricated empirical coefficients. All algorithms, descriptors, and thresholds must cite published, peer-reviewed literature.
2. **Honest Validation**: Report out-of-fold cross-validation or scaffold-split metrics rather than optimistic random splits.
3. **No Black-Box Hallucinations**: Implement confidence intervals or conformal bounds on predictive outputs.

---

## Development Setup

### 1. Clone & Environment Setup
```bash
git clone https://github.com/GauravPatil2515/AnuDrishti.git
cd AnuDrishti

# Setup Python environment
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Test Suite
Before submitting any pull request, ensure all tests pass:
```bash
PYTHONPATH=".:backend" pytest tests/ -p no:asyncio -v
```

---

## Pull Request Workflow

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Commit your changes with clear, descriptive commit messages.
3. Add unit tests in `tests/` covering your changes.
4. Update documentation in `docs/` and `README.md` if adding or modifying APIs.
5. Push to your fork and submit a Pull Request.

---

## License

By contributing to AnuDrishti, you agree that your contributions will be licensed under the project's **MIT License**.
