#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

Replace the placeholder logic inside `build_answers()` with your own agent loop
before submitting so the ``output`` fields contain your real predictions.

Reads the input questions from cse_476_final_project_test_data.json and writes
an answers JSON file where each entry contains a string under the "output" key.
"""

from __future__ import annotations


import json
from pathlib import Path
from typing import Any, Dict, List
from agent import answer_question


INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")


def load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data


def build_answers(questions: List[Dict[str, Any]], output_path: Path) -> List[Dict[str, str]]:
    answers = []
    total = len(questions)
    
    # Try to load existing answers if resuming
    if output_path.exists():
        try:
            with output_path.open("r", encoding="utf-8") as fp:
                existing = json.load(fp)
                if len(existing) > 0 and len(existing) < total:
                    answers = existing
                    print(f"Resuming from {len(answers)}/{total} completed answers...")
        except:
            pass
    
    for idx, question in enumerate(questions, start=1):
        # Skip if we already have this answer
        if idx <= len(answers):
            continue
            
        # question object should have an "input" field with the text prompt
        q_text = question["input"]

        # call my agent to get the final answer (no reasoning)
        print(f"Processing question {idx}/{total}...", end=" ", flush=True)
        try:
            pred = answer_question(q_text)
            # make sure it's a clean string
            pred = str(pred).strip()
            answers.append({"output": pred})
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
            answers.append({"output": ""})
        
        # Save progress every 10 questions or at the end
        if idx % 10 == 0 or idx == total:
            with output_path.open("w", encoding="utf-8") as fp:
                json.dump(answers, fp, ensure_ascii=False, indent=2)
            print(f"  Progress saved: {len(answers)}/{total} answers")
    
    return answers


def validate_results(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> None:
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). Please make sure your answer does not include any intermediate results."
            )


def main() -> None:
    questions = load_questions(INPUT_PATH)
    print(f"Loaded {len(questions)} questions from {INPUT_PATH}")
    answers = build_answers(questions, OUTPUT_PATH)

    with OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)
    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully."
    )


if __name__ == "__main__":
    main()

