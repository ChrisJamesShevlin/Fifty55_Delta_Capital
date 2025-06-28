import tkinter as tk
from tkinter import messagebox, font

class PortfolioPositionSizer:
    """
    GUI to translate a target asset-allocation into £/pt stakes
    using user-supplied live price, minimum stake, and margin at minimum stake
    for each instrument, ensuring portfolio weightings are as close as possible
    to the provided target weights (matching the reference table).
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('Twenty10 Delta Capital')
        root.geometry('1100x600')
        root.minsize(900, 500)

        # UI defaults
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(size=12)
        root.option_add('*Font', default_font)

        # ───────── INSTRUMENTS: update to match the instruments and sectors in the table ─────────
        # All portfolio logic, weights, display, and overlay logic are updated for these three instruments.
        #
        # Reference Table Instruments:
        # - US 500 cash DFB (Equity)
        # - UK Long-Gilt mini (Bond)
        # - WTI Crude cash DFB (Commodity)

        # Set example weights exactly as per % of total margin in the reference table
        self.instruments = [
            ("US 500 cash DFB", 0.444, "Equity"),
            ("UK Long-Gilt mini", 0.443, "Bond"),
            ("WTI Crude cash DFB", 0.116, "Commodity"),
            # No FX or overlay instruments for this table
        ]
        self.instrument_names = [name for name, _, _ in self.instruments]

        # Default margin usage (as shown in your table is 28%)
        self.default_margin_pct = 28

        # ───────── Build UI ─────────
        main = tk.Frame(root, padx=10, pady=10)
        main.pack(fill='both', expand=True)

        row = 0
        tk.Label(main, text='Account Balance (£):').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.entry_balance = tk.Entry(main)
        self.entry_balance.grid(row=row, column=1, sticky='we', padx=5, pady=5)
        row += 1

        tk.Label(main, text=f'Desired Margin Usage (% of balance, default {self.default_margin_pct}%):') \
            .grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.entry_margin_pct = tk.Entry(main)
        self.entry_margin_pct.insert(0, str(self.default_margin_pct))
        self.entry_margin_pct.grid(row=row, column=1, sticky='we', padx=5, pady=5)
        row += 1

        # Table Headers
        tk.Label(main, text="Instrument").grid(row=row, column=0, sticky='w', padx=5, pady=8)
        tk.Label(main, text="Live Price (pts)").grid(row=row, column=1, sticky='w', padx=5, pady=8)
        tk.Label(main, text="Min Stake (£/pt)").grid(row=row, column=2, sticky='w', padx=5, pady=8)
        tk.Label(main, text="Margin at Min Stake (£)").grid(row=row, column=3, sticky='w', padx=5, pady=8)
        row += 1

        # Per-instrument inputs
        self.price_entries = {}
        self.min_stake_entries = {}
        self.margin_min_entries = {}
        for name, _, _ in self.instruments:
            tk.Label(main, text=name).grid(row=row, column=0, sticky='w', padx=5, pady=3)
            pe = tk.Entry(main)
            pe.grid(row=row, column=1, sticky='we', padx=5, pady=3)
            self.price_entries[name] = pe
            mse = tk.Entry(main)
            mse.grid(row=row, column=2, sticky='we', padx=5, pady=3)
            self.min_stake_entries[name] = mse
            mme = tk.Entry(main)
            mme.grid(row=row, column=3, sticky='we', padx=5, pady=3)
            self.margin_min_entries[name] = mme
            row += 1

        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=1)
        main.grid_columnconfigure(3, weight=1)

        tk.Button(main, text='Calculate Stakes', command=self.calculate).grid(
            row=row, column=0, columnspan=4, pady=10
        )
        row += 1

        result_frame = tk.Frame(main, bd=1, relief='sunken')
        result_frame.grid(row=row, column=0, columnspan=4, sticky='nsew', padx=5, pady=5)
        main.grid_rowconfigure(row, weight=1)

        scrollbar = tk.Scrollbar(result_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.output = tk.Text(
            result_frame,
            wrap='none',
            yscrollcommand=scrollbar.set,
            font=('Courier', 12),
            bg='#f9f9f9',
        )
        self.output.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.output.yview)

    def calculate(self):
        """Validate inputs, compute stakes, and print the margin table."""

        self.output.config(state='normal')
        self.output.delete('1.0', tk.END)

        # 1️⃣ Account balance
        try:
            balance = float(self.entry_balance.get())
            if balance <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Input Error', 'Enter a valid positive Account Balance.')
            return

        # 2️⃣ Desired % of equity to commit as margin
        try:
            margin_pct = float(self.entry_margin_pct.get()) / 100
            if not (0 < margin_pct < 1):
                raise ValueError
            target_total_margin = balance * margin_pct
        except Exception:
            messagebox.showerror('Input Error', 'Enter a valid Desired Margin Usage % (e.g. 28).')
            return

        # 3️⃣ Read per-instrument user inputs
        prices, min_stakes, margin_at_mins = {}, {}, {}
        for name in self.instrument_names:
            try:
                prices[name] = float(self.price_entries[name].get())
                if prices[name] <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror('Input Error', f'Enter a valid price for {name}.')
                return
            try:
                min_stakes[name] = float(self.min_stake_entries[name].get())
                if min_stakes[name] <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror('Input Error', f'Enter a valid minimum stake for {name}.')
                return
            try:
                margin_at_mins[name] = float(self.margin_min_entries[name].get())
                if margin_at_mins[name] < 0:
                    raise ValueError
            except Exception:
                messagebox.showerror('Input Error', f'Enter a valid margin at minimum stake for {name}.')
                return

        # 4️⃣ Portfolio weights: as per reference table (no overlays/FX, only main 3)
        weights = {name: w for name, w, _ in self.instruments}

        # 5️⃣ Compute stakes and margins per instrument
        stakes, margins, notionals = {}, {}, {}
        sum_weight = sum([w for _, w, _ in self.instruments])
        effective_total_margin = target_total_margin

        for name, weight, _ in self.instruments:
            # Allocate target margin per instrument, respecting portfolio weights
            target_margin = effective_total_margin * (weight / sum_weight)
            min_stake = min_stakes[name]
            min_margin = margin_at_mins[name]
            price = prices[name]

            # Stake: try to hit target margin, but never below min stake
            margin_per_unit = min_margin / min_stake if min_stake > 0 else 0
            if margin_per_unit == 0:
                stake = min_stake
                margin = min_margin
            else:
                stake_ideal = target_margin / margin_per_unit
                stake = max(min_stake, stake_ideal)
                margin = stake * margin_per_unit
            stakes[name] = stake
            margins[name] = margin
            notionals[name] = stake * price

        # 6️⃣ Output
        header = f"{'Instrument':25s} {'Price':>10s} {'Stake (£/pt)':>15s} {'Notional £':>13s} {'Margin £':>12s} {'Weight %':>10s}\n"
        self.output.insert(tk.END, header)
        self.output.insert(tk.END, '-' * 93 + '\n')

        # Sector breakdowns for pretty display
        sector_map = {name: sector for name, _, sector in self.instruments}
        display_order = [name for name, _, _ in self.instruments]

        sector_subtotals = {}
        sector_margin = {}
        sector_notional = {}
        sector_instrs = {}
        total_margin = sum(margins[n] for n in self.instrument_names)
        total_notional = sum(notionals[n] for n in self.instrument_names)

        for name in display_order:
            sector = sector_map[name]
            sector_subtotals.setdefault(sector, 0)
            sector_margin.setdefault(sector, 0)
            sector_notional.setdefault(sector, 0)
            sector_instrs.setdefault(sector, []).append(name)
            sector_subtotals[sector] += stakes[name] * prices[name]
            sector_margin[sector] += margins[name]
            sector_notional[sector] += notionals[name]

        for sector in ['Equity', 'Bond', 'Commodity']:
            if sector not in sector_instrs:
                continue
            self.output.insert(tk.END, f"\n{'-'*10} {sector} {'-'*10}\n")
            for name in sector_instrs[sector]:
                p = prices[name]
                stake = stakes[name]
                margin_used = margins[name]
                notional = notionals[name]
                weight_pct = (margin_used / total_margin) * 100 if total_margin else 0
                self.output.insert(
                    tk.END,
                    f"{name:25s} {p:10.2f} {stake:15.4f} {notional:13.2f} {margin_used:12.2f} {weight_pct:10.2f}\n",
                )
            # Subtotals for sector
            s_notional = sector_notional[sector]
            s_margin = sector_margin[sector]
            s_wt = (s_margin / total_margin) * 100 if total_margin else 0
            self.output.insert(
                tk.END,
                f"{' ' * 2}{sector} subtotal{' ' * (16-len(sector))} {' ':>10} {' ':>15} {s_notional:13.2f} {s_margin:12.2f} {s_wt:10.2f}\n"
            )

        self.output.insert(tk.END, '-' * 93 + '\n')
        self.output.insert(
            tk.END,
            f"{'TOTALS':<48s}{total_notional:13.2f} {total_margin:12.2f} (target {target_total_margin:.2f})\n",
        )
        self.output.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    app = PortfolioPositionSizer(root)
    root.mainloop()
