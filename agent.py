import os, json, textwrap, re, time
import requests

API_KEY  = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")  
MODEL    = os.getenv("MODEL_NAME", "bens_model") 

# basic model call from starter code
def call_model_chat(prompt, system_msg="You are a helpful solver."):
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=50)
        if r.status_code == 200:
            data = r.json()
            txt = data["choices"][0]["message"]["content"]
            return txt
        else:
            return ""
    except:
        return ""

### helper functions
def normalize_ans(a):
    if not a:
        return ""
    s = a.strip().lower()
    s = re.sub(r"[^\w\s\-\+\.]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def majority_vote(ans_list):
    counts = {}
    orig = {}
    for a in ans_list:
        n = normalize_ans(a)
        if not n:
            continue
        counts[n] = counts.get(n, 0) + 1
        if n not in orig:
            orig[n] = a

    if not counts:
        return ans_list[0] if ans_list else ""

    best = max(counts, key=counts.get)
    return orig[best]


def extract_final(text):
    # look for "Final Answer:" line. if not found just return everything
    if not text:
        return ""
    m = re.search(r"final answer\s*:\s*(.*)", text, flags=re.I)
    if m:
        return m.group(1).strip()
    return text.strip()


# Chain of Thought and USC
def cot_once(question):
    cot_prompt = (
        "Think step by step and explain your thinking.\n"
        "Then end with: Final Answer: <answer here>\n\n"
        f"{question}"
    )
    sysmsg = (
        "You are a careful solver. Show your work, then say Final Answer: <...> at the end."
    )
    out = call_model_chat(cot_prompt, sysmsg)
    return out


def solve_with_cot_and_usc(question, samples=3):
    answers = []
    for i in range(samples):
        txt = cot_once(question)
        ans = extract_final(txt)
        answers.append(ans)
        time.sleep(0.1)
    final = majority_vote(answers)
    return final


# decomposition
def needs_decomp(q):
    # my simple rules: if there's and/then or multiple things happening
    low = q.lower()
    if q.count("?") > 1:
        return True
    if any(w in low for w in [" and ", " then ", "first ", "next "]):
        return True
    return False


def make_subqs(q):
    prompt = (
        "Break this problem into a few small subquestions I can solve one by one.\n"
        "Give them as a numbered list like:\n"
        "1. ...\n"
        "2. ...\n\n"
        f"{q}"
    )
    text = call_model_chat(prompt, "split big questions into steps.")
    if not text:
        return [q]

    subs = []
    for line in text.splitlines():
        m = re.match(r"\s*\d+[\.\)]\s*(.+)", line)
        if m:
            subs.append(m.group(1).strip())

    if not subs:
        subs = [q]

    return subs


def combine_subanswers(orig_q, subqs, subans):
    lines = []
    for i, (sq, sa) in enumerate(zip(subqs, subans), 1):
        lines.append(f"{i}. subQ: {sq}")
        lines.append(f"   ans: {sa}")
    stuff = "\n".join(lines)

    prompt = (
        "Here is the original question, and the subquestions + answers.\n"
        "Use them to get the final answer.\n"
        "End with 'Final Answer: <answer>'.\n\n"
        f"Original Q:\n{orig_q}\n\n"
        f"Work:\n{stuff}\n"
    )
    txt = call_model_chat(prompt, "combine subanswers correctly.")
    return extract_final(txt)


# main agent function
def answer_question(question):
    q = question.strip()
    if needs_decomp(q):
        subs = make_subqs(q)
        subans = []
        for sq in subs:
            a = solve_with_cot_and_usc(sq, samples=3)
            subans.append(a)
        final = combine_subanswers(q, subs, subans)
        return final
    else:
        return solve_with_cot_and_usc(q, samples=3)


# quick test when run directly
if __name__ == "__main__":
    print("my agent running. ctrl+c to exit.\n")
    while True:
        try:
            q = input("Question: ").strip()
            if q:
                print("Ans:", answer_question(q))
                print()
        except KeyboardInterrupt:
            print("\ndone")
            break
