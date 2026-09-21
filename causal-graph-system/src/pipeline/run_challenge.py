"""挑战档入口：原始文档 -> 抽取 -> 关系 -> 建图 -> 推理。"""
from .orchestrator import run


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="挑战档：原始文档全流程")
    p.add_argument("--config", default="configs/challenge.yaml")
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
