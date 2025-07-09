# Chacha20 Side-channel Analysis 
Using the low-cost ChipWhisperer platform, we demonstrate full keystream recovery under nonce reuse via Correlation Power Analysis (CPA). For proper nonce usage, we propose a novel two-phase CPA strategy that successfully recovers key bytes in the first column of the cipher’s internal state by exploiting second-round leakage. While full key recovery remains out of reach, the results confirm exploitable leakage and highlight practical risks in ChaCha20 implementations on embedded systems.

## Keywords
ARX-based cryptography, Chacha20, Side-Channel Attack, STM32, XMEGA, CPA
