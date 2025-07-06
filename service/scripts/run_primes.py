"""Generate prime numbers less than N and save them to a CSV file."""
import argparse
import csv


def sieve(n):
    """Return list of prime numbers less than n using Sieve of Eratosthenes."""
    if n < 2:
        return []
    sieve_list = [True] * n
    sieve_list[0:2] = [False, False]
    for i in range(2, int(n ** 0.5) + 1):
        if sieve_list[i]:
            for j in range(i * i, n, i):
                sieve_list[j] = False
    return [i for i, is_prime in enumerate(sieve_list) if is_prime]


def main(n):
    """Compute primes and write them to result.csv."""
    primes = sieve(n)
    output_file = 'result.csv'
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['prime'])
        for p in primes:
            writer.writerow([p])
    print(f'Primes saved to {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate primes less than N.')
    parser.add_argument('--n', type=int, required=True,
                        help='Upper bound (exclusive) for prime generation')
    args = parser.parse_args()
    main(args.n)