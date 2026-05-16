class TransientToolError(RuntimeError):
    """表示可重试的临时性错误，例如网络闪断、上游 5xx 或超时。"""


class DeterministicToolError(RuntimeError):
    """表示不可重试的确定性错误，例如入参缺失、业务约束不满足等。"""
