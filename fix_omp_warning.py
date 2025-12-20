#!/usr/bin/env python3
"""修復 OMP 警告並優化性能"""

import os

# 在導入任何庫之前設置環境變量
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# 禁用 OMP nested 警告
os.environ['KMP_WARNINGS'] = '0'

print("✅ 環境變量已設置")
print(f"  OMP_NUM_THREADS: {os.environ['OMP_NUM_THREADS']}")
print(f"  MKL_NUM_THREADS: {os.environ['MKL_NUM_THREADS']}")

