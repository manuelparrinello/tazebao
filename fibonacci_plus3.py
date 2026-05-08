def fibonacci_plus_3(n=200):
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a + 3)
        a, b = b, a + b
    return result
