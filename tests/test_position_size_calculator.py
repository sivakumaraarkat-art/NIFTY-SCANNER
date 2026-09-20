from trade_selection.position_size_calculator import calculate_position_size


def test_position_size():
    assert calculate_position_size(100000, 0.01, 100, 90) == 100
