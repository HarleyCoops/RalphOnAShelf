"""Simple E2B sandbox test - verifies connection and execution."""
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()

print("Creating E2B sandbox...")
sbx = Sandbox()
try:
    print(f"Sandbox created! ID: {sbx.sandbox_id}")

    # Test basic execution
    print("\nRunning Python code...")
    result = sbx.run_code('print("Hello from E2B sandbox!")')

    if result.logs.stdout:
        print(f"Output: {''.join(result.logs.stdout)}")

    if result.error:
        print(f"Error: {result.error}")

    # Test a more complex operation
    print("\nTesting calculation...")
    result = sbx.run_code('''
import sys
print(f"Python version: {sys.version}")
primes = [n for n in range(2, 50) if all(n % i != 0 for i in range(2, int(n**0.5)+1))]
print(f"Primes under 50: {primes}")
''')

    if result.logs.stdout:
        print(''.join(result.logs.stdout))

    print("\nE2B sandbox test complete!")
finally:
    sbx.kill()
