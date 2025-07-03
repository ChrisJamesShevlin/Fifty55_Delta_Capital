# 25Ten Delta Capital

A dynamic position-sizing tool built with Tkinter for Python, designed to help traders allocate margin across multiple instruments according to user-defined weights and minimum lot sizes.

![image](https://github.com/user-attachments/assets/5f09bc88-66cb-4cf4-a0f7-cebe1848a00d)


## Features

- **Account Inputs**  
  - Specify your total account balance (£)  
  - Set desired margin utilization (%)

- **Dynamic Instruments Table**  
  - Add or remove instruments on the fly  
  - Enter: name, sector, live price, minimum stake, margin & notional at min, target weight (%)

- **Smart Allocation Algorithm**  
  - Enforces per‐instrument minimum stakes  
  - Iteratively solves to maximize notional exposure under your margin target  
  - Scales up allocations proportionally when margin used is below target  
  - Outputs stake, notional, margin, and actual weight per instrument

- **Console Output**  
  - Neatly formatted table showing final positions and totals  

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/25Ten-Delta-Capital.git
   cd 25Ten-Delta-Capital
