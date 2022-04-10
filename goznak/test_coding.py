from coding import multiplicate

def test_multiplicate():
    # Проверка на примере из задания
    assert multiplicate([1, 2, 3, 4]) == [24, 12, 8, 6]

    # Проверка нулей
    assert multiplicate([0, 1]) == [1, 0]
    assert multiplicate([0, 0, 1]) == [0, 0, 0]

    # Проверка на больших числах. Не должно быть переполнения
    assert multiplicate([1, 10**100]) == [10**100, 1]

    # Граничный случай
    assert multiplicate([]) == []
