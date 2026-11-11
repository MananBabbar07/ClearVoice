def smart_slice(abstract: str, head: int, tail: int) -> str:
    if not abstract:
        return ""
    if len(abstract) <= head + tail:
        return abstract
    if tail <= 0:
        return abstract[:head]
    return f"{abstract[:head]} ... {abstract[-tail:]}"

