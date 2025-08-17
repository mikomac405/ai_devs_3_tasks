import os

task_files = os.path.join("data", "s04e02")

with open(os.path.join(task_files, "correct.txt"), "r", encoding="utf-8") as f:
    correct = [line.strip() for line in f.readlines()]

with open(os.path.join(task_files, "incorect.txt"), "r", encoding="utf-8") as f:
    incorrect = [line.strip() for line in f.readlines()]

data = ""
for entry in correct:
    data += (
        str(
            {
                "messages": [
                    {"role": "system", "content": "validate data"},
                    {"role": "user", "content": f"{entry}"},
                    {"role": "assistant", "content": "1"},
                ]
            }
        ).replace(" ", "")
        + "\n"
    )

for entry in incorrect:
    data += (
        str(
            {
                "messages": [
                    {"role": "system", "content": "validate data"},
                    {"role": "user", "content": f"{entry}"},
                    {"role": "assistant", "content": "0"},
                ]
            }
        ).replace(" ", "")
        + "\n"
    )

with open(os.path.join(task_files, "finetune.jsonl"), "w", encoding="utf-8") as f:
    f.write(data.replace("'", '"'))
