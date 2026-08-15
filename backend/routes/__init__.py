#!/usr/bin/env python3
"""Route blueprints for the PharmaGuard AI backend.

New endpoint groups live here instead of in the legacy ``app.py`` monolith.
Each blueprint exposes an ``init_<name>(**services)`` function that the main
app calls after ``initialize_services`` to inject shared objects
(predictor, faithfulness_validator, …).
"""
