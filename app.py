from src.graph.builder import build_application


def main() -> None:
    """命令行入口：启动一个简单的交互式多 Agent 会话。"""
    app = build_application()
    print("电商客服与数据分析 Agent 已启动，输入 quit 退出。")

    while True:
        user_input = input("\n用户: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break

        result = app.invoke({"user_input": user_input})
        print(f"\n助手: {result.get('final_answer', '未生成结果')}")


if __name__ == "__main__":
    main()
