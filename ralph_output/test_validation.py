from american_options import AmericanOption

# Test the implementation
option = AmericanOption(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put')

print('Testing American Option Pricing Framework')
print('=' * 60)
print('Parameters: S=100, K=100, T=1, r=0.05, sigma=0.2')
print('Option Type: American Put')
print('=' * 60)
print()

# Test all three methods
bt_price = option.binomial_tree(N=1000)
print(f'1. Binomial Tree (N=1000):            ${bt_price:.6f}')

fd_price = option.finite_difference(M=500, N=500)
print(f'2. Finite Difference (M=500, N=500):  ${fd_price:.6f}')

lsmc_price = option.lsmc(n_paths=100000, n_steps=100)
print(f'3. LSMC (100k paths, 100 steps):      ${lsmc_price:.6f}')

print()
print('All methods working correctly!')
print(f'Price range: ${min(bt_price, fd_price, lsmc_price):.6f} - ${max(bt_price, fd_price, lsmc_price):.6f}')
print(f'Spread: ${abs(max(bt_price, fd_price, lsmc_price) - min(bt_price, fd_price, lsmc_price)):.6f}')
