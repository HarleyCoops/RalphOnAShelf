import numpy as np
import time
from american_options import AmericanOption


def run_analysis():
    """
    Compare American option pricing methods and benchmark runtime
    """
    print("=" * 80)
    print("AMERICAN OPTION PRICING FRAMEWORK - COMPARATIVE ANALYSIS")
    print("=" * 80)

    # Test parameters
    S = 100      # Current stock price
    K = 100      # Strike price
    T = 1        # Time to maturity (1 year)
    r = 0.05     # Risk-free rate (5%)
    sigma = 0.2  # Volatility (20%)
    option_type = 'put'

    print("\nOption Parameters:")
    print(f"  Spot Price (S):       ${S}")
    print(f"  Strike Price (K):     ${K}")
    print(f"  Time to Maturity (T): {T} year")
    print(f"  Risk-free Rate (r):   {r * 100}%")
    print(f"  Volatility (sigma):   {sigma * 100}%")
    print(f"  Option Type:          American {option_type.capitalize()}")
    print()

    # Initialize option
    option = AmericanOption(S, K, T, r, sigma, option_type)

    # Results storage
    results = {}

    # Method 1: Binomial Tree
    print("-" * 80)
    print("METHOD 1: BINOMIAL TREE (CRR Model)")
    print("-" * 80)

    n_steps_bt = [100, 500, 1000, 2000]
    print(f"\nTesting with different time steps:")
    for n in n_steps_bt:
        start = time.time()
        price = option.binomial_tree(N=n)
        elapsed = time.time() - start
        print(f"  N={n:4d}: Price = ${price:.6f}, Time = {elapsed:.4f}s")

    # Final benchmark with N=1000
    start = time.time()
    bt_price = option.binomial_tree(N=1000)
    bt_time = time.time() - start
    results['Binomial Tree'] = {'price': bt_price, 'time': bt_time}
    print(f"\nSelected configuration: N=1000")
    print(f"Price: ${bt_price:.6f}")
    print(f"Runtime: {bt_time:.4f}s")

    # Method 2: Finite Difference
    print("\n" + "-" * 80)
    print("METHOD 2: FINITE DIFFERENCE (Crank-Nicolson)")
    print("-" * 80)

    configs_fd = [(500, 500), (800, 800), (1000, 1000)]
    print(f"\nTesting with different grid sizes (M, N):")
    for M, N in configs_fd:
        start = time.time()
        price = option.finite_difference(M=M, N=N)
        elapsed = time.time() - start
        print(f"  M={M:4d}, N={N:4d}: Price = ${price:.6f}, Time = {elapsed:.4f}s")

    # Final benchmark with M=1000, N=1000
    start = time.time()
    fd_price = option.finite_difference(M=1000, N=1000)
    fd_time = time.time() - start
    results['Finite Difference'] = {'price': fd_price, 'time': fd_time}
    print(f"\nSelected configuration: M=1000, N=1000")
    print(f"Price: ${fd_price:.6f}")
    print(f"Runtime: {fd_time:.4f}s")

    # Method 3: LSMC
    print("\n" + "-" * 80)
    print("METHOD 3: LEAST SQUARES MONTE CARLO (Longstaff-Schwartz)")
    print("-" * 80)

    configs_lsmc = [(50000, 50), (100000, 100), (200000, 100)]
    print(f"\nTesting with different simulation parameters (paths, steps):")
    for n_paths, n_steps in configs_lsmc:
        start = time.time()
        price = option.lsmc(n_paths=n_paths, n_steps=n_steps)
        elapsed = time.time() - start
        print(f"  Paths={n_paths:6d}, Steps={n_steps:3d}: Price = ${price:.6f}, Time = {elapsed:.4f}s")

    # Final benchmark with 100k paths, 100 steps
    start = time.time()
    lsmc_price = option.lsmc(n_paths=100000, n_steps=100)
    lsmc_time = time.time() - start
    results['LSMC'] = {'price': lsmc_price, 'time': lsmc_time}
    print(f"\nSelected configuration: 100,000 paths, 100 steps")
    print(f"Price: ${lsmc_price:.6f}")
    print(f"Runtime: {lsmc_time:.4f}s")

    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON TABLE")
    print("=" * 80)
    print()
    print(f"{'Method':<30} {'Price ($)':<15} {'Runtime (s)':<15} {'Rel Speed'}")
    print("-" * 80)

    min_time = min(r['time'] for r in results.values())

    for method, data in results.items():
        rel_speed = data['time'] / min_time
        print(f"{method:<30} {data['price']:<15.6f} {data['time']:<15.4f} {rel_speed:.2f}x")

    # Price convergence analysis
    print("\n" + "=" * 80)
    print("PRICE CONVERGENCE ANALYSIS")
    print("=" * 80)

    prices = [r['price'] for r in results.values()]
    mean_price = np.mean(prices)
    std_price = np.std(prices)
    max_diff = max(prices) - min(prices)

    print(f"\nMean Price:      ${mean_price:.6f}")
    print(f"Std Deviation:   ${std_price:.6f}")
    print(f"Max Difference:  ${max_diff:.6f}")
    print(f"Relative Spread: {(max_diff / mean_price * 100):.4f}%")

    print("\nDeviation from Mean:")
    for method, data in results.items():
        deviation = data['price'] - mean_price
        pct_dev = (deviation / mean_price) * 100
        print(f"  {method:<30} {deviation:+.6f} ({pct_dev:+.4f}%)")

    # Accuracy vs Speed trade-off
    print("\n" + "=" * 80)
    print("ACCURACY VS SPEED TRADE-OFF")
    print("=" * 80)

    print(f"\n{'Method':<30} {'Accuracy Score':<20} {'Speed Score':<20}")
    print("-" * 80)

    for method, data in results.items():
        # Accuracy: inverse of deviation from mean (normalized)
        accuracy_score = 1.0 - abs(data['price'] - mean_price) / mean_price
        # Speed: inverse of relative time (normalized)
        speed_score = min_time / data['time']
        print(f"{method:<30} {accuracy_score:<20.4f} {speed_score:<20.4f}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()

    return results


if __name__ == "__main__":
    results = run_analysis()
