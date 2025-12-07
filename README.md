# cse476-final-agent
1. Chain-of-Thought (CoT)

For each question, the model is asked to “think step by step” and end with
Final Answer: <…>.
This gives me the reasoning trace.

2. Universal Self-Consistency (USC)

Questions get answered multiple times (default is 3 samples), each with different CoT outputs.
Then I run a simple majority vote over the final answers.
This helps reduce randomness and incorrect reasoning.

3. Decomposition / Subquestion Generation

If a question looks multi-step (e.g., contains “and”, “then”, multiple sentences),
my agent asks the model to break it into smaller subquestions.
Each subquestion is solved with CoT + USC, and then everything is recombined into a final answer.
