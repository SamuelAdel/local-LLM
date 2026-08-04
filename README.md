<<<<<<< HEAD
h
=======
# Local LLM Evaluation for Text-to-SQL

## Project Overview

This project evaluates multiple open-source Local Large Language Models (LLMs) to select the best model for a Text-to-SQL system.

The evaluation focuses on running models locally using Ollama and comparing them based on:

- SQL generation quality
- Schema understanding
- Reasoning ability
- Response quality
- Inference speed
- Resource usage
- Overall suitability for our project

The selected model will be integrated into our final Text-to-SQL pipeline.

---

# Goal

Choose the best Local LLM that provides the best balance between:

- SQL Accuracy
- Response Time
- Resource Consumption
- Ease of Deployment

instead of selecting a model based only on popularity.

---

# Candidate Models

Current evaluation candidates:

- Qwen2.5-Coder 7B
- Gemma 3 4B
- Llama 3.1 8B
- DeepSeek-R1 7B

Additional models may be added later if necessary.

---

# Evaluation Criteria

Each model will be evaluated using the following metrics.

| Metric | Description |
|---------|-------------|
| SQL Accuracy | Ability to generate correct SQL queries |
| Schema Understanding | Correct understanding of database schema |
| Instruction Following | Ability to follow prompt instructions |
| Hallucination | Generates nonexistent tables or columns |
| Reasoning | Logical thinking capability |
| Response Time | Time required to generate the answer |
| Memory Usage | RAM / GPU Memory consumption |
| Ease of Use | Easy to run locally |
| Overall Performance | Final evaluation score |

---

# Project Structure

```
Local-LLM-Evaluation/

│
├── README.md
├── models.md
├── prompts.md
├── evaluation_results.xlsx
├── run_model.py
└── requirements.txt
```

---

# Evaluation Workflow

Research
↓

Select Candidate Models
↓

Download Models using Ollama
↓

Run Standard Prompt Set
↓

Collect Responses

↓

Evaluate Responses

↓

Compare Results

↓

Select Best Model

↓

Integrate into Final Project

---

# Model Testing Procedure

Each model will receive exactly the same prompts.

The prompts are divided into several categories:

- General reasoning
- SQL generation
- Schema understanding
- SQL correction
- Complex SQL reasoning
- Edge cases

This guarantees a fair comparison.

---

# Output

Each model will produce:

- Generated SQL
- Execution time
- Notes
- Evaluation score

All outputs will be documented inside the evaluation sheet.

---

# Tools

- Python
- VS Code
- Ollama
- Git
- Google Sheets (for collaboration)

---

# Team Workflow

Each team member is responsible for evaluating assigned models.

The evaluation process is identical for all members.

Results are merged into one shared evaluation sheet.

---

# Final Deliverable

The final report will include:

- Model comparison table
- Evaluation scores
- Strengths and weaknesses
- Final selected model
- Justification for selection
>>>>>>> d09c6abd6de21f3073a1120be4c07baf6e908b2f
