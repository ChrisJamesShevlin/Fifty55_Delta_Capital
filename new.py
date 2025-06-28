import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizerDynamic:
    def __init__(self, root):
        self.root = root
        root.title('Portfolio Position Sizer')
        root.geometry('1200x650')
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(size=12)
        root.option_add('*Font', default_font)

        self.rows = []
        self.headers = ["Instrument", "Sector", "Live Price", "Min Stake", "Margin @ Min", "Weight (%)"]
        self.dynamic_frame = tk.Frame(root)
        self.dynamic_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Account controls
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

        # Add starter rows (blank inputs except instrument name and sector)
        self.add_row(["US 500 cash DFB", "Equity", "", "", "", ""])
        self.add_row(["UK Long-Gilt mini", "Bond", "", "", "", ""])
        self.add_row(["WTI Crude cash DFB", "Commodity", "", "", "", ""])

        # Output area
        self.output = tk.Text(self.dynamic_frame, height=14, font=('Courier', 12), bg='#f9f9f9', state='disabled')
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
        sum_weights = 0
        for entries, _ in self.rows:
            try:
                name = entries[0].get().strip()
                sector = entries[1].get().strip()
                price = float(entries[2].get())
                min_stake = float(entries[3].get())
                margin_min = float(entries[4].get())
                weight = float(entries[5].get()) / 100
                if not name or not sector or price <= 0 or min_stake <= 0 or margin_min < 0 or weight < 0:
                    continue
                instruments.append(dict(name=name, sector=sector, price=price, min_stake=min_stake, margin_min=margin_min, weight=weight))
                sum_weights += weight
            except Exception:
                continue
        if not instruments or sum_weights == 0:
            messagebox.showerror('Input Error', 'Please enter at least one valid instrument with positive weights.')
            return

        # Calculate stakes and margins
        stakes, margins, notionals = {}, {}, {}
        for inst in instruments:
            target_margin = target_total_margin * (inst['weight'] / sum_weights)
            margin_per_unit = inst['margin_min'] / inst['min_stake'] if inst['min_stake'] > 0 else 0
            if margin_per_unit == 0:
                stake = inst['min_stake']
                margin = inst['margin_min']
            else:
                stake_ideal = target_margin / margin_per_unit
                stake = max(inst['min_stake'], stake_ideal)
                margin = stake * margin_per_unit
            stakes[inst['name']] = stake
            margins[inst['name']] = margin
            notionals[inst['name']] = stake * inst['price']

        total_margin = sum(margins[n] for n in stakes)
        total_notional = sum(notionals[n] for n in stakes)

        # Output
        header = f"{'Instrument':25s} {'Sector':10s} {'Price':>10s} {'Stake (£/pt)':>15s} {'Notional £':>13s} {'Margin £':>12s} {'Weight %':>10s}\n"
        self.output.insert(tk.END, header)
        self.output.insert(tk.END, '-' * 100 + '\n')
        for inst in instruments:
            n = inst['name']
            s = inst['sector']
            p = inst['price']
            stake = stakes[n]
            margin = margins[n]
            notional = notionals[n]
            w_pct = (margin/total_margin)*100 if total_margin else 0
            self.output.insert(tk.END, f"{n:25s} {s:10s} {p:10.2f} {stake:15.4f} {notional:13.2f} {margin:12.2f} {w_pct:10.2f}\n")
        self.output.insert(tk.END, '-' * 100 + '\n')

        # --- ACTUAL MARGIN % ---
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
