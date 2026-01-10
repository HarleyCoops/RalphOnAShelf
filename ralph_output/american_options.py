import numpy as np
from typing import Literal


class AmericanOption:
    """
    American Option Pricing Framework

    Implements three methods:
    1. Binomial Tree (CRR model)
    2. Finite Difference (Crank-Nicolson)
    3. Least Squares Monte Carlo (Longstaff-Schwartz)
    """

    def __init__(self, S: float, K: float, T: float, r: float, sigma: float,
                 option_type: Literal['call', 'put'] = 'put'):
        """
        Initialize American Option parameters

        Args:
            S: Current stock price
            K: Strike price
            T: Time to maturity (years)
            r: Risk-free rate
            sigma: Volatility
            option_type: 'call' or 'put'
        """
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.option_type = option_type

    def payoff(self, S: np.ndarray) -> np.ndarray:
        """Calculate option payoff"""
        if self.option_type == 'put':
            return np.maximum(self.K - S, 0)
        else:
            return np.maximum(S - self.K, 0)

    def binomial_tree(self, N: int = 1000) -> float:
        """
        Price American option using Binomial Tree (CRR model)

        Args:
            N: Number of time steps

        Returns:
            Option price
        """
        dt = self.T / N
        u = np.exp(self.sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(self.r * dt) - d) / (u - d)
        discount = np.exp(-self.r * dt)

        # Initialize asset prices at maturity
        S_T = self.S * d ** np.arange(N, -1, -1) * u ** np.arange(0, N + 1)

        # Initialize option values at maturity
        V = self.payoff(S_T)

        # Backward induction
        for i in range(N - 1, -1, -1):
            S_t = self.S * d ** np.arange(i, -1, -1) * u ** np.arange(0, i + 1)
            V = discount * (p * V[1:i+2] + (1 - p) * V[0:i+1])
            # Early exercise
            V = np.maximum(V, self.payoff(S_t))

        return V[0]

    def finite_difference(self, M: int = 1000, N: int = 1000,
                         S_max: float = None) -> float:
        """
        Price American option using Finite Difference (Crank-Nicolson)

        Args:
            M: Number of space steps
            N: Number of time steps
            S_max: Maximum stock price for grid (default: 5 * K)

        Returns:
            Option price
        """
        if S_max is None:
            S_max = 5 * self.K

        dS = S_max / M
        dt = self.T / N

        # Create price grid
        S_grid = np.linspace(0, S_max, M + 1)

        # Initialize option values at maturity
        V = self.payoff(S_grid)

        # Precompute coefficients for interior points
        j = np.arange(1, M)
        S_j = S_grid[1:-1]

        # Standard finite difference coefficients
        alpha = 0.25 * dt * ((self.sigma * j) ** 2 - self.r * j)
        beta = -0.5 * dt * ((self.sigma * j) ** 2 + self.r)
        gamma = 0.25 * dt * ((self.sigma * j) ** 2 + self.r * j)

        # Build tridiagonal matrix (implicit part)
        M1 = np.zeros((M - 1, M - 1))
        M2 = np.zeros((M - 1, M - 1))

        for i in range(M - 1):
            M1[i, i] = 1 - beta[i]
            M2[i, i] = 1 + beta[i]

            if i > 0:
                M1[i, i-1] = -alpha[i]
                M2[i, i-1] = alpha[i]

            if i < M - 2:
                M1[i, i+1] = -gamma[i]
                M2[i, i+1] = gamma[i]

        # Backward time stepping
        for _ in range(N):
            # Right-hand side vector
            V_rhs = M2 @ V[1:-1]

            # Add boundary conditions to RHS
            if self.option_type == 'put':
                V_rhs[0] += alpha[0] * self.K
                V_rhs[-1] += gamma[-1] * 0
            else:
                V_rhs[0] += alpha[0] * 0
                V_rhs[-1] += gamma[-1] * max(S_max - self.K, 0)

            # Solve linear system M1 * V_new = V_rhs
            V_interior = np.linalg.solve(M1, V_rhs)

            # Apply boundary conditions
            V_new = np.zeros(M + 1)
            if self.option_type == 'put':
                V_new[0] = self.K
                V_new[-1] = 0
            else:
                V_new[0] = 0
                V_new[-1] = max(S_max - self.K, 0)

            V_new[1:-1] = V_interior

            # Apply early exercise condition (American feature)
            V = np.maximum(V_new, self.payoff(S_grid))

        # Interpolate to get option value at current spot price
        idx = np.searchsorted(S_grid, self.S)
        if idx == 0:
            return V[0]
        elif idx >= len(S_grid):
            return V[-1]
        else:
            # Linear interpolation
            weight = (self.S - S_grid[idx-1]) / (S_grid[idx] - S_grid[idx-1])
            return V[idx-1] * (1 - weight) + V[idx] * weight

    def lsmc(self, n_paths: int = 100000, n_steps: int = 100,
             poly_degree: int = 3, seed: int = 42) -> float:
        """
        Price American option using Least Squares Monte Carlo (Longstaff-Schwartz)

        Args:
            n_paths: Number of simulation paths
            n_steps: Number of time steps
            poly_degree: Degree of polynomial for regression
            seed: Random seed for reproducibility

        Returns:
            Option price
        """
        np.random.seed(seed)

        dt = self.T / n_steps
        discount = np.exp(-self.r * dt)

        # Simulate stock price paths
        Z = np.random.standard_normal((n_paths, n_steps))
        S = np.zeros((n_paths, n_steps + 1))
        S[:, 0] = self.S

        for t in range(1, n_steps + 1):
            S[:, t] = S[:, t-1] * np.exp((self.r - 0.5 * self.sigma ** 2) * dt +
                                         self.sigma * np.sqrt(dt) * Z[:, t-1])

        # Calculate payoffs at each time step
        payoffs = self.payoff(S)

        # Initialize cash flow matrix (when option is exercised)
        cash_flows = payoffs[:, -1]

        # Backward induction
        for t in range(n_steps - 1, 0, -1):
            # Find in-the-money paths
            itm = payoffs[:, t] > 0

            if np.sum(itm) == 0:
                cash_flows *= discount
                continue

            # Regression on in-the-money paths
            X = S[itm, t]
            Y = cash_flows[itm] * discount

            # Create polynomial features
            poly_features = np.column_stack([X ** i for i in range(poly_degree + 1)])

            # Least squares regression
            try:
                coeffs = np.linalg.lstsq(poly_features, Y, rcond=None)[0]
                continuation_value = poly_features @ coeffs
            except np.linalg.LinAlgError:
                continuation_value = Y

            # Exercise decision
            exercise = payoffs[itm, t] > continuation_value

            # Update cash flows
            cash_flows[itm] = np.where(exercise, payoffs[itm, t],
                                      cash_flows[itm] * discount)
            cash_flows[~itm] *= discount

        # Discount to present value
        option_value = discount * np.mean(cash_flows)

        return option_value
