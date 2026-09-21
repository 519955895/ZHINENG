"""基础档入口：直接读因果图 + 推理问答。"""
from .orchestrator import run


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="基础档：因果图 -> 推理问答")
    p.add_argument("--config", default="configs/basic.yaml")
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
