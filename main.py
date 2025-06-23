import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizerIGMargins:
    def __init__(self, root):
        self.root = root
        root.title("Portfolio Position Sizer (IG Margin Rates)")

        # Window & font
        root.geometry("800x650")
        root.minsize(600, 400)
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        root.option_add("*Font", default_font)

        # Allocations (sum <=1; leftover is cash buffer)
        self.allocations = {
            "US500 futures": 0.35,
            "Gold futures": 0.25,
            "EUR/USD futures": 0.20,
            "FTSE 100 futures": 0.10,
            "Brent Crude futures": 0.05,
            "VIX futures": 0.01,  # tiny allocation by default; adjust or remove if too large
        }
        # Baseline stake for very small balances (Brent) if needed
        self.fixed_min_stake = 0.04
        # Default desired margin usage as fraction of balance
        self.default_desired_margin_pct = 0.25  # 25%

        # Hard-coded IG margin rates (Tier 1 small positions). VERIFY in your IG account:
        # US500 futures: 5% :contentReference[oaicite:5]{index=5}
        # FTSE 100 futures: 5% :contentReference[oaicite:6]{index=6}
        # Gold futures: 3% :contentReference[oaicite:7]{index=7}
        # EUR/USD futures: 3.33% :contentReference[oaicite:8]{index=8}
        # Brent Crude futures: 5% :contentReference[oaicite:9]{index=9}
        # VIX futures: 20% (example; please check your IG platform for actual VIX margin) 
        self.margin_rates = {
            "US500 futures": 0.05,
            "Gold futures": 0.03,
            "EUR/USD futures": 0.0333,
            "FTSE 100 futures": 0.05,
            "Brent Crude futures": 0.05,
            "VIX futures": 0.20,
        }

        # Build UI
        main = tk.Frame(root, padx=10, pady=10)
        main.pack(fill="both", expand=True)

        row = 0
        tk.Label(main, text="Account Balance (£):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_balance = tk.Entry(main)
        self.entry_balance.grid(row=row, column=1, sticky="we", padx=5, pady=5)
        row += 1

        tk.Label(main, text=f"Desired Margin Usage (% of balance, default {int(self.default_desired_margin_pct*100)}%):")\
            .grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_desired_margin = tk.Entry(main)
        self.entry_desired_margin.insert(0, str(int(self.default_desired_margin_pct*100)))
        self.entry_desired_margin.grid(row=row, column=1, sticky="we", padx=5, pady=5)
        row += 1

        tk.Label(main, text="Current Prices (points) per instrument:").grid(
            row=row, column=0, columnspan=2, pady=(10,5)
        )
        row += 1

        self.entries_price = {}
        for instr in self.allocations:
            tk.Label(main, text=f"{instr} Price:").grid(row=row, column=0, sticky="e", padx=5, pady=3)
            e_price = tk.Entry(main)
            e_price.grid(row=row, column=1, sticky="we", padx=5, pady=3)
            self.entries_price[instr] = e_price
            row += 1

        main.grid_columnconfigure(1, weight=1)

        tk.Button(main, text="Calculate Stakes", command=self.calculate).grid(
            row=row, column=0, columnspan=2, pady=10
        )
        row += 1

        # Results area
        rf = tk.Frame(main, bd=1, relief="sunken")
        rf.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        main.grid_rowconfigure(row, weight=1)
        sb = tk.Scrollbar(rf, orient="vertical")
        sb.pack(side="right", fill="y")
        self.txt = tk.Text(rf, wrap="none", yscrollcommand=sb.set, font=("Courier",12), bg="#f9f9f9")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)

    def calculate(self):
        self.txt.config(state="normal")
        self.txt.delete("1.0", tk.END)

        # 1) Read balance
        try:
            bal = float(self.entry_balance.get())
            if bal <= 0:
                raise ValueError
        except:
            messagebox.showerror("Input Error", "Enter a valid positive Account Balance.")
            return

        # 2) Read desired margin %
        try:
            desired_pct = float(self.entry_desired_margin.get()) / 100.0
            if not (0 < desired_pct < 1):
                raise ValueError
            desired_margin = bal * desired_pct
        except:
            messagebox.showerror("Input Error", "Enter a valid Desired Margin Usage % (e.g. 25).")
            return

        # 3) Read prices
        prices = {}
        for instr in self.allocations:
            ent = self.entries_price[instr]
            try:
                p = float(ent.get())
                if p <= 0:
                    raise ValueError
                prices[instr] = p
            except:
                messagebox.showerror("Input Error", f"Enter valid price for '{instr}'.")
                self.txt.config(state="disabled")
                return

        # 4) Compute ideal stakes = (balance * alloc%) / price
        ideal = {instr: (bal * alloc) / prices[instr] for instr, alloc in self.allocations.items()}

        # 5) Enforce Brent baseline if needed
        brent = "Brent Crude futures"
        if ideal.get(brent, 0) <= 0:
            messagebox.showerror("Calculation Error", "Invalid ideal stake for Brent.")
            return
        if ideal[brent] < self.fixed_min_stake:
            scale_base = self.fixed_min_stake / ideal[brent]
        else:
            scale_base = 1.0

        # 6) Compute margin usage at base stakes
        base_stakes = {instr: ideal[instr] * scale_base for instr in self.allocations}
        current_margin_usage = 0.0
        for instr, stake in base_stakes.items():
            rate = self.margin_rates.get(instr)
            if rate is None:
                messagebox.showerror("Configuration Error", f"No margin rate for '{instr}'")
                return
            # Margin = stake_per_point × price × margin_rate
            current_margin_usage += stake * prices[instr] * rate

        if current_margin_usage <= 0:
            messagebox.showerror("Calculation Error", "Computed zero or negative margin usage; check inputs.")
            return

        # 7) Scale factor to reach desired margin
        scale_margin = desired_margin / current_margin_usage

        # 8) Final stakes
        final_stakes = {instr: base_stakes[instr] * scale_margin for instr in self.allocations}

        # 9) Display results
        header = f"{'Instrument':25s} {'Alloc%':>7s} {'Price':>10s} {'Stake':>12s} {'Margin £':>12s}\n"
        self.txt.insert(tk.END, header)
        self.txt.insert(tk.END, "-"*80 + "\n")
        total_margin = 0.0
        for instr, alloc in self.allocations.items():
            p = prices[instr]
            stake = final_stakes[instr]
            rate = self.margin_rates[instr]
            margin_used = stake * p * rate
            total_margin += margin_used
            self.txt.insert(
                tk.END,
                f"{instr:25s} {alloc*100:7.1f}% {p:10.2f} {stake:12.4f} {margin_used:12.2f}\n"
            )



        # Summary line
        self.txt.insert(tk.END, "-"*80 + "\n")
        self.txt.insert(
            tk.END,
            f"{'Total Margin Used':<44s}{total_margin:12.2f} (target {desired_margin:.2f})\n"
        )

        self.txt.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioPositionSizerIGMargins(root)
    root.mainloop()
