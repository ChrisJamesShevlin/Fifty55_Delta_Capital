import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizerIGMargins:
    def __init__(self, root):
        self.root = root
        root.title("Twenty10 Delta Capital")

        root.geometry("800x650")
        root.minsize(600, 400)
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        root.option_add("*Font", default_font)

        # Adjusted base stakes to reflect latest weighting goals
        self.base_stakes = {
            "US500 futures": 0.25,
            "Gold futures": 0.75,        # Significantly increased for ~20%+ weight
            "EUR/USD futures": 0.14,
            "Brent Crude futures": 0.14,
            "Japan 225 futures": 0.04,
            "USD/JPY futures": 0.10
        }

        self.default_desired_margin_pct = 0.20  # 20%

        self.margin_rates = {
            "US500 futures": 0.05,
            "Gold futures": 0.03,
            "EUR/USD futures": 0.0333,
            "Brent Crude futures": 0.05,
            "Japan 225 futures": 0.05,
            "USD/JPY futures": 0.05
        }

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
            row=row, column=0, columnspan=2, pady=(10, 5)
        )
        row += 1

        self.entries_price = {}
        for instr in self.base_stakes:
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

        rf = tk.Frame(main, bd=1, relief="sunken")
        rf.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        main.grid_rowconfigure(row, weight=1)
        sb = tk.Scrollbar(rf, orient="vertical")
        sb.pack(side="right", fill="y")
        self.txt = tk.Text(rf, wrap="none", yscrollcommand=sb.set, font=("Courier", 12), bg="#f9f9f9")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)

    def calculate(self):
        self.txt.config(state="normal")
        self.txt.delete("1.0", tk.END)

        try:
            bal = float(self.entry_balance.get())
            if bal <= 0:
                raise ValueError
        except:
            messagebox.showerror("Input Error", "Enter a valid positive Account Balance.")
            return

        try:
            desired_pct = float(self.entry_desired_margin.get()) / 100.0
            if not (0 < desired_pct < 1):
                raise ValueError
            desired_margin = bal * desired_pct
        except:
            messagebox.showerror("Input Error", "Enter a valid Desired Margin Usage % (e.g. 20).")
            return

        prices = {}
        for instr in self.base_stakes:
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

        current_margin_usage = 0.0
        for instr, stake in self.base_stakes.items():
            price = prices[instr]
            rate = self.margin_rates[instr]
            current_margin_usage += stake * price * rate

        if current_margin_usage <= 0:
            messagebox.showerror("Calculation Error", "Computed zero or negative margin usage; check inputs.")
            return

        scale_factor = desired_margin / current_margin_usage
        final_stakes = {instr: self.base_stakes[instr] * scale_factor for instr in self.base_stakes}

        header = f"{'Instrument':25s} {'Price':>10s} {'Stake (£/pt)':>15s} {'Margin £':>12s} {'Weight %':>10s}\n"
        self.txt.insert(tk.END, header)
        self.txt.insert(tk.END, "-" * 90 + "\n")

        total_margin = 0.0
        margins = {}
        for instr in self.base_stakes:
            p = prices[instr]
            stake = final_stakes[instr]
            rate = self.margin_rates[instr]
            margin_used = stake * p * rate
            margins[instr] = margin_used
            total_margin += margin_used

        for instr in self.base_stakes:
            p = prices[instr]
            stake = final_stakes[instr]
            margin_used = margins[instr]
            weight_pct = (margin_used / total_margin) * 100
            self.txt.insert(
                tk.END,
                f"{instr:25s} {p:10.2f} {stake:15.4f} {margin_used:12.2f} {weight_pct:10.2f}\n"
            )

        self.txt.insert(tk.END, "-" * 90 + "\n")
        self.txt.insert(
            tk.END,
            f"{'Total Margin Used':<50s}{total_margin:12.2f} (target {desired_margin:.2f})\n"
        )

        self.txt.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioPositionSizerIGMargins(root)
    root.mainloop()
