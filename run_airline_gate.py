from airline_panel.bts_t100 import save_panel
from airline_panel.gate import run_gate


if __name__ == "__main__":
    save_panel("data/airline_t100_panel.csv", start="2019-01", end="2026-05")
    summary, ic = run_gate("data/airline_t100_panel.csv")
    print("\n=== BUCKET GATE ===")
    print(summary.to_string(index=False))
    print("\n=== RANK IC ===")
    print(ic.to_string(index=False))
