import pandas as pd
import mplfinance as mpf

"""Program reads OHLC share price data, creates portfolio, 
trades shares by given algorithm and analyses its efficiency. 
Program finishes after saving portfolio to Excel file and 
plotting share price and portfolio profit charts"""

# /-----------------------------------------------------------------------------/
# Read an open-high-low-close share price data
data = pd.read_csv("finance.csv", index_col=0, parse_dates=True)

# Declare portfolio DataFrame
pf = data.loc[:, ["close"]]
pf["balance"], pf["shares"] = 0, 0

# /-----------------------------------------------------------------------------/
# Trading algorithm
for i, row in enumerate(pf.itertuples()):
    balance = pf.loc[pf.index[i-1], "balance"]
    shares = pf.loc[pf.index[i-1], "shares"]
    current_close = pf.loc[pf.index[i], "close"]
    compare_close = pf.loc[pf.index[i-13], "close"]
    buy, sell = balance - current_close, balance + current_close

    # Buy single share if current close is higher than the close 13 days ago
    if shares == 0 and current_close > compare_close:
        pf.loc[pf.index[i], "balance"] = buy
        pf.loc[pf.index[i], "shares"] = 1
        continue

    # Sell single share if current close is lower than the close 13 days ago
    if shares == 1 and compare_close < current_close or i == len(pf.index) - 1:
        pf.loc[pf.index[i], "balance"] = sell
        pf.loc[pf.index[i], "shares"] = 0
        continue

    # Dont buy or sell if none of the conditions are true
    pf.loc[pf.index[i], "balance"] = balance
    pf.loc[pf.index[i], "shares"] = shares

# /-----------------------------------------------------------------------------/
# Calculate portfolio value and profit for each day
pf["value"] = pf["balance"] + pf["shares"] * pf["close"]
pf["profit"] = pf["value"] - pf["value"].shift()

# Output profits
print(f"Total profit is \t{pf['profit'].sum():.2f}$")
print(f"Mean daily profit: \t{pf['profit'].mean():.2f}$")
print(f"Daily profit variance: \t{pf['profit'].var():.2f}")
# Find weekday with maximum profit
wd_profit = pf.groupby(pf.index.day_name())["profit"].sum()
print(f"Maximum profit is {wd_profit.max():.2f}$ at {wd_profit.idxmax()}")

# /-----------------------------------------------------------------------------/
# Calculate maximum loss in two ways:
# as a price drop from overall maximum to nearest lowest
max_to_low = pf["value"].max() - pf.loc[pf["value"].idxmax():, "value"].min()
# or as a price drop from nearest highest to overall minimum
high_to_min = pf.loc[:pf["value"].idxmin(), "value"].max() - pf["value"].min()

if max_to_low > high_to_min:
    start_date = pf["value"].idxmax()
    end_date = pf.loc[pf["value"].idxmax():, "value"].idxmin()
else:
    start_date = pf.loc[:pf["value"].idxmin(), "value"].idxmax()
    end_date = pf["value"].idxmin()

print(f"Maximum daily loss: \t{pf['value'].min():.2f}$")
print(f"Maximum loss of {-max(max_to_low, high_to_min):.2f}$ lasts for "
      f"{(end_date-start_date).days} days from {start_date} to {end_date}")

# /-----------------------------------------------------------------------------/
# Calculate historical value at risk with 95% confidence
pf["returns"] = pf["close"].pct_change()
var = 100*pf["returns"].sort_values(ascending=True).quantile(0.05)
print(f"Value at risk with 95% confidence is {var:.2f}% of a portfolio value")

# /-----------------------------------------------------------------------------/
# Export created portfolio DataFrame to Excel file
with pd.ExcelWriter("finance.xlsx") as writer:
    pf.to_excel(writer, engine="xlsxwriter")

# /-----------------------------------------------------------------------------/
# Plot share price candlestick chart and equity curve
plt_style = mpf.make_mpf_style(
    base_mpf_style="yahoo", edgecolor='k', y_on_right=False)
equity_curve = mpf.make_addplot(
    pf["value"], panel=2, type="line", ylabel="Portfolio \nvalue, $", mav=253)
mpf.plot(data, type="candle", addplot=equity_curve, style=plt_style, mav=253,
         title="Financial charts", ylabel="Share price, $",
         ylabel_lower="Shares \ntraded", volume=True, figratio=(1, 1))
# /-----------------------------------------------------------------------------/
