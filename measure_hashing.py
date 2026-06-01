import hashlib
import os
import time
import statistics

def measure(label, hash_func, iterations=1000):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        hash_func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # convert ke ms
    
    avg = statistics.mean(times)
    std = statistics.stdev(times)
    mn  = min(times)
    mx  = max(times)
    
    print(f"\n{label}:")
    print(f"  Rata-rata : {avg:.4f} ms")
    print(f"  Std Dev   : {std:.4f} ms")
    print(f"  Min       : {mn:.4f} ms")
    print(f"  Max       : {mx:.4f} ms")

password = "TestPassword123"

# MD5 Tanpa Salt
measure("MD5 Tanpa Salt", lambda: 
    hashlib.md5(password.encode()).hexdigest()
)

# MD5 Dengan Salt
measure("MD5 Dengan Salt", lambda: (
    lambda salt: hashlib.md5((password + salt.hex()).encode()).hexdigest()
)(os.urandom(16))
)

# SHA-256 Tanpa Salt
measure("SHA-256 Tanpa Salt", lambda: 
    hashlib.sha256(password.encode()).hexdigest()
)

# SHA-256 Dengan Salt
measure("SHA-256 Dengan Salt", lambda: (
    lambda salt: hashlib.sha256((password + salt.hex()).encode()).hexdigest()
)(os.urandom(16))
)

print("\nSelesai!")