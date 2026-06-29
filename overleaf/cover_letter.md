# Cover Letter

**Manuscript:** DeNovo: A Faithful, Multi-Task AI Platform for Safer Drug Discovery with LLM-Augmented Explainability

**Authors:** Gaurav Patil, Parth Parmar

---

Dear Editor,

We are pleased to submit our manuscript, *"DeNovo: A Faithful, Multi-Task AI Platform for Safer Drug Discovery with LLM-Augmented Explainability,"* for consideration.

Graph Neural Networks now predict molecular ADMET properties with strong accuracy, and Large Language Models can turn those predictions into fluent natural-language explanations. But a critical, under-measured risk sits at their intersection: an LLM can produce a chemically plausible explanation that is *causally disconnected* from what the predictive model actually learned. In a safety-critical domain such as toxicity screening, acting on such an unfaithful explanation can be worse than having no explanation at all.

Our central contribution is a method for **causally validating LLM explanations of GNN predictions**. Rather than trusting the LLM's narrative, DeNovo treats it as an untrusted translator whose every structural claim must survive a counterfactual intervention on the GNN. We formalize a faithfulness score as the geometric mean of a **grounding** component (does the cited substructure carry high model attention, under a size-invariant adaptive cutoff?) and a **causal-consistency** component (does removing the cited substructure change the prediction?), and we enforce it through a reject-and-retry generation loop. Crucially, we draw an explicit distinction between **faithfulness and correctness**: DeNovo guarantees that an explanation honestly reflects the model's reasoning, enabling a domain expert to then judge whether that reasoning is chemically sound.

We believe this work is a good fit for the journal because it addresses trustworthy AI in a high-stakes biomedical setting with a concrete, reproducible methodology, and because it quantifies---rather than merely asserts---how often LLM explanations in chemistry are unfaithful, by comparing constrained generation against an unconstrained LLM baseline under an identical metric.

We are candid about scope. The faithfulness methodology is evaluated in depth on the **Tox21** toxicity benchmark, using random splits to isolate explanation behavior under controlled conditions. Extending the evaluation to additional toxicity endpoints and to scaffold-split distribution shift is the subject of ongoing work, which we discuss explicitly in the Limitations section. We have deliberately scoped the empirical claims to what our experiments support.

This manuscript is original, has not been published elsewhere, and is not under review at any other venue. The authors declare no conflicts of interest. We thank you and the reviewers in advance for your time and consideration.

Sincerely,

Gaurav Patil and Parth Parmar
