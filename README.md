# SolanaETL

## 🚀Getting Started

### 🔧Install

Let's start with the following command:
Install the dependencies:

```shell
pip install -r requirements.txt
```

### 🔍Detect a account 

The project will collect transaction data and account information from the designated account

If you want to collect data on this account "8KNu2J8gk4ZCGdpA2vPbcuKmRyc7R6qSCRPaycbCaia7"

Run on this command as follow:

```shell
scrapy crawl  solana.etl -a account_key=8KNu2J8gk4ZCGdpA2vPbcuKmRyc7R6qSCRPaycbCaia7 -a providers=https://few-morning-waterfall.solana-mainnet.quiknode.pro/12d6f7012c975de42801cbfbb5494b9eafa8e281,https://magical-greatest-haze.solana-mainnet.quiknode.pro/e9bc0e26c5cd1d10024e93933ec7b8d24467773c
```

If everything runs smoothly, you will get some tables.
You can find these tables on ./data on finished.

```
AccountInfo.csv: The information of the account
signature.csv: Signatures for account-related transactions
Log.csv: Program execution log for transactions
BalanceChanges.csv: Changes in the assets of transactions
Transactions.csv: Transaction information for transactions
TokenAccount.csv: Token account information for accounts
```



### 💡 Others

This project involves data scraping, all data scraping is based on our previous work: BlockChainSpider. If you are interested, you can visit  https://github.com/wuzhy1ng/BlockchainSpider to get more information. 