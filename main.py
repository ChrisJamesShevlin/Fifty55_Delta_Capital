import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizer:
    def __init__(self, root):
        self.root = root
        root.title("Twenty10 Delta Capital")
        root.geometry("800x650")
        root.minsize(600, 400)

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        root.option_add("*Font", default_font)

        # Target allocation weights (must sum to 1.00)
        self.target_weights = {
            "US500 futures":           0.28,
            "Gold futures":            0.13,
            "EUR/USD futures":         0.09,
            "USD/JPY futures":         0.08,
            "Brent Crude futures":     0.05,
            "Japan 225 futures":       0.17,
            "US Ultra Treasury Bond":  0.20,
        }

        # Margin rates as a fraction of notional
        self.margin_rates = {
            "US500 futures":           0.05,
            "Gold futures":            0.03,
            "EUR/USD futures":         0.0333,
            "USD/JPY futures":         0.05,
            "Brent Crude futures":     0.05,
            "Japan 225 futures":       0.05,
            "US Ultra Treasury Bond":  0.0333,
        }

        self.default_margin_pct = 20

        main = tk.Frame(root, padx=10, pady=10)
        main.pack(fill="both", expand=True)

        row = 0
        tk.Label(main, text="Account Balance (£):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_balance = tk.Entry(main)
        self.entry_balance.grid(row=row, column=1, sticky="we", padx=5, pady=5)
        row += 1

        tk.Label(main, text=f"Desired Margin Usage (% of balance, default {self.default_margin_pct}%):")\
            .grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_margin_pct = tk.Entry(main)
        self.entry_margin_pct.insert(0, str(self.default_margin_pct))
        self.entry_margin_pct.grid(row=row, column=1, sticky="we", padx=5, pady=5)
        row += 1

        tk.Label(main, text="Current Prices (points) per instrument:").grid(row=row, column=0, columnspan=2, pady=(10, 5))
        row += 1

        self.price_entries = {}
        for instr in self.target_weights:
            tk.Label(main, text=f"{instr} Price:").grid(row=row, column=0, sticky="e", padx=5, pady=3)
            entry = tk.Entry(main)
            entry.grid(row=row, column=1, sticky="we", padx=5, pady=3)
            self.price_entries[instr] = entry
            row += 1

        main.grid_columnconfigure(1, weight=1)

        tk.Button(main, text="Calculate Stakes", command=self.calculate).grid(
            row=row, column=0, columnspan=2, pady=10
        )
        row += 1

        result_frame = tk.Frame(main, bd=1, relief="sunken")
        result_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        main.grid_rowconfigure(row, weight=1)

        scrollbar = tk.Scrollbar(result_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.output = tk.Text(result_frame, wrap="none", yscrollcommand=scrollbar.set, font=("Courier", 12), bg="#f9f9f9")
        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.output.yview)

    def calculate(self):
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)

        # Validate account balance
        try:
            balance = float(self.entry_balance.get())
            if balance <= 0:
                raise ValueError
        except:
            messagebox.showerror("Input Error", "Enter a valid positive Account Balance.")
            return

        # Validate margin percentage
        try:
            margin_pct = float(self.entry_margin_pct.get()) / 100
            if not (0 < margin_pct < 1):
                raise ValueError
            target_total_margin = balance * margin_pct
        except:
            messagebox.showerror("Input Error", "Enter a valid Desired Margin Usage % (e.g. 20).")
            return

        # Read current prices
        prices = {}
        for instr in self.target_weights:
            try:
                price = float(self.price_entries[instr].get())
                if price <= 0:
                    raise ValueError
                prices[instr] = price
            except:
                messagebox.showerror("Input Error", f"Enter a valid price for '{instr}'.")
                return

        # Calculate stakes & margins per instrument
        stakes = {}
        margins = {}
        for instr, weight in self.target_weights.items():
            price = prices[instr]
            rate  = self.margin_rates[instr]
            target_margin = target_total_margin * weight
            stake = target_margin / (price * rate)
            stakes[instr] = stake
            margins[instr] = stake * price * rate

        total_margin = sum(margins.values())

        # Build output table
        header = f"{'Instrument':25s} {'Price':>10s} {'Stake (£/pt)':>15s} {'Margin £':>12s} {'Weight %':>10s}\n"
        self.output.insert(tk.END, header)
        self.output.insert(tk.END, "-" * 90 + "\n")
        for instr in self.target_weights:
            p = prices[instr]
            stake = stakes[instr]
            margin_used = margins[instr]
            weight_pct = (margin_used / total_margin) * 100
            self.output.insert(
                tk.END,
                f"{instr:25s} {p:10.2f} {stake:15.4f} {margin_used:12.2f} {weight_pct:10.2f}\n"
            )

        self.output.insert(tk.END, "-" * 90 + "\n")
        self.output.insert(
            tk.END,
            f"{'Total Margin Used':<50s}{total_margin:12.2f} (target {target_total_margin:.2f})\n"
        )
        self.output.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioPositionSizer(root)
    root.mainloop()
