import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizerDynamic:
    def __init__(self, root):
        self.root = root
        root.title('25Ten Delta Capital')
        root.geometry('1300x670')
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(size=12)
        root.option_add('*Font', default_font)

        self.rows = []
        self.headers = [
            "Instrument", "Sector", "Live Price", "Min Stake", 
            "Margin @ Min", "Notional @ Min", "Weight (%)"
        ]
        self.dynamic_frame = tk.Frame(root)
        self.dynamic_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Account controls (no Total Portfolio Notional box)
        control_frame = tk.Frame(self.dynamic_frame)
        control_frame.pack(anchor='w')
        tk.Label(control_frame, text="Account Balance (£):").pack(side='left')
        self.entry_balance = tk.Entry(control_frame, width=10)
        self.entry_balance.pack(side='left', padx=(0,10))
        tk.Label(control_frame, text="Desired Margin Usage (%):").pack(side='left')
        self.entry_margin_pct = tk.Entry(control_frame, width=5)
        self.entry_margin_pct.insert(0, "28")
        self.entry_margin_pct.pack(side='left', padx=(0,10))
        tk.Button(control_frame, text="Add Instrument", command=self.add_row).pack(side='left')
        tk.Button(control_frame, text="Calculate Stakes", command=self.calculate).pack(side='left')

        # Instrument Table
        self.table_frame = tk.Frame(self.dynamic_frame)
        self.table_frame.pack(fill='x', pady=10)
        for col, header in enumerate(self.headers):
            tk.Label(self.table_frame, text=header, borderwidth=1, relief='solid', width=16).grid(row=0, column=col)
        tk.Label(self.table_frame, text='', width=6).grid(row=0, column=len(self.headers)) # for delete button

        # Add starter rows (Instrument and Sector ONLY, all else blank)
        self.add_row(["US 500", "Equity", "", "", "", "", ""])
        self.add_row(["Japan 225", "Equity", "", "", "", "", ""])
        self.add_row(["US Treasury Bond", "Bond", "", "", "", "", ""])
        self.add_row(["Gold", "Commodity", "", "", "", "", ""])
        self.add_row(["WTI Crude", "Commodity", "", "", "", "", ""])

        # Output area
        self.output = tk.Text(self.dynamic_frame, height=16, font=('Courier', 12), bg='#f9f9f9', state='disabled')
        self.output.pack(fill='both', expand=True, pady=(10,0))

    def add_row(self, values=None):
        row_idx = len(self.rows) + 1
        entries = []
        for col in range(len(self.headers)):
            ent = tk.Entry(self.table_frame, width=16)
            if values and col < len(values):
                ent.insert(0, str(values[col]))
            ent.grid(row=row_idx, column=col, padx=1, pady=2)
            entries.append(ent)
        btn = tk.Button(self.table_frame, text="Delete", command=lambda idx=row_idx: self.delete_row(idx))
        btn.grid(row=row_idx, column=len(self.headers), padx=1)
        self.rows.append((entries, btn))

    def delete_row(self, idx):
        # Remove row from UI and from self.rows
        if idx-1 < len(self.rows):
            entries, btn = self.rows[idx-1]
            for ent in entries:
                ent.grid_forget()
            btn.grid_forget()
            self.rows.pop(idx-1)
            # Re-pack below rows upwards
            for i in range(idx-1, len(self.rows)):
                for col, ent in enumerate(self.rows[i][0]):
                    ent.grid(row=i+1, column=col)
                self.rows[i][1].grid(row=i+1, column=len(self.headers))

    def calculate(self):
        self.output.config(state='normal')
        self.output.delete('1.0', tk.END)
        # Get account info
        try:
            balance = float(self.entry_balance.get())
            if balance <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Input Error', 'Enter a valid positive Account Balance.')
            return

        try:
            margin_pct = float(self.entry_margin_pct.get()) / 100
            if not (0 < margin_pct < 1):
                raise ValueError
            target_total_margin = balance * margin_pct
        except Exception:
            messagebox.showerror('Input Error', 'Enter a valid Desired Margin Usage % (e.g. 28).')
            return

        # Read instrument rows
        instruments = []
        weights = []
        for entries, _ in self.rows:
            try:
                name = entries[0].get().strip()
                sector = entries[1].get().strip()
                price = float(entries[2].get())
                min_stake = float(entries[3].get())
                margin_min = float(entries[4].get())
                notional_min = float(entries[5].get())
                weight = float(entries[6].get()) / 100
                if not name or not sector or price <= 0 or min_stake <= 0 or margin_min < 0 or notional_min < 0 or weight < 0:
                    continue
                notional_per_unit = notional_min / min_stake
                margin_per_unit = margin_min / min_stake
                instruments.append(dict(
                    name=name, sector=sector, price=price, min_stake=min_stake,
                    margin_min=margin_min, notional_min=notional_min, weight=weight,
                    notional_per_unit=notional_per_unit, margin_per_unit=margin_per_unit
                ))
                weights.append(weight)
            except Exception:
                continue
        if not instruments or sum(weights) == 0:
            messagebox.showerror('Input Error', 'Please enter at least one valid instrument with positive weights.')
            return

        # --- Begin notional-weighted allocation with scaling and minimums ---
        n = len(instruments)
        min_stakes = [inst['min_stake'] for inst in instruments]
        notional_per_unit = [inst['notional_per_unit'] for inst in instruments]
        margin_per_unit = [inst['margin_per_unit'] for inst in instruments]
        weights = [inst['weight'] for inst in instruments]
        names = [inst['name'] for inst in instruments]

        # Iteratively solve for the max total_notional such that all assets that can be above minimum get as close as possible to their target notional share, and total margin is at or just below target_total_margin

        # 1. Allocate notional by weight, enforce minimums, loop
        # 2. After first pass, if margin used < target, scale up all assets (not below min) so margin is as close as possible to target

        # Helper: Given total_notional, allocate by weights with minimums enforced
        def allocate_notional(total_notional, weights, min_stakes, notional_per_unit):
            n = len(weights)
            stakes = [0.0] * n
            remaining = set(range(n))
            weights_left = weights[:]
            total_weight_left = sum(weights_left)
            notional_left = total_notional
            # First, pre-allocate minimums if needed
            while True:
                changed = False
                # Compute targets for remaining
                for i in list(remaining):
                    target = weights[i] / total_weight_left * notional_left if total_weight_left > 0 else 0
                    stake = target / notional_per_unit[i] if notional_per_unit[i] > 0 else 0
                    if stake < min_stakes[i]:
                        stakes[i] = min_stakes[i]
                        notional_fixed = min_stakes[i] * notional_per_unit[i]
                        notional_left -= notional_fixed
                        total_weight_left -= weights[i]
                        remaining.remove(i)
                        changed = True
                if not changed:
                    break
            # Allocate to the rest
            for i in remaining:
                target = weights[i] / total_weight_left * notional_left if total_weight_left > 0 else 0
                stakes[i] = target / notional_per_unit[i] if notional_per_unit[i] > 0 else 0
            return stakes

        # 1. Initial guess: allocate all at minimum, sum margin, if less than target, scale up
        stakes = min_stakes[:]
        margins = [stakes[i]*margin_per_unit[i] for i in range(n)]
        total_margin = sum(margins)
        total_notional = sum(stakes[i]*notional_per_unit[i] for i in range(n))

        # 2. Max possible notional (without exceeding margin target)
        # Use bisection to find total_notional so that after allocation, margin used is just at or under target
        # Lower bound: sum of minimums. Upper bound: big value.
        low = sum(min_stakes[i]*notional_per_unit[i] for i in range(n))
        high = low * 1000  # Arbitrary large
        best_stakes = min_stakes[:]
        for _ in range(40):
            mid = (low + high) / 2
            test_stakes = allocate_notional(mid, weights, min_stakes, notional_per_unit)
            test_margins = [test_stakes[i]*margin_per_unit[i] for i in range(n)]
            test_margin_sum = sum(test_margins)
            if test_margin_sum > target_total_margin + 1e-8:
                high = mid
            else:
                best_stakes = test_stakes[:]
                low = mid
        # Now, try to scale up all (not below min) so margin used is as close as possible to target
        margins = [best_stakes[i]*margin_per_unit[i] for i in range(n)]
        total_margin = sum(margins)
        if total_margin < target_total_margin - 1e-6:
            scale = target_total_margin / total_margin if total_margin > 0 else 1.0
            for i in range(n):
                best_stakes[i] = max(min_stakes[i], best_stakes[i]*scale)
        stakes = best_stakes
        margins = [stakes[i]*margin_per_unit[i] for i in range(n)]
        notionals = [stakes[i]*notional_per_unit[i] for i in range(n)]
        total_margin = sum(margins)
        total_notional = sum(notionals)

        # --- Output ---
        self.output.insert(tk.END, f"{'Instrument':25s} {'Sector':10s} {'Price':>10s} {'Stake (£/pt)':>15s} {'Notional £':>13s} {'Margin £':>12s} {'Weight %':>10s}\n")
        self.output.insert(tk.END, '-' * 100 + '\n')
        for i, inst in enumerate(instruments):
            w_pct = (notionals[i]/total_notional)*100 if total_notional else 0
            self.output.insert(
                tk.END, 
                f"{inst['name']:25s} {inst['sector']:10s} {inst['price']:10.2f} {stakes[i]:15.4f} {notionals[i]:13.2f} {margins[i]:12.2f} {w_pct:10.2f}\n"
            )
        self.output.insert(tk.END, '-' * 100 + '\n')

        actual_margin_pct = (total_margin / balance) * 100 if balance else 0
        self.output.insert(
            tk.END,
            f"{'TOTALS':<60s}{total_notional:13.2f} {total_margin:12.2f} "
            f"(target {target_total_margin:.2f}, actual margin used: {actual_margin_pct:.2f}%)\n"
        )
        self.output.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = PortfolioPositionSizerDynamic(root)
    root.mainloop()
