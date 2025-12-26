import argparse
import os
import subprocess
import sys

# 定义任务列表
# 格式: (Header Name, Git Repo URL, Submodule Path, Space Folder Name)
tasks = [
    (
        "Ladybird",
        "git@github.com:LadybirdBrowser/ladybird.git",
        "venders/ladybird",
        "ladybird",
    ),
    ("CrewAI", "git@github.com:crewAIInc/crewAI.git", "venders/crewAI", "crewAI"),
    (
        "LangGraph",
        "git@github.com:langchain-ai/langgraph.git",
        "venders/langgraph",
        "langgraph",
    ),
    (
        "Moondream",
        "git@github.com:vikhyat/moondream.git",
        "venders/moondream",
        "moondream",
    ),
    ("RAGFlow", "git@github.com:infiniflow/ragflow.git", "venders/ragflow", "ragflow"),
    (
        "Granian",
        "git@github.com:emmett-framework/granian.git",
        "venders/granian",
        "granian",
    ),
    ("Bun", "git@github.com:oven-sh/bun.git", "venders/bun", "bun"),
    ("Candle", "git@github.com:huggingface/candle.git", "venders/candle", "candle"),
    ("Qdrant", "git@github.com:qdrant/qdrant.git", "venders/qdrant", "qdrant"),
    (
        "SurrealDB",
        "git@github.com:surrealdb/surrealdb.git",
        "venders/surrealdb",
        "surrealdb",
    ),
    ("Spin", "git@github.com:spinframework/spin.git", "venders/spin", "spin"),
    (
        "WasmEdge",
        "git@github.com:WasmEdge/WasmEdge.git",
        "venders/WasmEdge",
        "WasmEdge",
    ),
    (
        "AppFlowy",
        "git@github.com:AppFlowy-IO/AppFlowy.git",
        "venders/AppFlowy",
        "AppFlowy",
    ),
    ("NocoDB", "git@github.com:nocodb/nocodb.git", "venders/nocodb", "nocodb"),
    (
        "Appwrite",
        "git@github.com:appwrite/appwrite.git",
        "venders/appwrite",
        "appwrite",
    ),
]


def run_task(start_index=0, end_index=None):
    tasks_to_run = tasks[start_index:end_index]
    print(
        f"[INFO] Running tasks range: [{start_index} : {end_index if end_index is not None else 'End'}]"
    )

    for name, repo, sub_path, space_folder in tasks_to_run:
        print(f"\n{'='*20}")
        print(f"Processing: {name}")
        print(f"{'='*20}")

        # 1. 执行 git submodule add
        if os.path.exists(sub_path):
            print(
                f"[INFO] Path '{sub_path}' already exists. Skipping git submodule add."
            )
        else:
            print(f"[CMD] git submodule add {repo} {sub_path}")
            try:
                subprocess.run(["git", "submodule", "add", repo, sub_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to add submodule: {e}")
                continue

        # Check if document exists
        doc_path = f"./space/{space_folder}/{space_folder}-arch-design.md"
        if os.path.exists(doc_path):
            print(
                f"[INFO] Document '{doc_path}' already exists. Skipping claude analysis."
            )
            print(f"[DONE] Finished processing {name}.")
            continue

        # 2. 构建提示词
        # 注意：这里根据 instructions.md 的格式生成提示词
        prompt = (
            f"仔细阅读 /{sub_path} 的代码，撰写一个详细的架构分析文档，"
            f"如需图表，使用 mermaid chart 文档放在 ./space/{space_folder}/{space_folder}-arch-design.md "
        )

        print(f"[INFO] Prompt generated for {name}.")

        # 3. 执行 claude
        # 使用 --dangerously-skip-permissions 标志
        # 将提示词通过 stdin 传入
        print(f"[CMD] claude --dangerously-skip-permissions (with prompt input)")

        try:
            # input=prompt 会将字符串写入 stdin，并在写入完成后关闭 stdin。
            # 大多数 CLI 工具在 stdin 关闭后会处理输入并最终退出。
            subprocess.run(
                ["claude", "--dangerously-skip-permissions"],
                input=prompt,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            print(
                "[ERROR] 'claude' command not found. Please ensure it is installed and in your PATH."
            )
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[WARN] Script interrupted by user.")
            sys.exit(1)

        # 4. 提交并推送更改
        print(
            f"[CMD] git add . && git commit -m 'Add architecture design for {name}' && git push"
        )
        try:
            subprocess.run(["git", "add", "."], check=True)
            # Check if there are changes to commit
            status = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            if status.stdout.strip():
                subprocess.run(
                    ["git", "commit", "-m", f"Add architecture design for {name}"],
                    check=True,
                )
                subprocess.run(["git", "push"], check=True)
            else:
                print("[INFO] No changes to commit.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to commit/push changes: {e}")

        print(f"[DONE] Finished processing {name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch analysis tasks.")
    parser.add_argument(
        "--start", type=int, default=0, help="Start index of tasks to run"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="End index of tasks to run"
    )
    parser.add_argument(
        "-i",
        "--index",
        type=int,
        default=None,
        help="Specific index of task to run (overrides start/end)",
    )

    args = parser.parse_args()

    if args.index is not None:
        run_task(args.index, args.index + 1)
    else:
        run_task(args.start, args.end)
