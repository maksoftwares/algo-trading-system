from src.evaluate import run, write_outputs


if __name__ == "__main__":
    result, annual, vetoes = run()
    write_outputs(result, annual, vetoes)
    print(result["decision"])
    print(
        f"baseline={result['baseline']['net_pnl_usd']:.2f} "
        f"challenger={result['challenger']['net_pnl_usd']:.2f} "
        f"delta={result['delta']['net_pnl_usd']:+.2f}"
    )
