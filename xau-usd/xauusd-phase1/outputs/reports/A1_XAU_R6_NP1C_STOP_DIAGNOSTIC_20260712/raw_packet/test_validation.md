# NP1 Validation

Terminal status: `R6_NP1_EVIDENCE_INVALID`

Error count: `8`

## Exact commit, environment, commands, and artifacts

```json
{
  "architecture": "AMD64",
  "artifact_sha256": {
    "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json": "49d55c77c4d226639bde736a20d18e00ffb5e4861f66d2e9b87927eebbe6a757",
    "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.md": "5be5acac45b5806070bd6d719b4b2c8ca64e28734e7b6aaf1b75d7de75645030",
    "compiled/A1XauR6MarketOnlyNativeParityOracle.ex5": "33f8ae50945c52c7f1e81e78a383866650d85145facdddc465ab305b5972ee4e",
    "compiled/A1XauR6MarketOnlyNativeParityOracle.mq5": "dd4e349a047f4e69dca61b81367134c68973a29fd551709739280e7941b64698",
    "compiled/compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log": "82251e5691e6ba275e18a9766f50d6ab225d44abf7ff384a2ac7545d2c8d2e62",
    "compiled/source_equivalence.json": "9e7b893d4af9d44540117cff2ac0e782b1d535d242f40f2ff61a8156ff5382c1",
    "parity/native_prefix_chain_hashes.csv": "847eea3f7acfef897958feeb73f9d2e12a393b111c26d406538facb0171d343b",
    "parity/ordercalcprofit_python_native_parity.csv": "02c17f011fd77b2c7523eee5e994300adb64204ab317b29e8fe67b43b1485207",
    "parity/router_python_native_parity.csv": "f3db548cc44a1e88f098f64c4f72a64b2d6beb581b2c3a5026ca7a4253cdcaff",
    "parity/router_state_summary.csv": "9d1b1a2ac4a84ffd5763972e7f3e831639dea1665d6ef97eb8acfe59129bf891",
    "runs/run1/deal.zero": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/run1/native_assertions.tsv": "d49ecab0cd4db15bc2fdf55f887c8b8135c8eafdccd0af538bc8af2e8f1914fd",
    "runs/run1/native_contract.tsv": "f92759a52d68400e031fe289a9adaaa82d58f3f3efb00feba28e40e9fdaf853a",
    "runs/run1/native_d1_bars.tsv": "65a186fcb5e195120de1483c7908ba003f29b98b735ae9b66bd58cc44831a1b5",
    "runs/run1/native_h1_bars.tsv": "c8aef874a65ec316f47450bd9f058366a16a4e0ebec959ccd380ee10aa8fcf45",
    "runs/run1/native_h4_bars.tsv": "08fb0016a07bd00584a111d94096db8bc1be01575efd8a0576b6918522d1e746",
    "runs/run1/native_ordercalcprofit.tsv": "1a3a2646cc38265b8488ca86f5b26c6eb13eb797689f0583fed5771fb42f4a46",
    "runs/run1/native_report.htm": "bd4b3f91c3f236adf25532651aa3b1e0038fdc563fe18442b0a531c61e8aaf65",
    "runs/run1/native_router_rows.tsv": "0faa2b275c174da027016dc024a0daff59b60f62a9ec2b908d0c556934b96934",
    "runs/run1/order.zero": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/run1/tester.ini": "7d764577ee4d171fbef97ace45c7469151524bf49bf2f811d5cc2320893bce5f",
    "runs/run2/deal.zero": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/run2/native_assertions.tsv": "45926ede7afea31b6bf2758503d98263574e259620cd491724a2ce371517b98e",
    "runs/run2/native_contract.tsv": "f92759a52d68400e031fe289a9adaaa82d58f3f3efb00feba28e40e9fdaf853a",
    "runs/run2/native_d1_bars.tsv": "d3deb5dc0e128e8bdb56266dae15d2b3deff31d5c0fe52dce937dce4f91ae21d",
    "runs/run2/native_h1_bars.tsv": "4cff7935627e263e9cc074c8a722dcbc77a9114bf538bf7def9eafaf11df58bc",
    "runs/run2/native_h4_bars.tsv": "ef06dabe55fb44c928285d4f82f141431da2ce72ab672f31cd4ba1a71f2ea844",
    "runs/run2/native_ordercalcprofit.tsv": "1a3a2646cc38265b8488ca86f5b26c6eb13eb797689f0583fed5771fb42f4a46",
    "runs/run2/native_report.htm": "45ca5bfd3a96471c82719b8f7836f22f3d5e5bf567197c9f5da765a54068a6bd",
    "runs/run2/native_router_rows.tsv": "e3afdee8d828eca855838d1aa6aa1ed33d09ef38f693d4f9a8e2aa9057cdc0eb",
    "runs/run2/order.zero": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "runs/run2/tester.ini": "5e24c123e23e18dbab0ab6457c8a68e8febca65166e1ab2bfee71b421bee9644"
  },
  "commands": [
    {
      "command": [
        "C:\\Program Files\\MetaTrader 5\\MetaEditor64.exe",
        "/compile:C:\\np1-compile-test\\A1XauR6MarketOnlyNativeParityOracle.mq5",
        "/log:C:\\np1-compile-test\\compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log"
      ],
      "exit_code": 1,
      "stderr_base64": "",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stdout_base64": "",
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "command": [
        "C:\\MT5A1M5MomentumBacktest\\terminal64.exe",
        "/portable",
        "/config:C:\\MT5A1M5MomentumBacktest\\Config\\np1_run1.ini"
      ],
      "exit_code": 0,
      "stderr_base64": "",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stdout_base64": "",
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "command": [
        "C:\\MT5A1M5MomentumBacktest\\terminal64.exe",
        "/portable",
        "/config:C:\\MT5A1M5MomentumBacktest\\Config\\np1_run2.ini"
      ],
      "exit_code": 0,
      "stderr_base64": "",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stdout_base64": "",
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "command": [
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase0\\.venv\\Scripts\\python.exe",
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase1\\scripts\\verify_a1_xau_r6_market_only_native_parity.py",
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase1\\outputs\\reports\\A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712",
        "--finalize",
        "--attestation-json",
        "C:\\np1-compile-test\\np1_campaign_attestation.json",
        "--quiet"
      ],
      "exit_code": 0,
      "stderr_base64": "",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stdout_base64": "",
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "command": [
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase0\\.venv\\Scripts\\python.exe",
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase1\\scripts\\verify_a1_xau_r6_market_only_native_parity.py",
        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase1\\outputs\\reports\\A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712",
        "--quiet"
      ],
      "exit_code": 0,
      "stderr_base64": "",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stdout_base64": "",
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ],
  "dependency_versions": {
    "pytest": "9.1.1",
    "python_implementation": "CPython",
    "third_party_runtime_dependencies": {}
  },
  "environment": {
    "account_login": 1025742,
    "currency": "USD",
    "cwd": "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase1",
    "leverage": "1:50",
    "server": "Capital.ComMena-Demo",
    "symbol": "XAUUSD",
    "timezone": "system-local"
  },
  "git_head": "88b2569196b131ebc7fb4a76ac62c7bca5ced7bf",
  "git_status_porcelain": "",
  "git_tree": "4e5e3f9d238e0018448d38840b5b1c63b021bc10",
  "metaeditor_version": "5.0.0.5833",
  "mt5_terminal_build": 5833,
  "os": "Windows-11-10.0.26200-SP0",
  "python_executable": "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system-router-audit\\xau-usd\\xauusd-phase0\\.venv\\Scripts\\python.exe",
  "python_version": "3.14.4",
  "review_authority": {
    "authorization_status": "AUTHORIZED",
    "controlling_review_artifact": "A1_XAU_NP1B4_NP1C_AUTHORIZATION_REVIEW_88B25691_2026_07_12.md",
    "controlling_review_sha256": "5cf99a0e40c0ba43b583ef26849072e9df33dfa1516b4f33c9d0875134965f6c",
    "review_verdict": "PASS",
    "reviewed_generator_commit": "88b2569196b131ebc7fb4a76ac62c7bca5ced7bf",
    "reviewed_generator_tree": "4e5e3f9d238e0018448d38840b5b1c63b021bc10"
  },
  "same_ex5_sha256_run1_run2": "33f8ae50945c52c7f1e81e78a383866650d85145facdddc465ab305b5972ee4e",
  "schema_version": "a1_xau_np1_exact_commit_attestation_v1"
}
```
