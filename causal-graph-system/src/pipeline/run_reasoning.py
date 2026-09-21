"""推理档入口：事件列表 -> 因果识别 -> 建图 -> 推理。"""
from .orchestrator import run


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="推理档：事件列表 -> 建图 -> 推理")
    p.add_argument("--config", default="configs/reasoning.yaml")
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
