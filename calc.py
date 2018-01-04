"""
  Coincheckにおける損益計算を行うツール.

  Input:
    1. 取引履歴：~/Downloads/orders.csv
      https://coincheck.com/ja/exchange/my_complete_orders?pair=btc_jpy
    2. 購入履歴：~/Downloads/buys.csv
      https://coincheck.com/ja/buys
    3. 売却履歴：~/Downloads/sells.csv
      https://coincheck.com/ja/sells
    4. 送信履歴：~/Downloads/sends.csv
      https://coincheck.com/ja/send
    5. 受信履歴：~/Downloads/deposits.csv
      https://coincheck.com/ja/deposit_bitcoin
    6. その他： 92行目付近（2段階認証の報酬など）

  Output:
    1. 取引履歴一覧とProfit/Loss
    ---
    order         ,currency ,type     ,date        ,amount      ,price      ,profit
    trade         ,BTC      ,buy      ,2017-08-31  ,0.1         ,510000     ,
    buy           ,XEM      ,buy      ,2017-09-01  ,100.0       ,38         ,
    trade         ,BTC      ,buy      ,2017-09-01  ,0.105       ,510804     ,
    trade         ,BTC      ,sell     ,2017-09-01  ,0.095       ,510804     ,191
    ...

    2. 期末残高
    ---
    BTC ,99.999     ,1416415.3
    XEM ,1234.0     ,50.918794
    XRP ,5678.0     ,28.789344
    ...

"""
import os
from pathlib import Path
import csv
from pprint import pprint
from decimal import Decimal, getcontext
import requests

# 有効桁数は少数第8位
getcontext().prec = 8

def load_csv(path):
  with open(path, newline="") as f:
    reader = csv.DictReader(f, delimiter=",")
    return [row for row in reader]

def load_activities():
  return (load_csv(os.path.join(Path.home(), "Downloads", "orders.csv")),
    load_csv(os.path.join(Path.home(), "Downloads", "buys.csv")),
    load_csv(os.path.join(Path.home(), "Downloads", "sells.csv")),
    load_csv(os.path.join(Path.home(), "Downloads", "sends.csv")),
    load_csv(os.path.join(Path.home(), "Downloads", "deposits.csv")))

def get_trades(orders, buys, sells, sends, deposits):
  """日付の降順でトレード内容を返却する."""
  items = []
  for trade in orders:
    items.append({
      "Order"             : "trade",
      "Date"              : trade["Date"],
      "Type"              : trade["Type"],
      "Amount"            : Decimal(trade["BTC"]),
      "Rate"              : Decimal(trade["Rate"]),
      "Price"             : Decimal(trade["JPY"]),
      "Trading Currency"  : "BTC",
      "Original Currency" : "JPY"
    })
  for buy in buys:
    if buy["Progress"] == "completed":
      items.append({
        "Order"            : "buy",
        "Date"             : buy["Time"],
        "Type"             : "buy" if buy["Original Currency"] == "JPY" else "exchange",
        "Amount"           : Decimal(buy["Amount"]),
        "Rate"             : Decimal(buy["Price"]) / Decimal(buy["Amount"]),
        "Price"            : Decimal(buy["Price"]),
        "Trading Currency" : buy["Trading Currency"],
        "Original Currency": buy["Original Currency"]
      })
  for sell in sells:
    if sell["Progress"] == "completed":
      items.append({
        "Order"            : "sell",
        "Date"             : sell["Time"],
        "Type"             : "sell" if buy["Original Currency"] == "JPY" else "exchange",
        "Amount"           : Decimal(sell["Amount"]) * -1,
        "Rate"             : Decimal(sell["Price"]) / Decimal(sell["Amount"]),
        "Price"            : Decimal(sell["Price"]),
        "Trading Currency" : sell["Trading Currency"],
        "Original Currency": sell["Original Currency"]
      })
  for send in sends:
    if send["Status"] == "confirmed":
      items.append({
        "Order"            : "send",
        "Date"             : send["Date"],
        "Type"             : "send",
        "Amount"           : Decimal(send["Amount"]) * -1,
        "Fee"              : Decimal(send["Fee"]),
        "Trading Currency" : send["Currency"],
      })
  for deposit in deposits:
    if deposit["Status"] == "confirmed":
      items.append({
        "Order"            : "deposit",
        "Date"             : deposit["Date"],
        "Type"             : "deposit",
        "Amount"           : Decimal(deposit["Amount"]),
        "Trading Currency" : deposit["Currency"],
      })
  # 2段階認証の報酬をdepositで処理.
  items.append({
    "Order"            : "deposit",
    "Date"             : "2017-09-05",
    "Type"             : "deposit",
    "Amount"           : Decimal(0.0003),
    "Trading Currency" : "BTC",
  })
  return sorted(items, key=lambda d:d["Date"])

def get_price(dt, currency):
  # TODO 取得結果はキャッシュしてもいいかな.
  year, month, _ = dt.split("-")
  url = "https://coincheck.com/exchange/closing_prices/list?month={}&year={}".format(int(month), int(year))
  result = requests.get(url).json()
  price = Decimal(result["closing_prices"][dt][currency.lower()][1])
  # print("price:", dt, currency, price)
  return price

def main():
  """メイン処理"""
  # 取引履歴, 購入履歴、売却履歴、送信履歴、受信履歴
  orders, buys, sells, sends, deposits = load_activities()

  # 取引記録を作成する
  print("{:14},{:4},{:9},{:12},{:12},{:11},{}".format('order', 'currency', 'type', 'date', 'amount', 'price', 'profit'))
  table = {}
  for trade in get_trades(orders, buys, sells, sends, deposits):
    dt = trade["Date"].split(" ")[0]
    # 対象は2017-12-31まで.
    if dt >= "2018-01-01":
      continue
    # 購入
    if trade["Type"] == "buy":
      amount, price = table.get(trade["Trading Currency"], (0, 0))
      # 加重平均の価格
      price = (price * amount + trade["Rate"] * Decimal(trade["Amount"])) / (amount + trade["Amount"])
      # 数量
      amount += trade["Amount"]
      # 保存
      table[trade["Trading Currency"]] = (amount, price)
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"], trade["Trading Currency"], 'buy', dt, amount, int(price), ''))
    # 売却
    elif trade["Type"] == "sell":
      amount, price = table.get(trade["Trading Currency"], (0, 0))
      amount += trade["Amount"]
      profit = (trade["Rate"] - price) * trade["Amount"] * -1
      # 保存
      table[trade["Trading Currency"]] = (amount, price)
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"], trade["Trading Currency"], 'sell', dt, amount, int(price), int(profit)))
    # 交換
    elif trade["Type"] == "exchange":
      # pprint(trade)
      # 交換元は売却として処理.
      buy_price = get_price(dt, trade["Original Currency"])
      buy_amount = trade["Price"] * -1
      amount, price = table.get(trade["Original Currency"], (0, 0))
      amount += buy_amount
      profit = (buy_price - price) * buy_amount * -1
      # 保存
      table[trade["Original Currency"]] = (amount, price)
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"] + "(exchange)", trade["Original Currency"], 'sell', dt, amount, int(price), int(profit)))
      # 交換先は購入として処理.
      amount, price = table.get(trade["Trading Currency"], (0, 0))
      # 加重平均の価格
      buy_rate = buy_price * buy_amount * -1 / trade["Amount"]
      # print("buy_rate:", buy_rate, buy_price, buy_amount)
      price = (price * amount + buy_rate) * trade["Amount"] / (amount + trade["Amount"])
      # 数量
      amount += trade["Amount"]
      # 保存
      table[trade["Trading Currency"]] = (amount, price)
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"] + "(exchange)", trade["Trading Currency"], 'buy', dt, amount, int(price), ''))
    # 送信
    elif trade["Type"] == "send":
      amount, price = table.get(trade["Trading Currency"], (0, 0))
      amount += trade["Amount"]
      amount -= trade["Fee"]
      table[trade["Trading Currency"]] = (amount, price)
      rate = get_price(dt, trade["Trading Currency"])
      profit = trade["Fee"] * rate * -1
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"], trade["Trading Currency"], 'send', dt, amount, int(price), int(profit)))
    # 受け取り
    elif trade["Type"] == "deposit":
      amount, price = table.get(trade["Trading Currency"], (0, 0))
      rate = get_price(dt, trade["Trading Currency"])
      # 加重平均の価格
      price = (price * amount + rate * trade["Amount"]) / (amount + trade["Amount"])
      # 数量
      amount += trade["Amount"]
      profit = rate * trade["Amount"]
      # 保存
      table[trade["Trading Currency"]] = (amount, price)
      # 出力
      print("{:14},{:4},{:9},{:<12},{:<12},{:<11},{}".format(trade["Order"], trade["Trading Currency"], 'deposit', dt, amount, int(price), profit))

  # 期末残高
  print("\n----------------------------")
  print("期末残高")
  for currency, item in table.items():
    print("{:4},{:<12},{:<12}".format(currency, item[0], item[1]))


if __name__ == "__main__":
  main()
