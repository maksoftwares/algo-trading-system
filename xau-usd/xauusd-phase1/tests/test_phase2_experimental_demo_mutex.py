from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"


def test_a1_executor_claims_gv_mutex_before_order_send():
    source = EA_SOURCE.read_text(encoding="utf-8")

    claim_call = source.index("if(!ClaimFamilyMutexBeforeOrder(observation, mutex_name))")
    order_send = source.index("bool sent = OrderSend(request, result);")

    assert claim_call < order_send
    assert "GlobalVariableSetOnCondition(mutex_name, (double)magic, 0.0)" in source
    assert source.index("GlobalVariableSetOnCondition(mutex_name, (double)magic, 0.0)") < order_send


def test_a1_executor_mutex_namespace_and_expiry_are_source_locked():
    source = EA_SOURCE.read_text(encoding="utf-8")

    assert 'return "FAMMUX_" + IntegerToString(family) + _Symbol + direction + CompactDateTimeForGlobalVariable(bar_time);' in source
    assert "FamilyCodeForMagic(InstanceMagic())" in source
    assert "FamilyMutexDirectionToken(observation.direction_text)" in source
    assert "CurrentM5BarStart()" in source
    assert "PeriodSeconds(PERIOD_M5)" in source
    assert "GlobalVariableTemp(mutex_name)" in source
    assert "WOULD_DUPLICATE_FAMILY_EVENT" in source


def test_a1_executor_writes_startup_gv_mutex_self_test_row():
    source = EA_SOURCE.read_text(encoding="utf-8")

    assert "RunFamilyMutexNamespaceSelfTest" in source
    assert "FAMMUX_SELFTEST_" in source
    assert "GV_MUTEX_NAMESPACE_SELF_TEST_PASS" in source
    assert "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL" in source
    assert "WriteStartupRow(gv_mutex_self_test_status);" in source
