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

| Model | Ollama Tag |
|-------|-----------|
| Qwen2.5-Coder 7B | `qwen2.5-coder:7b` |
| Gemma 3 4B | `gemma3:4b` |
| Llama 3.1 8B | `llama3.1:8b` |
| DeepSeek-R1 7B | `deepseek-r1:7b` |

These tags are kept in sync with `MODELS` in `models.py`. If you change one, change both.

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
├── config.py            # generation settings (temperature, ctx, timeout, ...)
├── models.py            # candidate model list (Ollama tags)
├── schema.py            # database schema given to every model
├── prompt.py            # shared prompt template
├── questions.py         # benchmark question set (24 questions)
├── expected_sql.py       # reference / expected SQL per question
├── run_model.py         # sends one question to one model via Ollama
├── evaluate.py          # scores generated SQL against expected_sql.py
├── main.py              # runs the full pipeline, saves results/results.txt
├── requirements.txt
└── results/
    ├── results.txt       # raw generated SQL per model/question
    └── evaluation.txt    # scored comparison report (from evaluate.py)
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

