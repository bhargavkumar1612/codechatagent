def fibonacci(n, memo={}):
    if n in memo: return memo[n]
    if n <= 2: return 1
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]

if __name__ == '__main__':
    num = int(input('Enter a number: '))
    print('The {}th Fibonacci number is {}'.format(num, fibonacci(num)))