from __future__ import annotations

import kagglehub


def main() -> None:
    path = kagglehub.dataset_download("emmarex/plantdisease")
    print(f"Dataset downloaded to: {path}")


if __name__ == "__main__":
    main()
