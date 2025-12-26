import argparse
import os
import shutil
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
        # 使用 --print 模式进行非交互式运行，避免 TTY/raw mode 错误
        # 使用 --dangerously-skip-permissions 标志跳过权限检查
        # 将提示词作为命令行参数传递（或通过 stdin）
        print(f"[CMD] claude --print --dangerously-skip-permissions (with prompt input)")
        print(f"[INFO] Prompt length: {len(prompt)} characters")
        print(f"[INFO] Starting Claude analysis (this may take several minutes)...")

        # 查找 claude 命令的完整路径
        claude_cmd = shutil.which("claude")
        if not claude_cmd:
            print(
                "[ERROR] 'claude' command not found. Please ensure it is installed and in your PATH."
            )
            print("[INFO] You can install it by running: npm install -g @anthropic-ai/claude-code")
            print("[INFO] Or visit: https://docs.claude.com/zh-CN/docs/claude-code/installation")
            sys.exit(1)

        try:
            # 使用 --print 模式进行非交互式运行
            # 将提示词通过 stdin 传入（在 --print 模式下支持非交互式输入）
            print("[INFO] Executing Claude command...")
            print("[INFO] This may take several minutes. Please wait...")
            sys.stdout.flush()
            
            import time
            start_time = time.time()
            
            print("[INFO] Sending prompt to Claude...")
            print("=" * 80)
            print("[CLAUDE OUTPUT START]")
            print("=" * 80)
            sys.stdout.flush()
            
            # 使用 -p 参数直接传递提示词，比 stdin 更可靠
            # 在 Windows 上使用 subprocess.run 替代 Popen 以避免缓冲问题
            process = subprocess.Popen(
                [
                    claude_cmd,
                    "--print",
                    "--dangerously-skip-permissions",
                    "-p",
                    prompt,
                ],
                stdin=subprocess.DEVNULL,  # 不需要 stdin
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并 stderr 到 stdout
                text=True,
                bufsize=0,  # 无缓冲，避免 Windows 缓冲问题
                env={**os.environ, "PYTHONUNBUFFERED": "1"},  # 确保 Python 子进程无缓冲
            )

            print(f"[DEBUG] Process started with prompt via -p flag")
            sys.stdout.flush()
            
            # 实时读取输出
            stdout_lines = []

            print("[INFO] Waiting for Claude response (this may take several minutes)...")
            print("[DEBUG] Process PID: {}".format(process.pid))
            sys.stdout.flush()

            # 在 Windows 上使用 communicate() 更可靠，避免管道死锁
            # 设置超时为 1 小时（3600秒）
            try:
                # 显示进度信息的线程
                import threading
                stop_progress = threading.Event()

                def show_progress():
                    while not stop_progress.is_set():
                        elapsed = time.time() - start_time
                        print(f"[INFO] Still processing... ({elapsed:.0f} seconds elapsed)", flush=True)
                        stop_progress.wait(30)  # 每30秒显示一次

                progress_thread = threading.Thread(target=show_progress, daemon=True)
                progress_thread.start()

                # 使用 communicate() 等待进程完成
                stdout, _ = process.communicate(timeout=3600)

                stop_progress.set()
                progress_thread.join(timeout=1)

                if stdout:
                    # 过滤掉 starship 错误
                    lines = stdout.split('\n')
                    for line in lines:
                        if not ("starship" in line.lower() and "error" in line.lower()):
                            print(line, flush=True)
                            stdout_lines.append(line + '\n')

            except subprocess.TimeoutExpired:
                print("\n[ERROR] Claude command timed out after 1 hour")
                process.kill()
                process.communicate()  # 清理
                raise
            except Exception as e:
                print(f"\n[ERROR] Error reading output: {e}")
                import traceback
                traceback.print_exc()
                raise

            # 汇总输出
            stdout = ''.join(stdout_lines) if stdout_lines else ''
            stderr = ''  # stderr 已合并到 stdout
            
            print("\n" + "=" * 80)
            print("[CLAUDE OUTPUT END]")
            print("=" * 80)
            
            elapsed_time = time.time() - start_time
            print(f"[INFO] Claude command finished in {elapsed_time:.1f} seconds")

            # 检查返回码
            returncode = process.returncode
            if returncode == 0:
                if stdout.strip():
                    print(f"\n[SUCCESS] Claude command completed successfully (exit code: {returncode})")
                else:
                    print(f"\n[WARN] Claude completed but produced no output (exit code: {returncode})")
            else:
                print(f"\n[ERROR] Claude command exited with code {returncode}")
                if stderr:
                    print("[ERROR] Error details:")
                    print(stderr)
                # 不立即退出，允许继续处理其他任务
                
        except subprocess.TimeoutExpired:
            print("[ERROR] Claude command timed out after 1 hour")
            process.kill()
            sys.exit(1)
        except FileNotFoundError:
            print(
                f"[ERROR] 'claude' command not found at: {claude_cmd}"
            )
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[WARN] Script interrupted by user.")
            if 'process' in locals():
                process.kill()
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
